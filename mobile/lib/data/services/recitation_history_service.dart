import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/recitation_session_record.dart';

/// Local persistence for AI-Recitation session history + streak tracking.
///
/// All data is stored in SharedPreferences as a single JSON list (capped to the
/// most recent [maxRecords] sessions) plus a denormalized streak count. The
/// streak is recomputed from actual session dates on every write so it can
/// never silently drift out of sync with the user's real activity.
class RecitationHistoryService {
  static const _kHistory = 'recitation_history';
  static const _kStreak = 'recitation_streak';
  static const _kLastActiveDate = 'recitation_last_active_date';

  static const int maxRecords = 200;

  final SharedPreferences _prefs;

  RecitationHistoryService(this._prefs);

  /// Records a completed session, updates the streak, and returns the saved
  /// record (with a freshly assigned id).
  RecitationSessionRecord saveSession({
    required String scope,
    required int surahNumber,
    required int ayahFrom,
    required int ayahTo,
    required double overallScore,
    required int correctCount,
    required int totalCount,
    required int durationSeconds,
    List<RecitationMistake> mistakes = const [],
  }) {
    final record = RecitationSessionRecord(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      scope: scope,
      surahNumber: surahNumber,
      ayahFrom: ayahFrom,
      ayahTo: ayahTo,
      recordedAt: DateTime.now(),
      overallScore: overallScore,
      correctCount: correctCount,
      totalCount: totalCount,
      durationSeconds: durationSeconds,
      mistakes: mistakes,
    );

    // A no-speech backend response is carried through the current mobile model
    // as one private sentinel verdict/mistake. It is a failed capture attempt,
    // not Quran practice: do not add it to history or advance the streak.
    final isNoSpeechAttempt = totalCount == 1 &&
        correctCount == 0 &&
        mistakes.length == 1 &&
        mistakes.first.errorType == 'no_speech';
    if (isNoSpeechAttempt) {
      return record;
    }

    final all = _readAll();
    all.insert(0, record);
    if (all.length > maxRecords) {
      all.removeRange(maxRecords, all.length);
    }
    _writeAll(all);
    _updateStreak(record.recordedAt);
    return record;
  }

  /// Replaces a previously saved record (matched by id) — used when a session
  /// is re-finalized with a richer result.
  void updateSession(RecitationSessionRecord record) {
    final all = _readAll();
    final idx = all.indexWhere((r) => r.id == record.id);
    if (idx >= 0) {
      all[idx] = record;
      _writeAll(all);
    }
  }

  List<RecitationSessionRecord> getAll() => _readAll();

  void deleteAll() {
    _prefs.remove(_kHistory);
    _prefs.remove(_kStreak);
    _prefs.remove(_kLastActiveDate);
  }

  // ─── Streak ───────────────────────────────────────────────────────────
  /// Consecutive-day streak ending today (or yesterday if today has no session
  /// yet). Recomputed from the real session dates so it is always accurate.
  int getStreak() {
    final dates = _readAll()
        .map((r) => _dayKey(r.recordedAt))
        .toSet()
        .toList()
      ..sort();
    if (dates.isEmpty) return 0;

    final today = _dayKey(DateTime.now());
    final yesterday = _dayKey(DateTime.now().subtract(const Duration(days: 1)));

    // Streak only "counts" if the user practiced today or yesterday.
    if (dates.last != today && dates.last != yesterday) return 0;

    int streak = 1;
    for (var i = dates.length - 1; i > 0; i--) {
      final diff = dates[i].difference(dates[i - 1]).inDays;
      if (diff == 1) {
        streak++;
      } else if (diff == 0) {
        continue;
      } else {
        break;
      }
    }
    return streak;
  }

  int getSessionCount() => _readAll().length;

  void _updateStreak(DateTime sessionDate) {
    _prefs.setInt(_kStreak, getStreak());
    _prefs.setString(_kLastActiveDate, _dayKey(sessionDate).toIso8601String());
  }

  // ─── IO ───────────────────────────────────────────────────────────────
  List<RecitationSessionRecord> _readAll() {
    final raw = _prefs.getString(_kHistory);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list
          .map((e) => RecitationSessionRecord.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  void _writeAll(List<RecitationSessionRecord> records) {
    final raw = jsonEncode(records.map((r) => r.toJson()).toList());
    _prefs.setString(_kHistory, raw);
  }

  /// Midnight-UTC day bucket for a date (used for streak math).
  static DateTime _dayKey(DateTime d) =>
      DateTime.utc(d.year, d.month, d.day);
}