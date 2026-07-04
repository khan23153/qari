"""
Tajweed classifier training script.

Trains binary classifiers for tajweed rule detection (ghunnah, qalqalah,
madd, ikhfa, idgham). Each classifier predicts whether a given audio
segment correctly applies a specific tajweed rule.

The classifiers use audio features (spectral, temporal, energy) extracted
from word-level segments, fed into a lightweight neural network or
gradient-boosted model.

Usage:
    python -m ml.training.train_tajweed_classifier \\
        --rule ghunnah \\
        --data_dir /data/tajweed_labels \\
        --output_dir /models/tajweed_classifiers \\
        --model_type xgboost \\
        --epochs 50

Dataset format (per-rule JSON manifest):
    [
        {
            "audio_path": "/data/audio/sample_001.wav",
            "word_index": 3,
            "start_ms": 1200,
            "end_ms": 1800,
            "label": 1,            // 1 = correct, 0 = incorrect
            "rule": "ghunnah",
            "letter": "ن",
            "surah": 1,
            "ayah": 1
        },
        ...
    ]
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Defaults ─────────────────────────────────────────────────────────────────

SUPPORTED_RULES = ["ghunnah", "qalqalah", "madd", "ikhfa", "idgham"]
DEFAULT_MODEL_TYPE = "xgboost"
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 32
DEFAULT_LR = 1e-3
SAMPLE_RATE = 16000


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train a tajweed rule classifier"
    )
    parser.add_argument(
        "--rule", type=str, required=True, choices=SUPPORTED_RULES,
        help="Tajweed rule to train classifier for"
    )
    parser.add_argument(
        "--data_dir", type=str, required=True,
        help="Directory containing labeled tajweed data"
    )
    parser.add_argument(
        "--output_dir", type=str, default="./tajweed_classifiers",
        help="Output directory for trained classifier"
    )
    parser.add_argument(
        "--model_type", type=str, default=DEFAULT_MODEL_TYPE,
        choices=["xgboost", "neural", "random_forest", "logistic"],
        help="Type of classifier to train"
    )
    parser.add_argument(
        "--epochs", type=int, default=DEFAULT_EPOCHS,
        help="Training epochs (neural model only)"
    )
    parser.add_argument(
        "--batch_size", type=int, default=DEFAULT_BATCH_SIZE,
        help="Training batch size"
    )
    parser.add_argument(
        "--learning_rate", type=float, default=DEFAULT_LR,
        help="Learning rate"
    )
    parser.add_argument(
        "--test_split", type=float, default=0.2,
        help="Fraction of data to use for testing"
    )
    return parser.parse_args()


# ── Feature extraction ───────────────────────────────────────────────────────

def extract_features(
    audio: np.ndarray,
    start_ms: int,
    end_ms: int,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """
    Extract acoustic features from an audio segment for tajweed classification.

    Features:
    1. Duration (ms)
    2. Mean RMS energy
    3. Max RMS energy
    4. Energy variance
    5. Spectral centroid (mean)
    6. Spectral centroid (std)
    7. Spectral rolloff
    8. Zero-crossing rate (mean)
    9. Zero-crossing rate (std)
    10. Energy rise time (ms to peak)
    11. Energy decay ratio (peak to end)
    12. Number of energy segments
    13. Spectral flux (mean)
    14. Spectral flatness

    Parameters
    ----------
    audio : np.ndarray
        Full audio signal.
    start_ms, end_ms : int
        Segment boundaries in milliseconds.
    sr : int
        Sample rate.

    Returns
    -------
    np.ndarray
        Feature vector of shape (14,).
    """
    start_s = int(start_ms * sr / 1000)
    end_s = int(end_ms * sr / 1000)
    segment = audio[start_s:end_s]

    if len(segment) < 4:
        return np.zeros(14)

    duration_ms = end_ms - start_ms

    # Energy features
    frame_size = int(sr * 0.01)  # 10ms frames
    n_frames = max(1, len(segment) // frame_size)
    rms_frames = np.array([
        np.sqrt(np.mean(segment[i*frame_size:(i+1)*frame_size].astype(np.float64)**2) + 1e-10)
        for i in range(n_frames)
    ])

    mean_rms = float(np.mean(rms_frames))
    max_rms = float(np.max(rms_frames))
    var_rms = float(np.var(rms_frames))

    # Rise time and decay
    peak_idx = int(np.argmax(rms_frames))
    rise_time_ms = peak_idx * 10
    if peak_idx < n_frames - 1:
        post_peak = rms_frames[peak_idx:]
        decay_ratio = float((post_peak[0] - post_peak[-1]) / (post_peak[0] + 1e-10))
    else:
        decay_ratio = 0.0

    # Number of segments (gaps in energy)
    threshold = max_rms * 0.3
    above = rms_frames > threshold
    n_segments = 0
    in_seg = False
    for a in above:
        if a and not in_seg:
            n_segments += 1
            in_seg = True
        elif not a:
            in_seg = False

    # Spectral features
    fft = np.fft.rfft(segment.astype(np.float64))
    magnitude = np.abs(fft)
    freqs = np.fft.rfftfreq(len(segment), 1.0 / sr)

    if magnitude.sum() > 0:
        centroid = float(np.sum(freqs * magnitude) / np.sum(magnitude))
    else:
        centroid = 0.0

    # Spectral centroid std (using sub-windows)
    sub_centroids = []
    sub_size = max(4, len(segment) // 4)
    for i in range(0, len(segment) - sub_size, sub_size):
        sub = segment[i:i+sub_size]
        if len(sub) < 4:
            continue
        sub_fft = np.abs(np.fft.rfft(sub.astype(np.float64)))
        sub_freqs = np.fft.rfftfreq(len(sub), 1.0 / sr)
        if sub_fft.sum() > 0:
            sub_centroids.append(np.sum(sub_freqs * sub_fft) / np.sum(sub_fft))
    centroid_std = float(np.std(sub_centroids)) if sub_centroids else 0.0

    # Spectral rolloff (85th percentile of energy)
    cumulative = np.cumsum(magnitude)
    total = cumulative[-1] if len(cumulative) > 0 else 1.0
    rolloff_idx = np.searchsorted(cumulative, 0.85 * total)
    rolloff = float(freqs[rolloff_idx]) if rolloff_idx < len(freqs) else 0.0

    # Zero-crossing rate
    signs = np.sign(segment)
    zcr = np.mean(np.abs(np.diff(signs)) > 0)
    zcr_std = float(np.std([
        np.mean(np.abs(np.diff(signs[i*frame_size:(i+1)*frame_size])) > 0)
        for i in range(n_frames) if (i+1)*frame_size <= len(signs)
    ])) if n_frames > 1 else 0.0

    # Spectral flux (change in spectrum between frames)
    if n_frames > 1:
        fluxes = []
        for i in range(1, n_frames):
            f1 = np.abs(np.fft.rfft(segment[(i-1)*frame_size:i*frame_size].astype(np.float64)))
            f2 = np.abs(np.fft.rfft(segment[i*frame_size:(i+1)*frame_size].astype(np.float64)))
            min_len = min(len(f1), len(f2))
            flux = np.sum((f2[:min_len] - f1[:min_len])**2)
            fluxes.append(flux)
        spectral_flux = float(np.mean(fluxes)) if fluxes else 0.0
    else:
        spectral_flux = 0.0

    # Spectral flatness (geometric mean / arithmetic mean)
    log_mag = np.log(magnitude + 1e-10)
    geo_mean = np.exp(np.mean(log_mag))
    arith_mean = np.mean(magnitude)
    flatness = float(geo_mean / (arith_mean + 1e-10)) if arith_mean > 0 else 0.0

    features = np.array([
        duration_ms,
        mean_rms,
        max_rms,
        var_rms,
        centroid,
        centroid_std,
        rolloff,
        zcr,
        zcr_std,
        rise_time_ms,
        decay_ratio,
        n_segments,
        spectral_flux,
        flatness,
    ], dtype=np.float32)

    return features


FEATURE_NAMES = [
    "duration_ms", "mean_rms", "max_rms", "var_rms",
    "spectral_centroid", "spectral_centroid_std", "spectral_rolloff",
    "zcr", "zcr_std", "rise_time_ms", "decay_ratio",
    "n_segments", "spectral_flux", "spectral_flatness",
]


# ── Data loading ─────────────────────────────────────────────────────────────

def load_labeled_data(
    data_dir: str,
    rule: str,
    sr: int = SAMPLE_RATE,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Load labeled tajweed data for a specific rule.

    Parameters
    ----------
    data_dir : str
        Directory containing labeled data JSON files.
    rule : str
        Tajweed rule name.
    sr : int
        Sample rate for audio loading.

    Returns
    -------
    X : np.ndarray, shape (n_samples, n_features)
        Feature matrix.
    y : np.ndarray, shape (n_samples,)
        Binary labels (1 = correct, 0 = incorrect).
    """
    import soundfile as sf

    data_path = Path(data_dir) / f"{rule}_labels.json"
    if not data_path.exists():
        # Try generic manifest
        data_path = Path(data_dir) / "manifest.json"
    if not data_path.exists():
        raise FileNotFoundError(f"No labeled data found in {data_dir} for rule '{rule}'")

    with open(data_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # Filter by rule
    samples = [s for s in samples if s.get("rule") == rule]

    if not samples:
        raise ValueError(f"No samples found for rule '{rule}'")

    features_list: list[np.ndarray] = []
    labels_list: list[int] = []

    for sample in samples:
        audio_path = sample["audio_path"]
        try:
            audio, _ = sf.read(audio_path, dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)

            feats = extract_features(
                audio,
                sample["start_ms"],
                sample["end_ms"],
                sr,
            )
            features_list.append(feats)
            labels_list.append(sample["label"])
        except Exception as e:
            logger.warning("Could not load %s: %s", audio_path, e)

    X = np.stack(features_list)
    y = np.array(labels_list, dtype=np.float32)

    logger.info("Loaded %d samples for rule '%s' (positive: %d, negative: %d)",
                len(y), rule, int(y.sum()), int((1 - y).sum()))

    return X, y


# ── Model training ───────────────────────────────────────────────────────────

def train_xgboost(X_train: np.ndarray, y_train: np.ndarray, **kwargs):
    """Train an XGBoost classifier."""
    from sklearn.ensemble import GradientBoostingClassifier

    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model


def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, **kwargs):
    """Train a Random Forest classifier."""
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def train_logistic(X_train: np.ndarray, y_train: np.ndarray, **kwargs):
    """Train a logistic regression classifier."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        random_state=42,
    )
    model.fit(X_scaled, y_train)

    # Return a wrapper that includes the scaler
    class ScaledModel:
        def __init__(self, model, scaler):
            self.model = model
            self.scaler = scaler

        def predict(self, X):
            return self.model.predict(self.scaler.transform(X))

        def predict_proba(self, X):
            return self.model.predict_proba(self.scaler.transform(X))

    return ScaledModel(model, scaler)


def train_neural(
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 1e-3,
    **kwargs,
):
    """Train a simple neural network classifier."""
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    X_tensor = torch.from_numpy(X_scaled).float()
    y_tensor = torch.from_numpy(y_train).float()

    dataset = TensorDataset(X_tensor, y_tensor)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    n_features = X_train.shape[1]

    class TajweedNet(nn.Module):
        def __init__(self, input_dim: int):
            super().__init__()
            self.fc1 = nn.Linear(input_dim, 64)
            self.fc2 = nn.Linear(64, 32)
            self.fc3 = nn.Linear(32, 1)
            self.relu = nn.ReLU()
            self.dropout = nn.Dropout(0.3)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = self.relu(self.fc1(x))
            x = self.dropout(x)
            x = self.relu(self.fc2(x))
            x = self.dropout(x)
            x = self.sigmoid(self.fc3(x))
            return x.squeeze(-1)

    model = TajweedNet(n_features)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for batch_X, batch_y in loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            logger.info("Epoch %d/%d, loss: %.4f", epoch + 1, epochs, total_loss / len(loader))

    model.eval()

    class NeuralWrapper:
        def __init__(self, model, scaler):
            self.model = model
            self.scaler = scaler

        def predict(self, X):
            X_scaled = self.scaler.transform(X)
            with torch.no_grad():
                preds = self.model(torch.from_numpy(X_scaled).float())
            return (preds.numpy() > 0.5).astype(int)

        def predict_proba(self, X):
            X_scaled = self.scaler.transform(X)
            with torch.no_grad():
                probs = self.model(torch.from_numpy(X_scaled).float())
            probs = probs.numpy()
            return np.column_stack([1 - probs, probs])

    return NeuralWrapper(model, scaler)


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    model_type: str,
    *,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 1e-3,
    test_split: float = 0.2,
):
    """
    Train a classifier and evaluate on a held-out test set.

    Returns
    -------
    model, metrics : trained model and dict of evaluation metrics
    """
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_split, random_state=42, stratify=y
    )

    trainers = {
        "xgboost": train_xgboost,
        "random_forest": train_random_forest,
        "logistic": train_logistic,
        "neural": lambda X, y, **kw: train_neural(X, y, epochs=epochs, batch_size=batch_size, lr=lr),
    }

    trainer = trainers.get(model_type, train_xgboost)
    model = trainer(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)) if len(np.unique(y_test)) > 1 else 0.0,
    }

    logger.info("Model evaluation (%s): %s", model_type, json.dumps(metrics, indent=2))
    return model, metrics


def save_model(model, output_dir: Path, rule: str, model_type: str, metrics: dict) -> None:
    """Save the trained model and metadata."""
    import joblib

    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"{rule}_{model_type}.joblib"
    joblib.dump(model, model_path)

    metadata = {
        "rule": rule,
        "model_type": model_type,
        "metrics": metrics,
        "feature_names": FEATURE_NAMES,
    }
    meta_path = output_dir / f"{rule}_{model_type}_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Model saved to %s", model_path)


def main() -> None:
    """Entry point for the tajweed classifier training script."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()

    logger.info("Training tajweed classifier for rule: %s", args.rule)

    X, y = load_labeled_data(args.data_dir, args.rule)
    model, metrics = train_model(
        X, y, args.model_type,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.learning_rate,
        test_split=args.test_split,
    )

    output_dir = Path(args.output_dir)
    save_model(model, output_dir, args.rule, args.model_type, metrics)

    logger.info("Training complete for rule '%s'", args.rule)


if __name__ == "__main__":
    main()
