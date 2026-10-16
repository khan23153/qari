"""Compare consecutive unprompted native views of one bounded audio occurrence.

RNNT emission frames are not acoustic word boundaries. A first partial decode
can omit a token or commit an early frame for its following word. Two mature,
agreeing native triples can independently identify that gap without inventing
an old hypothesis slot or moving the tracking cursor.
"""
from __future__ import annotations

import math


def prove_native_word_repair(previous, current, *, expected, before_span,
                             after_span, identity, threshold, sample_rate,
                             total_samples, right_context_seconds):
    """Return native provenance, or None if identity/time/occurrence is uncertain."""
    frame = .08
    epsilon = 1e-5  # Float32 bounds accumulate rounding at long offsets.
    anchor_drift = .4  # Partial-window first emissions can move up to five frames.
    try:
        if (sample_rate != 16000 or previous is None or current is None
                or not 0 <= threshold <= 1 or not math.isfinite(threshold)):
            return None
        expected = tuple(identity(word) for word in expected)
        if len(expected) != 3 or not all(expected) or len(set(expected)) != 3:
            return None
        left_begin, left_end = before_span
        right_begin, right_end = after_span
        if (not all(math.isfinite(v) for v in (*before_span, *after_span))
                or not 0 <= left_begin <= left_end
                or not left_end + frame <= right_begin + epsilon
                or not right_begin <= right_end):
            return None
        endpoints = []
        witnesses = []
        for view in (previous, current):
            start, endpoint, words, scores, timings = view
            if (not 0 <= start < endpoint <= total_samples
                    or not len(words) == len(scores) == len(timings)
                    or (endpoint - start) / sample_rate > 21. + epsilon):
                return None
            endpoints.append(endpoint)
            origin = start / sample_rate
            seconds = (endpoint - start) / sample_rate
            absolute = []
            last_begin = -1.
            for word, score, (begin, end) in zip(words, scores, timings):
                if (not isinstance(word, str) or not word
                        or not all(math.isfinite(v) for v in (score, begin, end))
                        or not 0 <= score <= 1
                        or not 0 <= begin <= end <= seconds + frame
                        or begin < last_begin):
                    return None
                last_begin = begin
                absolute.append((origin + begin, origin + end))
            # Identify the ORIGINAL anchor occurrences before considering a
            # correct middle word. A nearby later rereading must not erase an
            # explicit earlier mistake. Even weak competing anchors leave the
            # occurrence ambiguous; they cannot simply be discarded.
            left_hits = [j for j, word in enumerate(words)
                         if identity(word) == expected[0]
                         and abs(absolute[j][0] - left_begin) <= anchor_drift + epsilon]
            right_hits = [j for j, word in enumerate(words)
                          if identity(word) == expected[2]
                          and abs(absolute[j][0] - right_begin) <= anchor_drift + epsilon]
            if len(left_hits) != 1 or len(right_hits) != 1:
                return None
            candidates = []
            for i in range(1, len(words) - 1):
                if (i - 1 != left_hits[0] or i + 1 != right_hits[0]
                        or tuple(identity(word) for word in words[i-1:i+2]) != expected
                        or any(score < threshold for score in scores[i-1:i+2])):
                    continue
                spans = tuple(absolute[i-1:i+2])
                if (left_begin < origin - epsilon
                        or abs(spans[0][0] - left_begin) > anchor_drift + epsilon
                        or abs(spans[2][0] - right_begin) > anchor_drift + epsilon
                        or spans[0][1] + frame > spans[1][0] + epsilon
                        or spans[1][1] + frame > spans[2][0] + epsilon
                        or spans[1][0] < left_end - frame - epsilon
                        or spans[1][1] > right_begin + anchor_drift + epsilon
                        or max(end for _, end in spans) + frame
                           > endpoint / sample_rate - right_context_seconds + epsilon):
                    continue
                # A second strong token on an identifying frame makes the
                # occurrence ambiguous even if its recognized text agrees.
                if any(j not in (i-1, i, i+1) and scores[j] >= threshold
                       and any(abs(bounds[0] - span[0]) <= frame + epsilon for span in spans)
                       for j, bounds in enumerate(absolute)):
                    continue
                candidates.append((words[i], scores[i], spans))
            if len(candidates) != 1:
                return None
            witnesses.append(candidates[0])
        if endpoints[1] <= endpoints[0]:
            return None
        old, new = witnesses
        if identity(old[0]) != identity(new[0]):
            return None
        if any(abs(a[0] - b[0]) > frame + epsilon
               or max(a[0], b[0]) > min(a[1] + frame, b[1] + frame) + epsilon
               for a, b in zip(old[2], new[2])):
            return None
        return {'word': new[0], 'confidence': new[1], 'endpoints': endpoints,
                'previous_spans': old[2], 'spans': new[2]}
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
