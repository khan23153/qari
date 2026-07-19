package com.qari.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.Process
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Microphone foreground service (type `microphone`).
 *
 * On Android 14+ the OS only reliably delivers mic *data* to an app that is
 * capturing from within an active, microphone-typed foreground service. The
 * `record` Flutter plugin opens its `AudioRecord` on the Flutter engine thread,
 * outside that context, so on affected devices it initialises fine and is even
 * granted audio focus yet receives 0 frames forever (the "mic chunks: 0 /
 * focus: yes" failure). Capturing natively *here*, inside the service, is the
 * sanctioned fix.
 *
 * Safety: NOTHING in this service may throw to the OS. Every native call is
 * wrapped so a failure is reported via the status [EventChannel] and the
 * service stops cleanly instead of crashing the app.
 */
class MicForegroundService : Service() {
    companion object {
        const val CHANNEL_ID = "qari_mic_capture"
        const val NOTIFICATION_ID = 8841
        const val TARGET_RATE = 16000
        const val FALLBACK_RATE = 44100

        fun start(context: Context) {
            try {
                val intent = Intent(context, MicForegroundService::class.java)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(intent)
                } else {
                    context.startService(intent)
                }
            } catch (e: Exception) {
                // Never crash the app from a failed start; surface it.
                MicStreamBridge.lastStatus = "start error: ${e.message}"
                MicStreamBridge.statusSink?.success(MicStreamBridge.lastStatus)
            }
        }

        fun stop(context: Context) {
            try {
                context.stopService(Intent(context, MicForegroundService::class.java))
            } catch (_: Exception) {
                // ignore
            }
        }
    }

    private var reader: AudioRecord? = null
    private var readThread: Thread? = null
    private var running = false
    /** Monotonic token for the current capture; bumped in stopCapture so the
     *  main-thread flush Runnable from a previous session stops re-posting. */
    private var captureToken = 0

    /** All EventChannel sink calls MUST run on the main thread. Calling a Flutter
     *  sink from a background thread is an uncatchable JNI crash on Android. */
    private val mainHandler = Handler(Looper.getMainLooper())

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        try {
            createChannel()
        } catch (e: Exception) {
            MicStreamBridge.lastStatus = "createChannel error: ${e.message}"
            MicStreamBridge.statusSink?.success(MicStreamBridge.lastStatus)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        try {
            // The notification channel MUST exist before startForeground(), and
            // the icon MUST be a valid monochrome drawable — otherwise the OS
            // throws BadNotificationException and instantly kills the app. On
            // Android 14+ the microphone type MUST be passed here (manifest
            // alone is not enough) or the OS terminates the app.
            createChannel()
            val notification = buildNotification()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(
                    NOTIFICATION_ID,
                    notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE,
                )
            } else {
                startForeground(NOTIFICATION_ID, notification)
            }
            startCapture()
        } catch (e: Exception) {
            // A throw here (e.g. SecurityException / IllegalStateException from
            // startForeground) would otherwise crash the whole app. Report it
            // and shut the service down gracefully instead.
            val msg = "foreground start error: ${e.javaClass.simpleName}: ${e.message}"
            MicStreamBridge.lastStatus = msg
            MicStreamBridge.statusSink?.success(msg)
            stopCapture()
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        stopCapture()
        try {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } catch (_: Exception) {
        }
        super.onDestroy()
    }

    private fun status(msg: String) {
        MicStreamBridge.lastStatus = msg
        // Route to the main thread — Flutter sinks must not be called from a
        // background thread (uncatchable JNI crash). Also guard against a
        // cancelled sink throwing (which would otherwise hard-crash the app).
        mainHandler.post {
            try {
                MicStreamBridge.statusSink?.success(msg)
            } catch (_: Exception) {
            }
        }
    }

    private fun startCapture() {
        try {
            val (rate, resample) = pickRate()
            val minBuf = AudioRecord.getMinBufferSize(
                rate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
            )
            if (minBuf <= 0) {
                status("capture error: getMinBufferSize invalid (rate=$rate)")
                return
            }
            val ar = buildAudioRecord(rate, minBuf * 2)
            if (ar == null) {
                status("capture error: AudioRecord not initialized (rate=$rate source=UNPROCESSED)")
                return
            }
            ar.startRecording()
            if (ar.recordingState != AudioRecord.RECORDSTATE_RECORDING) {
                ar.release()
                status("capture error: AudioRecord not recording (rate=$rate source=UNPROCESSED)")
                return
            }
            // Defensive: a stray OS/hal mute state can starve the mic. Ensure
            // unmuted before we begin (no-op on most devices, harmless).
            try {
                val am = getSystemService(Context.AUDIO_SERVICE) as android.media.AudioManager
                am.isMicrophoneMute = false
            } catch (_: Exception) {
            }
            reader = ar
            running = true
            status("capture started: rate=$rate resample=$resample source=UNPROCESSED")
            val shortBuf = ShortArray(minBuf / 2)
            val resampler = if (resample) LinearResampler(rate, TARGET_RATE) else null
            var zeroTicks = 0
            var dataTicks = 0
            var audioPosted = 0
            var lastDiagAt = System.currentTimeMillis()
            // Drain the native read loop into an in-service buffer and flush to the
            // Flutter audio sink on the MAIN thread on a timer. Posting one
            // `success()` per read tick from a tight background loop overwhelmed
            // the main-thread Handler and the binary frames were silently dropped
            // (status text survived because it's far less frequent). Buffering +
            // one flush per ~50ms keeps delivery reliable while still streaming.
            // Buffered PCM frames waiting to be delivered to the Flutter audio
            // sink. CRITICAL: if `audioSink` is not attached yet when we flush,
            // the OLD code discarded (cleared) the buffer → every frame produced
            // during the start/sink race was lost, yielding "mic chunks: 0 ·
            // bytes sent: 0" even though native capture was healthy. We now KEEP
            // buffering until the sink attaches (capped to avoid OOM), then flush
            // immediately via onAudioSinkAttached.
            val outBuf = java.util.concurrent.ConcurrentLinkedQueue<ByteArray>()
            var audioDropped = 0
            val maxBufferedBytes = 1_600_000 // ~10s of 16kHz PCM16
            val bufferedBytes = java.util.concurrent.atomic.AtomicInteger(0)
            MicStreamBridge.onAudioSinkAttached = {
                // Flush immediately on attach so pre-buffered frames are not lost.
                mainHandler.post { flushNow(outBuf, maxBufferedBytes, bufferedBytes) }
            }
            readThread = Thread {
                // Android expects the AudioRecord read loop to run at audio
                // thread priority; without it some OEMs starve the read (or the
                // OS watchdog reaps the process under heavy capture load).
                try {
                    Process.setThreadPriority(Process.THREAD_PRIORITY_AUDIO)
                } catch (_: Exception) {
                }
                try {
                    while (running) {
                        val n = ar.read(shortBuf, 0, shortBuf.size)
                        if (n > 0) {
                            dataTicks++
                            val bytes = if (resampler != null) {
                                resampler.resample(shortBuf, n)
                            } else {
                                shortsToBytes(shortBuf, n)
                            }
                            // Enforce a back-pressure cap so a late/never-attached
                            // sink can't grow the buffer without bound (OOM).
                            if (bufferedBytes.get() + bytes.size <= maxBufferedBytes) {
                                outBuf.add(bytes)
                                bufferedBytes.addAndGet(bytes.size)
                            } else {
                                audioDropped++
                            }
                        } else if (n < 0) {
                            status("read error: $n")
                            break
                        } else {
                            zeroTicks++
                        }
                        // n == 0: HAL delivered nothing this tick; keep polling.
                        val now = System.currentTimeMillis()
                        if (now - lastDiagAt > 2000) {
                            lastDiagAt = now
                            status("reading: rate=$rate source=UNPROCESSED zeroTicks=$zeroTicks dataTicks=$dataTicks audioPosted=$audioPosted dropped=$audioDropped")
                        }
                    }
                } catch (e: Exception) {
                    status("read exception: ${e.javaClass.simpleName}: ${e.message}")
                }
            }
            readThread?.start()
            // Main-thread flusher: coalesces buffered PCM frames into one sink
            // call every 50ms. Runs as long as capture is active.
            val myToken = captureToken
            val flushRunnable = object : Runnable {
                override fun run() {
                    if (!running || myToken != captureToken) return
                    // Keep buffering until the Flutter audio sink attaches; do NOT
                    // drop frames when it's null (that caused "mic chunks: 0").
                    flushNow(outBuf, maxBufferedBytes, bufferedBytes)
                    mainHandler.postDelayed(this, 50)
                }
            }
            mainHandler.postDelayed(flushRunnable, 50)
        } catch (e: Exception) {
            status("capture exception: ${e.javaClass.simpleName}: ${e.message}")
        }
    }

    /** Coalesces all buffered PCM frames and delivers them to the Flutter audio
     *  sink if attached. When the sink is absent the buffer is preserved (capped)
     *  so no captured audio is lost during the start/sink attach race. */
    private fun flushNow(
        outBuf: java.util.concurrent.ConcurrentLinkedQueue<ByteArray>,
        maxBufferedBytes: Int,
        bufferedBytes: java.util.concurrent.atomic.AtomicInteger,
    ) {
        if (outBuf.isEmpty()) return
        val sink = MicStreamBridge.audioSink ?: return // keep buffering
        val total = outBuf.sumOf { it.size }
        if (total == 0) return
        val merged = ByteArray(total)
        var off = 0
        while (!outBuf.isEmpty()) {
            val b = outBuf.poll()
            System.arraycopy(b, 0, merged, off, b.size)
            off += b.size
        }
        bufferedBytes.addAndGet(-total)
        // Flutter's EventSink throws IllegalStateException if `success` is called
        // after the listener cancels/closure. That throw is uncatchable JNI-side
        // and hard-crashes the whole app. Always guard the call.
        try {
            sink.success(merged)
        } catch (_: Exception) {
            // Listener gone (user cancelled / page disposed). Leave capture
            // running; the next flush will simply find a null sink and buffer.
        }
    }


    private fun buildAudioRecord(rate: Int, bufSize: Int): AudioRecord? {
        // Try UNPROCESSED first. On Android 16 / some OEM builds the
        // VOICE_RECOGNITION and even MIC source can be reserved or starved by the
        // HAL, delivering 0 frames despite focus being granted. UNPROCESSED (when
        // supported) gives raw mic data. Fall back to MIC if UNPROCESSED fails.
        val sources = listOfNotNull(
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q)
                MediaRecorder.AudioSource.UNPROCESSED else null,
            MediaRecorder.AudioSource.MIC,
        )
        for (src in sources) {
            try {
                val ar = AudioRecord(
                    src,
                    rate,
                    AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    bufSize,
                )
                if (ar.state == AudioRecord.STATE_INITIALIZED) {
                    return ar
                }
                ar.release()
            } catch (_: Exception) {
                // try next source
            }
        }
        return null
    }

    private fun pickRate(): Pair<Int, Boolean> {
        // Lever (d): force the FALLBACK_RATE (44100) first. Some Android 16 / OEM
        // HALs only serve the native 44.1k/48k rate and feed a 16 kHz AudioRecord
        // nothing (read() returns 0 forever, focus granted, no error). We resample
        // 44100 -> 16000 in software via LinearResampler. Fall back to 16 kHz if
        // 44.1k isn't supported on this device.
        val ok44 = AudioRecord.getMinBufferSize(
            FALLBACK_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        return if (ok44 > 0) FALLBACK_RATE to true else TARGET_RATE to false
    }

    private fun stopCapture() {
        running = false
        captureToken++
        try {
            readThread?.join(500)
        } catch (_: Exception) {
        }
        readThread = null
        try {
            reader?.stop()
        } catch (_: Exception) {
        }
        try {
            reader?.release()
        } catch (_: Exception) {
        }
        reader = null
    }

    private fun shortsToBytes(buf: ShortArray, n: Int): ByteArray {
        val bb = ByteBuffer.allocate(n * 2).order(ByteOrder.LITTLE_ENDIAN)
        for (i in 0 until n) bb.putShort(buf[i])
        return bb.array()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val mgr = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            if (mgr.getNotificationChannel(CHANNEL_ID) == null) {
                val channel = NotificationChannel(
                    CHANNEL_ID,
                    "Qari Microphone Capture",
                    NotificationManager.IMPORTANCE_LOW,
                )
                channel.setShowBadge(false)
                mgr.createNotificationChannel(channel)
            }
        }
    }

    private fun buildNotification(): Notification {
        val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
        val contentIntent = if (launchIntent != null) {
            PendingIntent.getActivity(
                this,
                0,
                launchIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
        } else {
            null
        }

        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }
        builder
            .setContentTitle("Qari is listening")
            .setContentText("Recording your recitation. Tap to return.")
            .setSmallIcon(R.drawable.ic_mic_notification)
            .setContentIntent(contentIntent)
            .setOngoing(true)
        return builder.build()
    }
}

/** Simple linear-resampler for the 44.1 kHz → 16 kHz fallback. Good enough for
 *  ASR (Whisper is fairly robust to mild resampling artifacts). */
class LinearResampler(private val inRate: Int, private val outRate: Int) {
    private val ratio = inRate.toDouble() / outRate.toDouble()

    fun resample(input: ShortArray, n: Int): ByteArray {
        val outLen = (n / ratio).toInt().coerceAtLeast(1)
        val bb = ByteBuffer.allocate(outLen * 2).order(ByteOrder.LITTLE_ENDIAN)
        for (i in 0 until outLen) {
            val pos = i * ratio
            val i0 = pos.toInt().coerceIn(0, n - 1)
            val i1 = (i0 + 1).coerceIn(0, n - 1)
            val frac = pos - i0
            val s0 = input[i0].toInt()
            val s1 = input[i1].toInt()
            val s = (s0 + (s1 - s0) * frac).toInt().coerceIn(-32768, 32767)
            bb.putShort(s.toShort())
        }
        return bb.array()
    }
}
