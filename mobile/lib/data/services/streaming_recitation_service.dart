import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:audio_session/audio_session.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../core/constants/app_constants.dart';
import '../models/recitation_stream_event.dart';

/// Native side-channel to the `MicForegroundService` (microphone-typed Android
/// foreground service). Starting it is what makes the OS grant capture focus on
/// Android 14+; it is non-fatal if it fails (capture is still attempted).
const MethodChannel _micForegroundChannel =
    MethodChannel('com.qari.app/mic_foreground');

/// PCM16 audio frames captured natively inside the foreground service.
const EventChannel _micStreamChannel = EventChannel('com.qari.app/mic_stream');

/// Status / error text from the native capture (e.g. "capture started:
/// rate=16000", "capture error: ..."), surfaced live in the diag line.
const EventChannel _micStatusChannel = EventChannel('com.qari.app/mic_status');

/// Connection state of a live recitation streaming session.
enum LiveConnectionState { idle, connecting, listening, finishing, closed, error }

/// Streams microphone audio continuously to the backend `/ws/recitation/stream`
/// WebSocket and surfaces real-time word-by-word match events.
///
/// This powers the upgraded AI Recitation section (real-time tracking +
/// Memorization Mode). It is completely separate from [RecordingService]
/// (single-file record → upload), so the Quran reader's per-ayah "Recite" flow
/// is unaffected.
class StreamingRecitationService {
  WebSocket? _socket;
  StreamSubscription<dynamic>? _audioSub;
  StreamSubscription? _socketSub;
  /// Subscription to the native mic *status* channel (capture started / errors),
  /// surfaced live in the diag line so a swallowed native failure is visible.
  StreamSubscription? _statusSub;
  Timer? _pingTimer;

  /// Android audio session (via `audio_session`) activated before capture to
  /// request focus + speech attributes — helps the OS route the mic on devices
  /// that otherwise deliver silence despite the app permission being granted.
  AudioSession? _audioSession;

  /// Whether Android granted audio focus when we activated the session.
  /// `null` until activation finishes; `false` means the OS denied focus — a
  /// strong signal that another app holds the mic (or the OS is suppressing
  /// capture), which produces exactly the silent 0-frame stream behind
  /// "mic chunks: 0 · bytes sent: 0". Surfaced live in the diag line so a
  /// focus denial is visible immediately instead of being guessed at.
  bool? _audioFocusGranted;

  /// Latest native capture status string (e.g. "capture started: rate=16000",
  /// "capture error: ..."). Surfaced live in the diag line.
  String? _nativeStatus;

  /// Buffered PCM16 audio that is flushed to the socket on a fixed cadence
  /// (see [_flushInterval]) so each WS message carries a real, non-empty chunk
  /// (fixes the earlier "0s duration" payload bug and avoids chatty micro-frames).
  final BytesBuilder _audioBuffer = BytesBuilder();
  Timer? _flushTimer;
  // Buffered PCM16 is flushed to the socket every 250ms so each WS frame
  // carries a real, non-empty audio window (fixes the earlier "0s duration"
  // payload bug and keeps the ASR fed continuously).
  static const Duration _flushInterval = Duration(milliseconds: 250);

  final StreamController<RecitationStreamEvent> _events =
      StreamController<RecitationStreamEvent>.broadcast();
  final StreamController<double> _amplitude =
      StreamController<double>.broadcast();
  final StreamController<LiveConnectionState> _connection =
      StreamController<LiveConnectionState>.broadcast();

  Completer<RecitationStreamEvent?>? _finalCompleter;
  LiveConnectionState _state = LiveConnectionState.idle;

  /// Total PCM bytes sent to the server (for debugging the "Duration: 0s" bug).
  int _totalSentBytes = 0;
  int _chunkCount = 0;
  DateTime? _firstChunkAt;

  /// Real-time backend events (ready / word / final / error).
  Stream<RecitationStreamEvent> get events => _events.stream;

  /// Normalized (0–1) mic loudness per audio chunk for the live visualizer.
  Stream<double> get amplitude => _amplitude.stream;

  /// Connection lifecycle updates.
  Stream<LiveConnectionState> get connectionState => _connection.stream;

  LiveConnectionState get state => _state;
  bool get isActive =>
      _state == LiveConnectionState.listening ||
      _state == LiveConnectionState.connecting;

  /// Total PCM bytes sent to the server so far (0 ⇒ no mic audio captured /
  /// no binary frames delivered → "Duration: 0s"). Exposed for live diagnostics.
  int get sentBytes => _totalSentBytes;

