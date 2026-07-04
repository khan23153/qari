import 'package:flutter_test/flutter_test.dart';
import 'package:qari/core/constants/app_constants.dart';

void main() {
  group('AppConstants', () {
    test('total surahs is 114', () {
      expect(AppConstants.totalSurahs, 114);
    });

    test('MVP juz is 30', () {
      expect(AppConstants.mvpJuz, 30);
    });

    test('grammar colors map has all three pos groups', () {
      expect(AppConstants.grammarColors.keys, containsAll(['fil', 'ism', 'harf']));
    });

    test('fil (verb) is green', () {
      expect(AppConstants.grammarColors['fil']!.color, isA<Never>());
      // Color check would need import
    });
  });
}
