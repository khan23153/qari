"""Research-only human vowel masks and native acoustic localization."""
import math
import re

from ml.training.human_word_data import OFFSETS, REFERENCES, _normalize

CONSONANTS = frozenset(range(1, 29))  # Pinned Muaalem43-token QPS alphabet.
VOWEL_TYPES = frozenset(('حركات', 'حركات وتجويد'))


def vowel_word_labels(row):
    ayah = row.get('ayah')
    if type(ayah) is not int or ayah not in REFERENCES:
        raise ValueError('Known audited Ikhlas ayah required')
    words = REFERENCES[ayah].split()
    result = [{'word_index': i, 'target': None, 'known': False} for i in range(len(words))]
    kind, location = row.get('source_error_type', ''), row.get('source_error_location', '')
    if row.get('source_label') == 'correct':
        if kind.strip() or location.strip():
            raise ValueError('Conflicting correct source annotation')
        return [{'word_index': i, 'target': 0, 'known': True} for i in range(len(words))]
    if row.get('source_label') != 'error' or not kind.strip() or not location.strip():
        raise ValueError('Explicit contributor error annotation required')
    kinds = [re.sub(r'\s+', ' ', value).strip() for value in re.split('[,،]', kind)]
    locations = [_normalize(value) for value in re.split('[,،]', location)]
    if len(kinds) != len(locations):
        return result
    for name, category in zip(locations, kinds):
        positions = [i for i, word in enumerate(words) if word == name]
        if category not in VOWEL_TYPES or len(positions) != 1 or (ayah == 3 and name == 'لم'):
            continue
        index = positions[0]
        slot = OFFSETS[ayah] + index
        if row['targets'][slot] != 1 or row['mask'][slot] != 1:
            raise ValueError('Vowel location differs from audited contributor word label')
        result[index] = {'word_index': index, 'target': 1, 'known': True}
    return result


def unique_exact_matches(expected, actual):
    """Exact token pairs forced by ALL minimal edit paths; no tie-breaking."""
    return {i:j for i,j in unique_consuming_pairs(expected,actual).items() if expected[i]==actual[j]}


def unique_consuming_pairs(expected, actual):
    """Forced edit pairs for assessment localization, never correctness evidence."""
    if (len(expected) > 256 or len(actual) > 256
            or any(type(token) is not int or not 1 <= token <= 42 for token in [*expected, *actual])):
        raise ValueError('Bounded native phoneme IDs required')
    n, m = len(expected), len(actual)
    forward = [[0] * (m + 1) for _ in range(n + 1)]
    backward = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        forward[i][0] = i
        backward[i][m] = n - i
    for j in range(m + 1):
        forward[0][j] = j
        backward[n][j] = m - j
    for i in range(n):
        for j in range(m):
            forward[i+1][j+1] = min(forward[i][j+1] + 1, forward[i+1][j] + 1,
                                     forward[i][j] + (expected[i] != actual[j]))
    for i in range(n-1, -1, -1):
        for j in range(m-1, -1, -1):
            backward[i][j] = min(backward[i+1][j] + 1, backward[i][j+1] + 1,
                                  backward[i+1][j+1] + (expected[i] != actual[j]))
    distance = forward[n][m]
    matches = {}
    for i in range(n):
        possibilities = set()
        for j in range(m + 1):
            if forward[i][j] + 1 + backward[i+1][j] == distance:
                possibilities.add(None)
            if j < m:
                same = expected[i] == actual[j]
                if forward[i][j] + (not same) + backward[i+1][j+1] == distance:
                    possibilities.add(j)
        if len(possibilities) == 1 and None not in possibilities:
            matches[i] = possibilities.pop()
    return matches


def local_word_crops(reference_ids, reference_word_indices, emissions, frame_count,
                     blank=0, min_confidence=.55, *, allow_substitutions=False):
    if (blank != 0 or type(frame_count) is not int or not 1 <= frame_count <= 600
            or type(allow_substitutions) is not bool
            or not math.isfinite(min_confidence) or not .55 <= min_confidence <= 1
            or not 1 <= len(reference_ids) <= 256 or len(reference_ids) != len(reference_word_indices)
            or any(type(t) is not int or not 1 <= t <= 42 for t in reference_ids)
            or any(type(i) is not int or not 0 <= i < 64 for i in reference_word_indices)
            or any(b < a for a, b in zip(reference_word_indices, reference_word_indices[1:]))
            or len(emissions) > frame_count):
        raise ValueError('Invalid bounded native crop contract')
    previous = 0
    for emission in emissions:
        token, left, right, confidence = (emission.get(k) for k in
                                          ('id', 'start_frame', 'end_frame', 'confidence'))
        if (type(token) is not int or not 1 <= token <= 42
                or type(left) is not int or type(right) is not int
                or not previous <= left < right <= frame_count
                or not isinstance(confidence, (float, int))
                or not math.isfinite(confidence) or not 0 <= confidence <= 1):
            raise ValueError('Malformed native phoneme emission')
        previous = right
    reference = [(token, word) for token, word in zip(reference_ids, reference_word_indices)
                 if token in CONSONANTS]
    native = [row for row in emissions if row['id'] in CONSONANTS]
    expected = [token for token, _ in reference]
    actual = [r['id'] for r in native]
    paired = (unique_consuming_pairs if allow_substitutions else unique_exact_matches)(expected,actual)
    result = []
    for word in range(max(reference_word_indices) + 1):
        wanted = [i for i, (_, owner) in enumerate(reference) if owner == word]
        item = {'word_index': word, 'available': False, 'frame_start': None, 'frame_end': None,
                'reference_ids': [token for token, owner in zip(reference_ids, reference_word_indices)
                                  if owner == word], 'reason': 'ambiguous_native_anchors'}
        if not wanted or any(i not in paired for i in wanted):
            result.append(item); continue
        indices = [paired[i] for i in wanted]
        if allow_substitutions and len(indices)<2:
            item['reason']='insufficient_native_anchors'
            result.append(item); continue
        if allow_substitutions and not any(expected[i]==actual[paired[i]] for i in wanted):
            item['reason']='no_exact_native_anchor'
            result.append(item); continue
        if indices != list(range(indices[0], indices[-1] + 1)):
            item['reason'] = 'noncontiguous_native_consonants'
        elif any(native[i]['confidence'] < min_confidence for i in indices):
            item['reason'] = 'low_native_confidence'
        else:
            left = native[indices[0]]['start_frame']
            right = native[indices[-1]+1]['start_frame'] if indices[-1]+1 < len(native) else frame_count
            if not 2 <= right - left <= 150 or not 1 <= len(item['reference_ids']) <= 64:
                item['reason'] = 'outside_word_frame_bounds'
            else:
                item.update(available=True, frame_start=left, frame_end=right, reason=None,
                            native_anchor_indices=indices)
                if allow_substitutions:
                    item.update(native_consonant_ids=[actual[i] for i in indices],
                                native_anchor_types=['exact' if expected[i]==actual[paired[i]]
                                                     else 'substitution' for i in wanted])
        result.append(item)
    return result