  /// Number of microphone chunks received from the recorder (0 ⇒ the recorder
  /// is producing no data → OS blocked capture despite the permission).
  int get micChunks => _chunkCount;

  /// Last native recorder error (if any). Surfaced live in the diag line.
  String? _micError;
  String? get micError => _micError;

  /// On-screen diagnostics for the native→Dart audio delivery, so we can debug
  /// the "mic chunks: 0" case without `flutter logs` (useful on a phone with no
  /// dev machine). Counts how many native audio frames actually reached the Dart
  /// `onData` callback (vs `_chunkCount`, which counts successfully processed).
  int _audioOnDataCount = 0;
  int get audioOnDataCount => _audioOnDataCount;
  String? _lastFrameType;
  String? get lastFrameType => _lastFrameType;
  /// Last raw (pre-parse) event type Tarteel sent — surfaced in the diag so a
  /// rejected/empty auth shows up as `lastRx: <event>` (or `lastRx: <none>`).
  String? _tarteelLastRx;
  String? get tarteelLastRx => _tarteelLastRx;
  /// Full raw payload of the last Tarteel ERROR/unknown frame — surfaced in the
  /// diag so the user can paste Tarteel's actual rejection reason without us
  /// needing the (often-failing) VPS echo round-trip.
  String? _tarteelLastError;
  String? get tarteelLastError => _tarteelLastError;
  String? _audioOnDataError;
  String? get audioOnDataError => _audioOnDataError;

  /// Effective sample rate of the audio we SEND to the server (after the native
  /// 44.1kHz capture is software-resampled to 16kHz). Always 16000 for the live
  /// stream — surfaced in the diag as `sentRate` so the user isn't confused by
  /// the native `rate=44100` capture reading.
  static const int sentSampleRate = 16000;

  /// Result of the Android audio-focus request (via `audio_session`). `null`
  /// until the session is activated; `false` means the OS denied focus, which
  /// on many ROMs yields a silently-dead recorder (0 chunks, 0 errors) — the
  /// exact symptom behind "mic chunks: 0 · bytes sent: 0".
  bool? get audioFocusGranted => _audioFocusGranted;

  /// Latest native capture status (e.g. "capture started: rate=16000",
  /// "capture error: ..."). Surfaced live in the diag line.
  String? get nativeStatus => _nativeStatus;

  void _setState(LiveConnectionState s) {
    _state = s;
    if (!_connection.isClosed) _connection.add(s);
  }

  Future<bool> hasPermission() async {
    final status = await Permission.microphone.status;
    return status.isGranted;
  }

  Future<bool> requestPermission() async {
    final status = await Permission.microphone.request();
    return status.isGranted;
  }

