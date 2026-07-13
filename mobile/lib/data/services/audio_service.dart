import 'package:just_audio/just_audio.dart';
import 'package:flutter/foundation.dart';
import '../../core/constants/app_constants.dart';
import 'local_storage_service.dart';

/// Audio service wrapping just_audio for Quran ayah playback.
/// Supports speed control, reciter selection, and audio session management.
class AudioService {
  final AudioPlayer _player = AudioPlayer();
  final LocalStorageService _storage = LocalStorageService();

  bool _isInitialized = false;
  String _currentReciter = 'abdul_basit';
  double _currentSpeed = AppConstants.defaultPlaybackSpeed;
  String? _currentUrl;

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
    final r = reciter ?? _currentReciter;
    final paddedSurah = surahNumber.toString().padLeft(3, '0');
    final paddedAyah = ayahNumber.toString().padLeft(3, '0');
    return '${AppConstants.audioCdnUrl}/ayah/$r/$paddedSurah$paddedAyah.mp3';
  }

  /// Builds the audio URL for a full surah.
  String buildSurahUrl({
    required int surahNumber,
    String? reciter,
  }) {
    final r = reciter ?? _currentReciter;
    final paddedSurah = surahNumber.toString().padLeft(3, '0');
    return '${AppConstants.audioCdnUrl}/surah/$r/$paddedSurah.mp3';
  }

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
