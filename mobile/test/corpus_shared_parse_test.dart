import 'dart:io';
import 'dart:isolate';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/repositories/local_corpus_repository.dart';

/// The bundled Quran is ~48 MB of JSON. Every screen makes its own
/// [LocalCorpusRepository]; they must share ONE parse, or low-memory phones
/// run out of RAM (the app is killed when live recitation opens).
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    LocalCorpusRepository.resetSharedCache();
    LocalCorpusRepository.shareParse = true;
  });
  tearDown(() {
    LocalCorpusRepository.shareParse = false;
    LocalCorpusRepository.resetSharedCache();
  });

  test('many repositories parse the corpus once', () async {
    final before = LocalCorpusRepository.parseCount;
    final results = await Future.wait([
      LocalCorpusRepository().getAyahs(1),
      LocalCorpusRepository().getAyahs(2),
      LocalCorpusRepository().getAyahsByPage(3),
      LocalCorpusRepository().getAyahs(114),
    ]);
    await LocalCorpusRepository().getAyahs(36);
    expect(LocalCorpusRepository.parseCount - before, 1);
    expect(results[0], hasLength(7));
    expect(results[1], hasLength(286));
    expect(results[3], hasLength(6));
  });

  test('the parser runs in a background isolate', () async {
    final bytes = Uint8List.fromList(
      File('assets/quran_corpus.json.gz').readAsBytesSync(),
    );
    final bySurah = await Isolate.run(() => parseCorpusBundle(bytes));
    expect(bySurah, hasLength(114));
    expect(bySurah[1]!.first.words, isNotEmpty);
    expect(bySurah.values.fold<int>(0, (n, a) => n + a.length), 6236);
  });
}