  /// Opens the WebSocket, sends the `start` handshake, and begins streaming
  /// microphone audio. Throws on permission denial or connection failure.
  ///
  /// [ayahRefs] is the explicit ordered list of `(surah, ayah)` the user will
  /// recite continuously (a full Mushaf page or a whole surah). When omitted we
  /// fall back to a single-surah range built from [surahNumber]/[ayahNumber].
  Future<void> start({
    required int surahNumber,
    required int ayahNumber,
    int? ayahFrom,
    int? ayahTo,
    List<(int, int)>? ayahRefs,
    required bool memorizationMode,
    List<String>? words,
  }) async {
    if (isActive) return;
    _setState(LiveConnectionState.connecting);
    _totalSentBytes = 0;
    _chunkCount = 0;
    _audioOnDataCount = 0;
    _lastFrameType = null;
    _audioOnDataError = null;
    _tarteelLastRx = null;
    _tarteelLastError = null;
    _micError = null;
    _audioFocusGranted = null;
    _firstChunkAt = null;

    if (!await hasPermission()) {
      final granted = await requestPermission();
      if (!granted) {
        _setState(LiveConnectionState.error);
        throw const MicPermissionDeniedException();
      }
    }
    _audioSession?.setActive(false).catchError((_) => false);
    _audioSession = null;

    // --- Connect the WebSocket (trust the VPS self-signed cert) ---
    final useTarteel = AppConstants.useTarteelLiveApi;
    final wsUrl = useTarteel
        ? AppConstants.tarteelLiveWsUrl
        : AppConstants.recitationStreamWsUrl;
    // Tarteel runs behind Cloudflare with a valid CA, so we don't need the
    // self-signed bypass there — but the same permissive client is harmless.
    final httpClient = HttpClient()
      ..badCertificateCallback =
          (cert, host, port) => host == AppConstants.trustedSelfSignedHost;
    try {
      debugPrint('[Streaming] connecting to $wsUrl '
          '(tarteel=$useTarteel)');
      _socket = await WebSocket.connect(
        wsUrl,
        customClient: httpClient,
      ).timeout(const Duration(seconds: 15), onTimeout: () {
        throw StreamingConnectionException('WebSocket connect timed out');
      });
    } catch (e) {
      _setState(LiveConnectionState.error);
      debugPrint('[Streaming] WS CONNECT FAILED: $e');
      throw StreamingConnectionException('Could not connect: $e');
    }

    _socketSub = _socket!.listen(
      _onSocketData,
      onError: (Object e, StackTrace? st) {
        // A WebSocket-level error (handshake failure, 400/500, dropped
        // connection). Surface it loudly so "Duration 0s" can be diagnosed.
        debugPrint('[Streaming] WS ERROR: $e');
        if (st != null) debugPrint('$st');
        _setState(LiveConnectionState.error);
      },
      onDone: () {
        debugPrint('[Streaming] WS CLOSED (done). state=${_state.name}');
        if (AppConstants.useTarteelLiveApi) {
          _tarteelLastRx = 'WS_CLOSED';
        }
        if (_state != LiveConnectionState.finishing) {
          _setState(LiveConnectionState.closed);
        }
      },
      cancelOnError: false,
    );

    // --- Handshake ---
    // Send the explicit ordered ayah sequence so the backend can resolve the
    // concatenated reference list and track words seamlessly across ayah
    // boundaries (full-page / full-surah continuous recitation). Also send the
    // client's resolved word list as a fallback reference so the backend can
    // still score when its own reference store is empty (prevents "0 of 0").
    final List<List<int>> refs = ayahRefs == null
        ? []
        : ayahRefs.map((r) => [r.$1, r.$2]).toList();
    if (useTarteel) {
      await _appVersion();
      _sendTarteelHandshake(surahNumber, ayahNumber, words);
    } else {
      _socket!.add(jsonEncode({
        'type': 'start',
        'surah_number': surahNumber,
        'ayah_number': ayahNumber,
        'ayah_from': ayahFrom ?? ayahNumber,
        'ayah_to': ayahTo ?? ayahNumber,
        if (refs.isNotEmpty) 'ayahs': refs,
        if (words != null && words.isNotEmpty) 'words': words,
        'mode': memorizationMode ? 'memorization' : 'tracking',
        'sample_rate': AppConstants.liveRecitationSampleRate,
      }));
    }
    debugPrint('[Streaming] sent start handshake '
        '(surah=$surahNumber, ayah=$ayahNumber, refs=${refs.length}, '
        'clientWords=${(words?.length) ?? 0})');

    // --- Start the continuous PCM audio stream (native, inside the mic
    // foreground service). The `record` plugin opens AudioRecord on the Flutter
    // engine thread, outside the foreground-service capture context, so on
    // Android 14+ it can be granted focus yet receive 0 frames. Capturing
    // natively inside the service is the sanctioned fix.
    await _activateAudioSession();
    // Subscribe to the native mic stream BEFORE starting the foreground service
    // so the Flutter EventChannel listener is attached and `audioSink` is set on
    // the native side *before* the service begins producing + flushing frames.
    // Otherwise the first frames are flushed into a null sink and (previously)
    // dropped → "mic chunks: 0 · bytes sent: 0".
    try {
      _subscribeNativeMic();
      debugPrint('[Streaming] native mic stream SUBSCRIBED.');
    } on MicPermissionDeniedException {
      rethrow;
    } catch (e, st) {
      _micError = e.toString();
      debugPrint('[Streaming] native mic subscribe FAILED: $e\n$st');
      _setState(LiveConnectionState.error);
      throw StreamingConnectionException('Mic could not start: $e');
    }
    // Start the microphone foreground service so the OS grants capture focus on
    // Android 14+ (fixes the "mic chunks: 0 / focus: NO" silent-capture case).
    await _startForegroundMicService();

    // --- Keep-alive pings so long hands-free sessions never drop ---
    _pingTimer = Timer.periodic(
      const Duration(seconds: AppConstants.liveRecitationPingIntervalSeconds),
      (_) {
        final sock = _socket;
        if (sock != null && sock.readyState == WebSocket.open) {
          sock.add(jsonEncode({'type': 'ping'}));
        }
      },
    );

    // --- Chunked upload: emit buffered audio every 250ms ---
    _flushTimer = Timer.periodic(_flushInterval, (_) {
      _flushAudio();
    });

    _setState(LiveConnectionState.listening);
    debugPrint('StreamingRecitation: streaming started (sentBytes tracked)');
  }

