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
        // background thread (uncatchable JNI crash).
        mainHandler.post { MicStreamBridge.statusSink?.success(msg) }
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
            val ar = AudioRecord(
                MediaRecorder.AudioSource.VOICE_RECOGNITION,
                rate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                minBuf * 2,
            )
            if (ar.state != AudioRecord.STATE_INITIALIZED) {
                ar.release()
                status("capture error: AudioRecord not initialized (rate=$rate)")
                return
            }
            ar.startRecording()
            if (ar.recordingState != AudioRecord.RECORDSTATE_RECORDING) {
                ar.release()
                status("capture error: AudioRecord not recording (rate=$rate)")
                return
            }
            reader = ar
            running = true
            status("capture started: rate=$rate resample=$resample")
            val shortBuf = ShortArray(minBuf / 2)
            val resampler = if (resample) LinearResampler(rate, TARGET_RATE) else null
            readThread = Thread {
                try {
                    while (running) {
                        val n = ar.read(shortBuf, 0, shortBuf.size)
                        if (n > 0) {
                            val bytes = if (resampler != null) {
                                resampler.resample(shortBuf, n)
                            } else {
                                shortsToBytes(shortBuf, n)
                            }
                            // Route to the main thread (Flutter sink rule).
                            val data = bytes
                            mainHandler.post { MicStreamBridge.audioSink?.success(data) }
                        } else if (n < 0) {
                            status("read error: $n")
                            break
                        }
                        // n == 0: HAL delivered nothing this tick; keep polling.
                    }
                } catch (e: Exception) {
                    status("read exception: ${e.javaClass.simpleName}: ${e.message}")
                }
            }
            readThread?.start()
        } catch (e: Exception) {
            status("capture exception: ${e.javaClass.simpleName}: ${e.message}")
        }
    }

    private fun pickRate(): Pair<Int, Boolean> {
        val ok = AudioRecord.getMinBufferSize(
            TARGET_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        return if (ok > 0) TARGET_RATE to false else FALLBACK_RATE to true
    }

    private fun stopCapture() {
        running = false
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
