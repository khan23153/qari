"""
Wav2Vec2-CTC fine-tuning for Quranic Arabic — explicit PyTorch training loop.

Complements ml/training/finetune_whisper.py: Whisper powers transcription,
while a fine-tuned Wav2Vec2-CTC model powers the FORCED ALIGNER
(ml/alignment/forced_alignment.py) — per-letter timing that the tajweed
checks (ghunnah/madd durations) depend on. Better CTC accuracy ⇒ tighter
word/letter timestamps ⇒ more trustworthy tajweed verdicts.

Consumes the same dataset layout as the Whisper script
(scripts/build_training_dataset.py output):
    <data_dir>/manifest.jsonl   {"audio_path", "text", ...}
    <data_dir>/audio/...        16 kHz mono WAV

Usage (GPU machine):
    pip install torch torchaudio transformers soundfile
    python -m ml.training.finetune_wav2vec2 \\
        --model_id jonatasgrosman/wav2vec2-large-xlsr-53-arabic \\
        --data_dir /data/quran_train \\
        --output_dir /models/qari-wav2vec2-ctc \\
        --epochs 5 --batch_size 8 --learning_rate 3e-5

The character vocabulary is built FROM THE DATASET (normalized Arabic), so
the CTC head is exactly matched to Quranic text. Training freezes the
convolutional feature encoder (standard for low-data fine-tuning) and
reports WER + CER on a held-out split every epoch, keeping the best
checkpoint by WER.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CTC_BLANK_TOKEN = "[PAD]"
CTC_UNK_TOKEN = "[UNK]"
WORD_DELIMITER = "|"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fine-tune Wav2Vec2-CTC on Quran recitation data"
    )
    p.add_argument(
        "--model_id",
        default="jonatasgrosman/wav2vec2-large-xlsr-53-arabic",
        help="Pretrained Wav2Vec2 checkpoint (an Arabic XLSR works best)",
    )
    p.add_argument("--data_dir", required=True, help="Dataset dir with manifest.jsonl")
    p.add_argument("--output_dir", default="./wav2vec2-quran-finetuned")
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--learning_rate", type=float, default=3e-5)
    p.add_argument("--warmup_ratio", type=float, default=0.1)
    p.add_argument("--eval_split", type=float, default=0.1)
    p.add_argument("--max_audio_s", type=float, default=30.0,
                   help="Drop clips longer than this (CTC memory blows up)")
    p.add_argument("--grad_accum", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--num_workers", type=int, default=4)
    return p.parse_args()


# ── Data ─────────────────────────────────────────────────────────────────────

def load_manifest(data_dir: str) -> list[dict]:
    manifest = Path(data_dir) / "manifest.jsonl"
    if not manifest.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest}")
    entries = []
    with open(manifest, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    base = Path(data_dir)
    for e in entries:
        ap = e["audio_path"]
        if not Path(ap).is_absolute():
            e["audio_path"] = str(base / ap)
    logger.info("Loaded %d entries", len(entries))
    return entries


def normalize_text(text: str) -> str:
    """Match the runtime normalization (ml.inference.asr.normalize_arabic) so
    the CTC vocab and the aligner see the same text distribution."""
    from ml.inference.asr import normalize_arabic

    return normalize_arabic(text)


def build_vocab(entries: list[dict]) -> dict[str, int]:
    """Character vocabulary from the (normalized) dataset text."""
    chars: set[str] = set()
    for e in entries:
        chars.update(normalize_text(e["text"]).replace(" ", ""))
    vocab = {c: i for i, c in enumerate(sorted(chars))}
    vocab[WORD_DELIMITER] = len(vocab)
    vocab[CTC_UNK_TOKEN] = len(vocab)
    vocab[CTC_BLANK_TOKEN] = len(vocab)
    logger.info("Vocab: %d symbols", len(vocab))
    return vocab


class QuranCTCDataset:
    """Lazy dataset: loads + featurizes one clip per __getitem__."""

    def __init__(self, entries: list[dict], processor, max_audio_s: float):
        self.entries = entries
        self.processor = processor
        self.max_samples = int(max_audio_s * SAMPLE_RATE)

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, idx: int) -> dict | None:
        import soundfile as sf

        e = self.entries[idx]
        try:
            audio, sr = sf.read(e["audio_path"], dtype="float32")
        except Exception as exc:  # unreadable clip → collator drops it
            logger.warning("skip %s: %s", e["audio_path"], exc)
            return None
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sr != SAMPLE_RATE:
            import torch
            import torchaudio

            audio = torchaudio.functional.resample(
                torch.from_numpy(audio), sr, SAMPLE_RATE
            ).numpy()
        if len(audio) > self.max_samples or len(audio) < SAMPLE_RATE // 4:
            return None
        inputs = self.processor(
            audio, sampling_rate=SAMPLE_RATE, return_tensors="pt"
        )
        with self.processor.as_target_processor():
            labels = self.processor(normalize_text(e["text"])).input_ids
        return {
            "input_values": inputs.input_values.squeeze(0),
            "labels": labels,
        }


def collate(batch: list[dict | None], processor, blank_id: int):
    """Pad audio + labels; label padding is -100 so CTC loss masks it."""
    import torch

    batch = [b for b in batch if b is not None]
    if not batch:
        return None
    audio = [b["input_values"] for b in batch]
    lengths = [a.shape[0] for a in audio]
    max_len = max(lengths)
    input_values = torch.zeros(len(batch), max_len)
    attention_mask = torch.zeros(len(batch), max_len, dtype=torch.long)
    for i, a in enumerate(audio):
        input_values[i, : a.shape[0]] = a
        attention_mask[i, : a.shape[0]] = 1
    label_lens = [len(b["labels"]) for b in batch]
    labels = torch.full((len(batch), max(label_lens)), -100, dtype=torch.long)
    for i, b in enumerate(batch):
        labels[i, : len(b["labels"])] = torch.tensor(b["labels"])
    return {
        "input_values": input_values,
        "attention_mask": attention_mask,
        "labels": labels,
    }


# ── Metrics ──────────────────────────────────────────────────────────────────

def _edit_distance(a: list, b: list) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a):
        cur = [i + 1]
        for j, y in enumerate(b):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (x != y)))
        prev = cur
    return prev[-1]


def wer(preds: list[str], refs: list[str]) -> float:
    errs = words = 0
    for p, r in zip(preds, refs):
        rw = r.split()
        errs += _edit_distance(p.split(), rw)
        words += len(rw)
    return errs / max(words, 1)


def cer(preds: list[str], refs: list[str]) -> float:
    errs = chars = 0
    for p, r in zip(preds, refs):
        errs += _edit_distance(list(p), list(r))
        chars += len(r)
    return errs / max(chars, 1)


# ── Training ─────────────────────────────────────────────────────────────────

def train(args: argparse.Namespace) -> None:
    import torch
    from torch.utils.data import DataLoader
    from transformers import (
        Wav2Vec2CTCTokenizer,
        Wav2Vec2FeatureExtractor,
        Wav2Vec2ForCTC,
        Wav2Vec2Processor,
        get_linear_schedule_with_warmup,
    )

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = load_manifest(args.data_dir)
    random.shuffle(entries)
    n_eval = max(1, int(len(entries) * args.eval_split))
    eval_entries, train_entries = entries[:n_eval], entries[n_eval:]

    # Tokenizer/vocab built from OUR normalized text (not the checkpoint's).
    vocab = build_vocab(entries)
    vocab_path = out_dir / "vocab.json"
    vocab_path.write_text(json.dumps(vocab, ensure_ascii=False))
    tokenizer = Wav2Vec2CTCTokenizer(
        str(vocab_path),
        unk_token=CTC_UNK_TOKEN,
        pad_token=CTC_BLANK_TOKEN,
        word_delimiter_token=WORD_DELIMITER,
    )
    feature_extractor = Wav2Vec2FeatureExtractor(
        feature_size=1, sampling_rate=SAMPLE_RATE,
        padding_value=0.0, do_normalize=True, return_attention_mask=True,
    )
    processor = Wav2Vec2Processor(feature_extractor, tokenizer)

    model = Wav2Vec2ForCTC.from_pretrained(
        args.model_id,
        vocab_size=len(vocab),
        pad_token_id=tokenizer.pad_token_id,
        ctc_loss_reduction="mean",
        ignore_mismatched_sizes=True,  # new CTC head for our vocab
    ).to(device)
    model.freeze_feature_encoder()

    train_ds = QuranCTCDataset(train_entries, processor, args.max_audio_s)
    eval_ds = QuranCTCDataset(eval_entries, processor, args.max_audio_s)
    coll = lambda b: collate(b, processor, tokenizer.pad_token_id)  # noqa: E731
    train_dl = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        collate_fn=coll, num_workers=args.num_workers,
    )
    eval_dl = DataLoader(
        eval_ds, batch_size=args.batch_size, shuffle=False,
        collate_fn=coll, num_workers=args.num_workers,
    )

    steps_per_epoch = max(1, len(train_dl) // args.grad_accum)
    total_steps = steps_per_epoch * args.epochs
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * args.warmup_ratio),
        num_training_steps=total_steps,
    )
    scaler = torch.cuda.amp.GradScaler(enabled=device == "cuda")

    best_wer = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        optimizer.zero_grad()
        for step, batch in enumerate(train_dl, 1):
            if batch is None:
                continue
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.cuda.amp.autocast(enabled=device == "cuda"):
                loss = model(**batch).loss / args.grad_accum
            scaler.scale(loss).backward()
            running += loss.item() * args.grad_accum
            if step % args.grad_accum == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()
            if step % 50 == 0:
                logger.info("epoch %d step %d loss %.4f", epoch, step, running / step)

        # ── Validation ──
        model.eval()
        preds: list[str] = []
        refs: list[str] = []
        with torch.no_grad():
            for batch in eval_dl:
                if batch is None:
                    continue
                labels = batch.pop("labels")
                batch = {k: v.to(device) for k, v in batch.items()}
                logits = model(**batch).logits
                ids = torch.argmax(logits, dim=-1).cpu()
                preds.extend(processor.batch_decode(ids))
                labels = labels.masked_fill(labels == -100, tokenizer.pad_token_id)
                refs.extend(
                    processor.batch_decode(labels, group_tokens=False)
                )
        e_wer, e_cer = wer(preds, refs), cer(preds, refs)
        logger.info(
            "epoch %d done · train_loss %.4f · eval WER %.4f · CER %.4f",
            epoch, running / max(len(train_dl), 1), e_wer, e_cer,
        )
        if e_wer < best_wer:
            best_wer = e_wer
            model.save_pretrained(out_dir)
            processor.save_pretrained(out_dir)
            logger.info("new best WER %.4f -> saved to %s", best_wer, out_dir)

    logger.info("Training complete. Best eval WER: %.4f", best_wer)
    logger.info(
        "Deploy: point ml/alignment/forced_alignment.py's ForcedAligner at %s "
        "(QARI_ALIGNER_MODEL_DIR).", out_dir,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    train(parse_args())


if __name__ == "__main__":
    main()