  /// Starts the native microphone foreground service (Android 14+). Non-fatal:
  /// if it fails we still try to record — but without it the OS denies capture
  /// focus (the "mic chunks: 0 / focus: NO" failure).
  Future<void> _startForegroundMicService() async {
    try {
      await _micForegroundChannel.invokeMethod<void>('start');
      debugPrint('[Streaming] mic foreground service started.');
    } catch (e) {
      debugPrint('[Streaming] mic foreground service start failed (non-fatal): $e');
    }
  }

  /// Stops the native microphone foreground service.
  Future<void> _stopForegroundMicService() async {
    try {
      await _micForegroundChannel.invokeMethod<void>('stop');
      debugPrint('[Streaming] mic foreground service stopped.');
    } catch (e) {
      debugPrint('[Streaming] mic foreground service stop failed (non-fatal): $e');
    }
  }

  /// Sends the Tarteel live-voice handshake. Captured + verified schema (the
  /// client→Tarteel START_STREAM frame):
  ///   {"type":"START_STREAM","data":{ audioConfig, authToken, deviceId,
  ///    devicePlatform, recitationMode:"FOLLOW_ALONG", isMemorization,
  ///    isDiacritized, shouldCollectAudio, ... }}
  /// `type` is a STRING (not an int). The DRF token goes in `data.authToken`.
  /// Audio frames → `{"type":3,"data":"<base64 PCM16>"}` (verified).
  /// Server replies → `{"type":2,"text":"{...}"}` (PARTIAL_TRANSCRIPT /
  ///   STATES_UPDATE events).
  /// The reference word list is NOT sent to Tarteel (it tracks against its own
  /// internal mushaf); we keep our local [_words] for the results grid.
  static String? _cachedAppVersion;
  static Future<String> _appVersion() async {
    if (_cachedAppVersion != null) return _cachedAppVersion!;
    try {
      final info = await PackageInfo.fromPlatform();
      _cachedAppVersion = '${info.version}+${info.buildNumber}';
    } catch (_) {
      _cachedAppVersion = '1.0.45';
    }
    return _cachedAppVersion!;
  }

  void _sendTarteelHandshake(
    int surahNumber,
    int ayahNumber,
    List<String>? words,
  ) {
    final token = AppConstants.tarteelLiveToken;
    // Tarteel's protocol uses integer `type` codes (audio frame is `type:3`),
    // so the init/config frame is `type:1`. Send it as such (with the config
    // under `data`) so the server registers the session before audio arrives.
    final startFrame = {
      'type': 1,
      'event': 'START_STREAM',
      'data': {
        'appVersion': _cachedAppVersion ?? '1.0.45',
        'audioConfig': {
          'fileFormat': 'WAV',
          'channels': 1,
          'sampleRate': AppConstants.liveRecitationSampleRate,
          'modelName': null,
          'languageCode': 'ar-BH',
          'enableInterimResults': true,
          'enableWordTimeOffsets': true,
          'maxAlternatives': 1,
        },
        if (token.isNotEmpty) 'authToken': token,
        'deviceId': 'qari-app',
        'devicePlatform': 'android',
        'isMemorization': false,
        'isDiacritized': true,
        'isDualModel': false,
        'isInitialTargetRangeStrict': false,
        'isNewSttServer': true,
        'isStartPositionStrict': null,
        'startPosition': null,
        'endPosition': null,
        'recitationMode': 'FOLLOW_ALONG',
        'isEphemeral': null,
        'shouldCollectAudio': true,
        'shouldLabelAudio': true,
        'userId': null,
        'sessionGroupId': null,
      },
    };
    _socket!.add(jsonEncode(startFrame));
    debugPrint('[Streaming] sent Tarteel START_STREAM '
        '(surah=$surahNumber, ayah=$ayahNumber, '
        'authToken=${token.isNotEmpty ? 'set' : 'empty'})');
  }

  /// Requests Android audio focus + configures a speech/record audio session so

