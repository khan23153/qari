import 'package:just_audio/just_audio.dart';
import 'package:flutter/foundation.dart';
import '../../core/constants/app_constants.dart';
import 'local_storage_service.dart';

/// Audio service wrapping just_audio for Quran ayah playback.
/// Supports speed control, reciter selection, and audio session management.
class AudioService {
  /// Maps the app's reciter keys (stored via LocalStorageService) to the
  /// folder name used by the everyayah.com audio CDN.
  static const Map<String, String> _reciterFolders = {
    'abdul_basit': 'Abdul_Basit_Murattal_192kbps',
    'sudais': 'Abdurrahmaan_As-Sudais_192kbps',
    'minshawi': 'Minshawy_Murattal_128kbps',
    'husary': 'Husary_128kbps',
    'afasy': 'Alafasy_128kbps',
  };

  /// Falls back to Al-Afasy if an unknown reciter key is selected.
  static String _folderFor(String reciter) =>
      _reciterFolders[reciter] ?? 'Alafasy_128kbps';
  final AudioPlayer _player = AudioPlayer();
  final LocalStorageService _storage = LocalStorageService();

  bool _isInitialized = false;
  String _currentReciter = 'abdul_basit';
  double _currentSpeed = AppConstants.defaultPlaybackSpeed;
  String? _currentUrl;
  bool _isSequential = false;

  AudioService() {
    _init();
  }

  Future<void> _init() async {
    if (_isInitialized) return;
    try {
      _currentReciter = await _storage.getSelectedQari();
      _isInitialized = true;
    } catch (e) {
      debugPrint('AudioService init error: $e');
    }
  }

  AudioPlayer get player => _player;

  /// Builds the audio URL for a given surah and ayah.
  String buildAyahUrl({
    required int surahNumber,
    required int ayahNumber,
    String? reciter,
  }) {
    final folder = _folderFor(reciter ?? _currentReciter);
    final paddedSurah = surahNumber.toString().padLeft(3, '0');
    final paddedAyah = ayahNumber.toString().padLeft(3, '0');
    return '${AppConstants.audioCdnUrl}/$folder/$paddedSurah$paddedAyah.mp3';
  }

  /// Builds the audio URL for a full surah.
  String buildSurahUrl({
    required int surahNumber,
    String? reciter,
  }) {
    final folder = _folderFor(reciter ?? _currentReciter);
    final paddedSurah = surahNumber.toString().padLeft(3, '0');
    return '${AppConstants.audioCdnUrl}/$folder/$paddedSurah.mp3';
  }

  /// Plays a sequence of ayah URLs as one continuous, gapless track — i.e. the
  /// whole surah played in a single tap instead of one ayah at a time.
  ///
  /// [urls] is the ordered list of per-ayah audio URLs (e.g. the remaining
  /// ayahs of a surah). [initialIndex] lets playback start partway through the
  /// list (defaults to 0).
  Future<void> playSurahSequence({
    required List<String> urls,
    int initialIndex = 0,
  }) async {
    if (urls.isEmpty) return;
    debugPrint('AudioService: playing surah sequence (${urls.length} ayahs, '
        'start @ $initialIndex)');
    try {
      final sources = urls
          .map((u) => AudioSource.uri(Uri.parse(u)))
          .toList(growable: false);
      final concat = ConcatenatingAudioSource(children: sources);
      await _player.setAudioSource(concat, initialIndex: initialIndex);
      await _player.setSpeed(_currentSpeed);
      await _player.play();
      _isSequential = true;
      _currentUrl = null;
    } catch (e) {
      debugPrint('AudioService playSurahSequence error: $e');
      rethrow;
    }
  }

  /// Stream of the index of the currently playing item within a sequential
  /// (whole-surah) queue. Emits null when not playing a sequence.
  Stream<int?> get currentIndexStream =>
      _player.sequenceStateStream.map((s) => s?.currentIndex);

  /// Whether a whole-surah sequence is currently loaded.
  bool get isSequential => _isSequential;

  /// Plays a single ayah audio.
  Future<void> playAyah({
    required int surahNumber,
    required int ayahNumber,
    String? reciter,
  }) async {
    final url = buildAyahUrl(
      surahNumber: surahNumber,
      ayahNumber: ayahNumber,
      reciter: reciter,
    );
    await _playUrl(url);
  }

  /// Plays audio from a URL.
  Future<void> playUrl(String url) async {
    await _playUrl(url);
  }

  Future<void> _playUrl(String url) async {
    debugPrint('AudioService: playing url -> $url');
    try {
      if (_currentUrl == url && _player.playing) {
        await _player.pause();
        return;
      }
      await _player.setAudioSource(AudioSource.uri(Uri.parse(url)));
      await _player.setSpeed(_currentSpeed);
      await _player.play();
      _currentUrl = url;
      _isSequential = false;
    } catch (e) {
      debugPrint('AudioService play error: $e');
      rethrow;
    }
  }

  /// Pauses playback.
  Future<void> pause() async {
    await _player.pause();
  }

  /// Resumes playback.
  Future<void> resume() async {
    await _player.play();
  }

  /// Stops playback and releases resources.
  Future<void> stop() async {
    await _player.stop();
    _currentUrl = null;
    _isSequential = false;
  }

  /// Seeks to a position in the audio.
  Future<void> seek(Duration position) async {
    await _player.seek(position);
  }

  /// Sets the playback speed.
  Future<void> setSpeed(double speed) async {
    _currentSpeed = speed;
    await _player.setSpeed(speed);
  }

  /// Gets the current playback speed.
  double get currentSpeed => _currentSpeed;

  /// Sets the reciter.
  Future<void> setReciter(String reciter) async {
    _currentReciter = reciter;
    await _storage.setSelectedQari(reciter);
  }

  /// Gets the current reciter.
  String get currentReciter => _currentReciter;

  /// Whether audio is currently playing.
  bool get isPlaying => _player.playing;

  /// Current playback position.
  Stream<Duration> get positionStream => _player.positionStream;

  /// Total duration of the current audio.
  Stream<Duration?> get durationStream => _player.durationStream;

  /// Player state stream.
  Stream<PlayerState> get playerStateStream => _player.playerStateStream;

  /// Disposes the audio player.
  void dispose() {
    _player.dispose();
  }
}
