package com.qari.app

import android.os.Bundle
import android.os.FileUtils
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter

class MainActivity : FlutterActivity() {
    companion object {
        const val MIC_CHANNEL = "com.qari.app/mic_foreground"
        const val MIC_STREAM = "com.qari.app/mic_stream"
        const val MIC_STATUS = "com.qari.app/mic_status"
        const val CRASH_CHANNEL = "com.qari.app/crash"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Capture any otherwise-uncatchable native crash (e.g. from the mic
        // foreground service / AudioRecord JNI path) so we can read the stack
        // from the device instead of a silent process death. The stack is
        // written to a file the Flutter side picks up and reports.
        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            try {
                val sw = StringWriter()
                throwable.printStackTrace(PrintWriter(sw))
                val crashFile = File(cacheDir, "crash.txt")
                crashFile.writeText(
                    "thread=${thread.name}\ntime=${System.currentTimeMillis()}\n${sw.toString()}",
                )
            } catch (_: Exception) {
            }
            defaultHandler?.uncaughtException(thread, throwable)
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        val messenger = flutterEngine.dartExecutor.binaryMessenger

        MethodChannel(messenger, MIC_CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "start" -> {
                    // The OS may throw here (e.g. ForegroundServiceStartNotAllowedException
                    // / SecurityException) at the exact moment startForegroundService()
                    // is invoked — BEFORE the service's own try/catch runs. Catch it
                    // and pipe it to the Flutter result so the app never hard-crashes.
                    try {
                        MicForegroundService.start(this)
                        result.success(null)
                    } catch (e: Exception) {
                        MicStreamBridge.lastStatus = "foreground start error: " +
                            "${e.javaClass.simpleName}: ${e.message}"
                        MicStreamBridge.statusSink?.success(MicStreamBridge.lastStatus)
                        result.error("mic_service", MicStreamBridge.lastStatus, null)
                    }
                }
                "stop" -> {
                    try {
                        MicForegroundService.stop(this)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("mic_service", e.message, null)
                    }
                }
                else -> result.notImplemented()
            }
        }

        EventChannel(messenger, MIC_STREAM).setStreamHandler(
            object : EventChannel.StreamHandler {
                override fun onListen(args: Any?, sink: EventChannel.EventSink) {
                    try {
                        MicStreamBridge.attachAudioSink(sink)
                    } catch (e: Exception) {
                        MicStreamBridge.statusSink?.success("stream onListen error: ${e.message}")
                    }
                }

                override fun onCancel(args: Any?) {
                    MicStreamBridge.attachAudioSink(null)
                }
            },
        )

        EventChannel(messenger, MIC_STATUS).setStreamHandler(
            object : EventChannel.StreamHandler {
                override fun onListen(args: Any?, sink: EventChannel.EventSink) {
                    try {
                        MicStreamBridge.statusSink = sink
                        MicStreamBridge.lastStatus?.let { sink.success(it) }
                    } catch (e: Exception) {
                        // ignore — can't report if the sink itself failed
                    }
                }

                override fun onCancel(args: Any?) {
                    MicStreamBridge.statusSink = null
                }
            },
        )

        MethodChannel(messenger, CRASH_CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "readCrash" -> {
                    try {
                        val f = File(cacheDir, "crash.txt")
                        val text = if (f.exists()) f.readText() else ""
                        f.delete()
                        result.success(text)
                    } catch (e: Exception) {
                        result.success("")
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    override fun onDestroy() {
        // Tear the mic foreground service down if the activity is killed without
        // an explicit stop/cancel (e.g. swipe-to-close). Never crash on this.
        try {
            MicForegroundService.stop(this)
        } catch (_: Exception) {
        }
        super.onDestroy()
    }
}