  /// Requests Android audio focus + configures a speech/record audio session so
  /// the OS routes the mic to this app. Non-fatal: if it fails we still try to
  /// record (some devices don't need it; a failure here is not the capture bug).
  Future<void> _activateAudioSession() async {
    try {
      final session = await AudioSession.instance;
      await session.configure(const AudioSessionConfiguration(
        androidAudioFocusGainType: AndroidAudioFocusGainType.gain,
        androidAudioAttributes: AndroidAudioAttributes(
          contentType: AndroidAudioContentType.speech,
          usage: AndroidAudioUsage.voiceCommunication,
        ),
        androidWillPauseWhenDucked: false,
      ));
      // `setActive` returns whether the OS actually granted focus. A `false`
      // here (or a throw) means the mic is contended/blocked — capture it so
      // the UI can show "focus: NO" instead of a bare 0-chunk stream.
      final granted = await session.setActive(true);
      _audioFocusGranted = granted;
      _audioSession = session;
      debugPrint('[Streaming] audio session activated '
          '(focus granted: $granted).');
    } catch (e) {
      _audioFocusGranted = false;
      debugPrint('[Streaming] audio session activate failed (non-fatal): $e');
    }
  }

  /// Subscribes to the native mic PCM stream + status channel. The status
  /// channel fires first ("capture started: rate=…" / "capture error: …") so a
  /// silently-dead capture is visible immediately instead of a bare "0 bytes".
  void _subscribeNativeMic() {
    _statusSub?.cancel();
    _statusSub = _micStatusChannel.receiveBroadcastStream().listen(
      (dynamic msg) {
        final s = msg is String ? msg : msg?.toString();
        if (s != null) {
          _nativeStatus = s;
          debugPrint('[Streaming] native mic status: $s');
          if (s.toLowerCase().contains('error')) _micError = s;
        }
      },
      onError: (Object e, StackTrace? st) {
        _micError = e.toString();
        debugPrint('[Streaming] native mic STATUS ERROR: $e');
        if (st != null) debugPrint('$st');
      },
      cancelOnError: false,
    );

    _audioSub = _micStreamChannel.receiveBroadcastStream().listen(
      (dynamic chunk) {
        _audioOnDataCount++;
        _lastFrameType = chunk.runtimeType.toString();
        try {
          debugPrint('[Streaming] native audio onData type=${chunk.runtimeType} '
              'len=${chunk is List ? chunk.length : 'n/a'}');
          Uint8List bytes;
          if (chunk is Uint8List) {
            bytes = chunk;
          } else if (chunk is List<int>) {
            bytes = Uint8List.fromList(chunk);
          } else {
            debugPrint('[Streaming] native audio UNKNOWN type, ignoring');
            return;
          }
          _onNativeAudio(bytes);
        } catch (e, st) {
          _audioOnDataError = e.toString();
          debugPrint('[Streaming] native audio onData ERROR: $e\n$st');
        }
      },
      onError: (Object e, StackTrace? st) {
        _micError = e.toString();
        debugPrint('[Streaming] native mic STREAM ERROR: $e');
        if (st != null) debugPrint('$st');
      },
      cancelOnError: false,
    );
  }

  /// Forwards a native PCM16 frame to the live visualizer + upload buffer.
  void _onNativeAudio(Uint8List chunk) {
    // Count + buffer the frame FIRST, before any amplitude math, so a failure in
    // RMS computation can never suppress chunk counting / server upload (that
    // was the "mic chunks: 0 · bytes sent: 0" despite 500+ frames arriving).
    _chunkCount++;
    _firstChunkAt ??= DateTime.now();
    if (chunk.isNotEmpty) {
      _audioBuffer.add(chunk);
    }
    if (_chunkCount <= 5 || _chunkCount % 50 == 0) {
      debugPrint('[Streaming] mic chunk #$_chunkCount '
          'len=${chunk.length} bytes (buffered=${_audioBuffer.length})');
    }
    try {
      _emitAmplitude(chunk);
    } catch (e, st) {
      _audioOnDataError = e.toString();
      debugPrint('[Streaming] _emitAmplitude ERROR (chunk len=${chunk.length}): '
          '$e\n$st');
    }
  }

