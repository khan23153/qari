import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'similar_verses.dart';

/// One pair of similar ayahs the reciter has slid between, and how often.
class SlipRecord {
  const SlipRecord({
    required this.from,
    required this.to,
    required this.count,
    required this.lastAt,
  });

  final String from;
  final String to;
  final int count;
  final DateTime lastAt;

  factory SlipRecord.fromJson(Map<String, dynamic> json) => SlipRecord(
        from: json['from'] as String,
        to: json['to'] as String,
        count: (json['count'] as num?)?.toInt() ?? 1,
        lastAt: DateTime.tryParse(json['last_at'] as String? ?? '') ??
            DateTime.fromMillisecondsSinceEpoch(0),
      );

  Map<String, dynamic> toJson() => {
        'from': from,
        'to': to,
        'count': count,
        'last_at': lastAt.toIso8601String(),
      };
}

/// The reciter's own list of similar-verse slips, kept on the phone so the
/// pairs they mix up can be revised later.
class SlipStore {
  SlipStore({SharedPreferences? prefs}) : _prefs = prefs;

  static const _key = 'hifz_similar_slips';

  SharedPreferences? _prefs;

  Future<SharedPreferences> get _p async =>
      _prefs ??= await SharedPreferences.getInstance();

  Future<List<SlipRecord>> all() async {
    final raw = (await _p).getString(_key);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = (jsonDecode(raw) as List<dynamic>)
          .map((e) => SlipRecord.fromJson(e as Map<String, dynamic>))
          .toList();
      list.sort((a, b) {
        final byCount = b.count.compareTo(a.count);
        return byCount != 0 ? byCount : b.lastAt.compareTo(a.lastAt);
      });
      return list;
    } catch (_) {
      return [];
    }
  }

  /// Counts one more slip from [slip.from] into [slip.to].
  Future<void> record(SimilarVerseSlip slip, {DateTime? at}) async {
    final when = at ?? DateTime.now();
    final list = await all();
    final i = list.indexWhere((r) => r.from == slip.from && r.to == slip.to);
    final next = SlipRecord(
      from: slip.from,
      to: slip.to,
      count: i >= 0 ? list[i].count + 1 : 1,
      lastAt: when,
    );
    if (i >= 0) {
      list[i] = next;
    } else {
      list.add(next);
    }
    await (await _p)
        .setString(_key, jsonEncode(list.map((r) => r.toJson()).toList()));
  }
}
