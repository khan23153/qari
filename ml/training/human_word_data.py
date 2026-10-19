"""Strict human binary-word annotations; no synthetic or inferred phone targets."""
import hashlib
import math
import re
import unicodedata

REFERENCES = {
    1: 'قل هو الله احد', 2: 'الله الصمد', 3: 'لم يلد ولم يولد',
    4: 'ولم يكن له كفوا احد',
}
OFFSETS = {1: 0, 2: 4, 3: 6, 4: 10}


def _normalize(value):
    # Location lookup only; these strings never become acoustic phone labels.
    value = unicodedata.normalize('NFKC', value)
    value = ''.join(c for c in value if unicodedata.category(c) != 'Mn' and c != 'ـ')
    return value.translate(str.maketrans('ٱأإآ', 'اااا')).strip()


def parse_label_row(row, reserved_speakers):
    name = row.get('file_name', '')
    match = re.fullmatch(r'data/ID(\d+)V([1-4])([TF])\.wav', name)
    if not match:
        raise ValueError('Invalid public source path')
    speaker = str(int(match.group(1)))
    ayah = int(match.group(2))
    correct = row.get('label') == '1'
    if (row.get('label') not in ('0', '1') or row.get('label_name') != ('correct' if correct else 'error')
            or match.group(3) != ('T' if correct else 'F')):
        raise ValueError('Conflicting explicit label/name/filename')
    if row.get('verse_number') != str(ayah):
        raise ValueError('Source ayah conflict')
    words = _normalize(row.get('verse_text', '')).split()
    if words != REFERENCES[ayah].split():
        raise ValueError('Reference text conflict')
    targets, mask = [0] * 15, [0] * 15
    if correct:
        if any(row.get(key, '').strip() for key in ('error_location', 'error_type', 'error_explanation')):
            raise ValueError('Correct label has conflicting error annotations')
        for i in range(len(words)):
            mask[OFFSETS[ayah] + i] = 1
    else:
        locations = [_normalize(s) for s in re.split('[,،]', row.get('error_location', ''))]
        if not locations or any(not s for s in locations) or not row.get('error_type', '').strip():
            raise ValueError('Missing human error annotation')
        for word in locations:
            indices = [i for i, reference in enumerate(words) if reference == word]
            if len(indices) != 1 or (ayah == 3 and word == 'لم'):
                raise ValueError('Unmapped or ambiguous repeated error location')
            slot = OFFSETS[ayah] + indices[0]
            targets[slot], mask[slot] = 1, 1
    bucket = int(hashlib.sha256(('qari-human-word-v1:' + speaker).encode()).hexdigest()[:8], 16) % 10
    role = 'validation' if bucket == 0 else 'test' if bucket == 1 else 'train'
    if speaker in reserved_speakers:
        role = 'reserved'
    return {'id': name[5:-4], 'source_file': name, 'speaker_id': speaker,
            'ayah': ayah, 'surah': 112, 'role': role, 'targets': targets, 'mask': mask,
            'source_label': row['label_name'], 'source_error_type': row.get('error_type', ''),
            'source_error_location': row.get('error_location', '')}


def select_threshold(validation_rows):
    rows = list(validation_rows)
    if not rows or any(r.get('role') != 'validation' or r.get('target') not in (0, 1)
                       or not math.isfinite(r.get('score', math.nan))
                       or not 0 <= r['score'] <= 1 for r in rows):
        raise ValueError('Threshold selection requires only explicit known validation labels')
    bad = [r for r in rows if r['target'] == 1]
    good = [r for r in rows if r['target'] == 0]
    if not bad or not good:
        raise ValueError('Both human label classes required for validation')
    candidates = [2.] + sorted({r['score'] for r in rows})
    eligible = []
    for threshold in candidates:
        false_alarms = sum(r['score'] >= threshold for r in good) / len(good)
        if false_alarms <= .02:
            recall = sum(r['score'] >= threshold for r in bad) / len(bad)
            eligible.append((recall, -false_alarms, threshold))
    return max(eligible)[2]