  /// Wraps raw 16-bit PCM mono samples in a minimal WAV container. Tarteel's
  /// START_STREAM `audioConfig.fileFormat` is "WAV", so it expects WAV bytes
  /// (not bare PCM16) in the audio frames.
  static Uint8List _wrapWav(Uint8List pcm16, int sampleRate) {
    final numChannels = 1;
    final bytesPerSample = 2;
    final byteRate = sampleRate * numChannels * bytesPerSample;
    final blockAlign = numChannels * bytesPerSample;
    final dataLen = pcm16.length;
    final header = ByteData(44);
    final ascii = const AsciiCodec();
    header.setUint32(0, 0x52494646, Endian.big); // "RIFF"
    header.setUint32(4, 36 + dataLen, Endian.little);
    header.setUint32(8, 0x57415645, Endian.big); // "WAVE"
    header.setUint32(12, 0x666d7420, Endian.big); // "fmt "
    header.setUint32(16, 16, Endian.little); // PCM fmt chunk size
    header.setUint16(20, 1, Endian.little); // PCM
    header.setUint16(22, numChannels, Endian.little);
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, byteRate, Endian.little);
    header.setUint16(32, blockAlign, Endian.little);
    header.setUint16(34, 16, Endian.little); // bits/sample
    header.setUint32(36, 0x64617461, Endian.big); // "data"
    header.setUint32(40, dataLen, Endian.little);
    final out = BytesBuilder(copy: false);
    out.add(header.buffer.asUint8List());
    out.add(pcm16);
    return out.toBytes();
  }

  /// Sends any buffered PCM16 audio to the server as a single binary frame.
  /// Flushing on a fixed cadence (not per raw microphone chunk) guarantees the
  /// server receives non-empty, real-duration windows.
  void _flushAudio() {
    if (_audioBuffer.isEmpty) return;
    final sock = _socket;
    if (sock != null && sock.readyState == WebSocket.open) {
      final frame = Uint8List.fromList(_audioBuffer.takeBytes());
      _totalSentBytes += frame.length;
      if (AppConstants.useTarteelLiveApi) {
        // Tarteel expects audio frames as a JSON envelope, NOT raw binary.
        // Its server rejects raw bytes with:
        //   "The message sent is not valid, please format it using
        //    {event: [eventName], data: [data]}"
        // The wire shape (captured) is {"type":3,"data":"<base64 WAV>"}.
        final wav = _wrapWav(frame, AppConstants.liveRecitationSampleRate);
        final b64 = base64Encode(wav);
        sock.add(jsonEncode({'type': 3, 'data': b64}));
        _totalSentBytes += wav.length;
        debugPrint('[Tarteel] FLUSH #$_chunkCount -> sent audio frame '
            '(wav=${wav.length} b64=${b64.length}, totalSent=$_totalSentBytes)');
      } else {
        sock.add(frame);
        debugPrint('[Streaming] FLUSH #$_chunkCount -> sent ${frame.length} bytes '
            '(totalSent=$_totalSentBytes)');
      }
    } else {
      debugPrint('[Streaming] FLUSH skipped: socket not open '
          '(state=${_state.name}, buffered=${_audioBuffer.length})');
      _audioBuffer.clear();
    }
  }

  /// Fire-and-forget echo of a raw Tarteel frame to our VPS debug endpoint so
  /// we can read the (encrypted) protocol from the server logs. Never blocks or
  /// throws into the caller. No-op unless we're on the Tarteel live path.
  /// Uses a self-signed-cert-bypassing HttpClient for our VPS host (the plain
  /// `http` client would reject the self-signed TLS and the echo would fail
  /// silently — which is why no frames ever reached the server logs).
  final HttpClient _echoHttpClient = HttpClient()
    ..badCertificateCallback =
        (cert, host, port) => host == AppConstants.trustedSelfSignedHost;

  void _echoTarteelFrame(dynamic frame) {
    if (!AppConstants.useTarteelLiveApi) return;
    final url = AppConstants.tarteelDebugEchoUrl;
    if (url.isEmpty) return;
    unawaited(() async {
      try {
        final uri = Uri.parse(url);
        final req = await _echoHttpClient.postUrl(uri)
          ..headers.contentType = frame is String
              ? ContentType.json
              : ContentType.binary;
        if (frame is String) {
          req.write(frame);
        } else {
          final bytes = frame is Uint8List ? frame : Uint8List.fromList(frame as List<int>);
          req.add(bytes);
        }
        await req.close();
      } catch (e) {
        debugPrint('[Tarteel] echo failed (non-fatal): $e');
      }
    }());
  }

  void _onSocketData(dynamic data) {
    if (AppConstants.useTarteelLiveApi) {
      // Store the RAW frame preview (event name + a snippet of the payload) so
      // the diag can surface Tarteel's actual rejection reason on-screen without
      // relying on the VPS echo round-trip (which is failing in the field).
      if (data is String) {
        try {
          final j = jsonDecode(data) as Map<String, dynamic>;
          final ev = j['event']?.toString() ?? j['type']?.toString() ?? 'json';
          final snippet = data.length > 200 ? data.substring(0, 200) : data;
          _tarteelLastRx = '$ev · $snippet';
        } catch (_) {
          _tarteelLastRx = 'text(${data.length}): ${data.length > 120 ? data.substring(0, 120) : data}';
        }
      } else {
        final len = data is Uint8List ? data.length : (data as List).length;
        _tarteelLastRx = 'bin($len)';
      }
    }
    if (data is! String) {
      // Tarteel's voice API sends encrypted/proprietary frames (we captured
      // `uWebSockets v20` but the payloads are not plain JSON). Echo the raw
      // bytes to our VPS debug endpoint so we can reverse-engineer the protocol
      // from the server logs (no need to pull logs off the phone). For our own
      // backend this branch is unexpected and safely ignored.
      if (AppConstants.useTarteelLiveApi) {
        final bytes = data is Uint8List ? data : Uint8List.fromList(data as List<int>);
        debugPrint('[Tarteel] RX binary frame (${bytes.length} bytes): '
            '${bytes.length > 64 ? bytes.sublist(0, 64) : bytes}');
        _echoTarteelFrame(bytes);
      } else {
        debugPrint('[Streaming] received non-string frame (ignored).');
      }
      return;
    }
    try {
      final json = jsonDecode(data) as Map<String, dynamic>;
      if (AppConstants.useTarteelLiveApi) _echoTarteelFrame(data);
      // Capture Tarteel's rejection reason directly so it can be shown in the
      // diag without relying on the (often-failing) VPS echo round-trip.
      final ev = json['event']?.toString() ?? json['type']?.toString();
      if (AppConstants.useTarteelLiveApi &&
          (ev == 'ERROR' || ev == 'error' || ev == 'UNKNOWN' || ev == 'FATAL' || ev == null)) {
        _tarteelLastError = data.length > 300 ? data.substring(0, 300) : data;
        debugPrint('[Tarteel] RX error/unknown frame: $_tarteelLastError');
      }
      final events = AppConstants.useTarteelLiveApi
          ? RecitationStreamEvent.fromTarteelJson(json)
          : [RecitationStreamEvent.fromJson(json)];
      for (final event in events) {
      if (event.type == RecitationStreamEventType.word) {
        debugPrint('[Streaming] RX word event idx=${event.wordIndex} '
            'status=${event.status.name} expected=${event.expected}');
      } else if (event.type == RecitationStreamEventType.ready) {
        debugPrint('[Streaming] RX ready (${event.words.length} words)');
      } else if (event.type == RecitationStreamEventType.finalResult) {
        debugPrint('[Streaming] RX final (duration=${event.result?.durationSeconds}s, '
            'verdicts=${event.result?.wordVerdicts.length})');
      } else if (event.type == RecitationStreamEventType.error) {
        debugPrint('[Streaming] RX ERROR: ${event.detail}');
      }
      if (!_events.isClosed) _events.add(event);
      if (event.type == RecitationStreamEventType.finalResult) {
        _finalCompleter?.complete(event);
        _finalCompleter = null;
      }
      }
    } catch (e) {
      debugPrint('[Streaming] decode error: $e');
    }
  }

  /// Computes an RMS loudness (0–1) from a PCM16 little-endian chunk.
  void _emitAmplitude(Uint8List chunk) {
    if (chunk.length < 2) return;
    // The incoming `Uint8List` is often a VIEW (`_Uint8ArrayView`) with an odd
    // `offsetInBytes` into a larger buffer. `buffer.asInt16List(offset, n)`
    // throws RangeError when `offset` is not a multiple of 2 — and that throw
    // happened here on every frame, skipping `_chunkCount++` and leaving the
    // whole session at "mic chunks: 0 · bytes sent: 0" despite 500+ native
    // frames arriving (onData: N). Read the samples manually via byte indexing
    // so alignment can never throw.
    final sampleCount = chunk.length ~/ 2; // drop a trailing odd byte
    if (sampleCount == 0) return;
    var sumSq = 0.0;
    for (var i = 0; i < sampleCount; i++) {
      final lo = chunk[i * 2];
      final hi = chunk[i * 2 + 1];
      // little-endian 16-bit signed
      final s = (hi << 8) | lo;
      final v = (s >= 0x8000 ? s - 0x10000 : s) / 32768.0;
      sumSq += v * v;
    }
    final rms = math.sqrt(sumSq / sampleCount);
    // Map RMS to a lively 0–1 range (recitation is fairly quiet at the mic).
    final normalized = (rms * 3.2).clamp(0.0, 1.0);
    if (!_amplitude.isClosed) _amplitude.add(normalized);
  }

  /// Stops recording, tells the backend to finalize, and awaits the final
  /// result (bounded by [timeout]). Returns the final result event if received.
  /// IMPORTANT: the caller must NOT navigate to results until this resolves —
  /// it blocks until the server sends the aggregated `final` payload.
  Future<RecitationStreamEvent?> stop({
    Duration timeout = const Duration(seconds: 30),
  }) async {
    if (_state == LiveConnectionState.idle ||
        _state == LiveConnectionState.closed) {
      debugPrint('[Streaming] stop() called but session not active '
          '(state=${_state.name}) — nothing to finalize.');
      return null;
    }
    _setState(LiveConnectionState.finishing);

    // Stop capturing audio first.
    await _audioSub?.cancel();
    _audioSub = null;
    await _statusSub?.cancel();
    _statusSub = null;
    _pingTimer?.cancel();
    _flushTimer?.cancel();
    _flushAudio(); // send any trailing audio before finalizing

    debugPrint('[Streaming] requesting finalize from server '
        '(totalSentBytes=$_totalSentBytes, micChunks=$_chunkCount)');

    _finalCompleter = Completer<RecitationStreamEvent?>();
    final sock = _socket;
    if (sock != null && sock.readyState == WebSocket.open) {
      sock.add(jsonEncode({'type': 'stop'}));
    } else {
      debugPrint('[Streaming] cannot send stop: socket not open '
          '(state=${_state.name})');
      _finalCompleter?.complete(null);
    }

    RecitationStreamEvent? finalEvent;
    try {
      if (AppConstants.useTarteelLiveApi) {
        // Tarteel's voice API does NOT emit a `final` event in our shape (and
        // ignores our `type:stop` frame), so blocking on it would hang the
        // "Finalizing" screen for the full [timeout]. Instead we resolve almost
        // immediately with null and let the page synthesize a result from the
        // words revealed live. A short grace period still lets any trailing
        // word events arrive.
        await Future.delayed(const Duration(milliseconds: 800));
        _finalCompleter?.complete(null);
        finalEvent = null;
      } else {
        finalEvent = await _finalCompleter!.future.timeout(timeout);
      }
    } on TimeoutException {
      debugPrint('[Streaming] TIMEOUT waiting for server final result '
          '(server did not respond in ${timeout.inSeconds}s).');
    } finally {
      _finalCompleter = null;
      await _closeSocket();
      _setState(LiveConnectionState.closed);
    }

    final r = finalEvent?.result;
    debugPrint('[Streaming] FINAL result received: '
        'duration=${r?.durationSeconds}s, '
        'verdicts=${r?.wordVerdicts.length}, '
        'score=${r?.overallScore}');
    return finalEvent;
  }

  /// Aborts the session without waiting for a final result.
  Future<void> cancel() async {
    _pingTimer?.cancel();
    _flushTimer?.cancel();
    _audioBuffer.clear();
    await _audioSub?.cancel();
    _audioSub = null;
    await _statusSub?.cancel();
    _statusSub = null;
    await _closeSocket();
    _setState(LiveConnectionState.closed);
  }

  /// Releases the Android audio focus / speech session acquired in
  /// [_activateAudioSession]. Best-effort and non-fatal.
  void _deactivateAudioSession() {
    final session = _audioSession;
    _audioSession = null;
    _audioFocusGranted = null;
    if (session != null) {
      session.setActive(false).catchError((_) => false);
    }
  }

  Future<void> _closeSocket() async {
    _flushTimer?.cancel();
    _pingTimer?.cancel();
    _deactivateAudioSession();
    await _stopForegroundMicService();
    await _audioSub?.cancel();
    _audioSub = null;
    await _statusSub?.cancel();
    _statusSub = null;
    await _socketSub?.cancel();
    _socketSub = null;
    try {
      await _socket?.close();
    } catch (_) {}
    _socket = null;
  }

  Future<void> dispose() async {
    await cancel();
    await _events.close();
    await _amplitude.close();
    await _connection.close();
  }
}

/// Thrown when microphone permission is denied.
class MicPermissionDeniedException implements Exception {
  const MicPermissionDeniedException();
  @override
  String toString() => 'Microphone permission denied';
}

/// Thrown when the streaming WebSocket cannot be established.
class StreamingConnectionException implements Exception {
  final String message;
  const StreamingConnectionException(this.message);
  @override
  String toString() => message;
}
