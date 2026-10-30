import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../../data/services/api_client.dart';
import 'library_models.dart';
import 'library_repository.dart';
import 'local_library_repository.dart';

/// Library data that works out of the box: the API when it answers, the
/// bundled snapshot when it does not.
///
/// Any remote failure (404 because the library route is not deployed yet, no
/// connection, timeout, 5xx, or an unparseable response) falls back to
/// [local]. After a failure the API is skipped for [retryAfter], so offline
/// screens do not each wait out a timeout. A 404 for one specific record
/// while the API is otherwise up is a real "not found": it is tried locally
/// but does not mark the app offline.
class FallbackLibraryRepository implements LibraryRepository {
  FallbackLibraryRepository({
    required this.remote,
    required this.local,
    this.remoteTimeout = const Duration(seconds: 8),
    this.retryAfter = const Duration(minutes: 2),
    DateTime Function()? clock,
  }) : _clock = clock ?? DateTime.now;

  final LibraryRepository remote;
  final LibraryRepository local;
  final Duration remoteTimeout;
  final Duration retryAfter;
  final DateTime Function() _clock;

  /// True while screens are being served from the bundled snapshot.
  final ValueNotifier<bool> usingBundledData = ValueNotifier(false);

  DateTime? _remoteDownUntil;

  bool get _remoteDown {
    final until = _remoteDownUntil;
    return until != null && _clock().isBefore(until);
  }

  Future<T> _run<T>(Future<T> Function(LibraryRepository repo) call, {bool singleRecord = false}) async {
    if (!_remoteDown) {
      try {
        final result = await call(remote).timeout(remoteTimeout);
        _remoteDownUntil = null;
        usingBundledData.value = false;
        return result;
      } catch (error, stack) {
        final recordMissing = singleRecord && error is ApiException && error.isNotFound;
        if (!recordMissing) _remoteDownUntil = _clock().add(retryAfter);
        try {
          final result = await call(local);
          if (!recordMissing) usingBundledData.value = true;
          return result;
        } on LibraryNotBundledException {
          // Nothing offline either: report the server's own error.
          Error.throwWithStackTrace(error, stack);
        }
      }
    }
    final result = await call(local);
    usingBundledData.value = true;
    return result;
  }

  @override
  Future<List<LibraryCategory>> categories() => _run((r) => r.categories());

  @override
  Future<LibraryPage<LibraryCollection>> collections({String? category, int page = 1, int pageSize = 50}) =>
      _run((r) => r.collections(category: category, page: page, pageSize: pageSize));

  @override
  Future<LibraryPage<LibraryBook>> books(String slug, {int page = 1, int pageSize = 100}) =>
      _run((r) => r.books(slug, page: page, pageSize: pageSize));

  @override
  Future<LibraryPage<HadithSummary>> bookHadiths(String slug, int book, {int page = 1, int pageSize = 20}) =>
      _run((r) => r.bookHadiths(slug, book, page: page, pageSize: pageSize));

  @override
  Future<LibraryPage<HadithSummary>> hadiths({String graded = 'all', int page = 1, int pageSize = 20}) =>
      _run((r) => r.hadiths(graded: graded, page: page, pageSize: pageSize));

  @override
  Future<HadithDetail> hadith(String id) => _run((r) => r.hadith(id), singleRecord: true);

  @override
  Future<NarratorProfile> narrator(String id) => _run((r) => r.narrator(id), singleRecord: true);

  /// The API answers "no entry" with null, which an undeployed route also
  /// produces, so a null from the server is double-checked offline.
  @override
  Future<GharibEntry?> gharib(String word) async {
    final entry = await _run((r) => r.gharib(word), singleRecord: true);
    return entry ?? await local.gharib(word);
  }

  @override
  Future<LibrarySearchResult> search(String query) => _run((r) => r.search(query));
}
