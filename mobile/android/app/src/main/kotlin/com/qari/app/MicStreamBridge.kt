package com.qari.app

import io.flutter.plugin.common.EventChannel

/**
 * Process-wide bridge letting [MicForegroundService] push PCM audio + status to
 * the Flutter [EventChannel] sinks registered in [MainActivity]. The service and
 * the Flutter engine live in the same process, so a plain object works.
 */
object MicStreamBridge {
    var audioSink: EventChannel.EventSink? = null
    var statusSink: EventChannel.EventSink? = null

    /** Set by the service once capture is actually running. Used so that when the
     *  Flutter `mic_stream` listener attaches (and sets [audioSink]), we can
     *  flush any frames that were buffered *before* the sink existed instead of
     *  discarding them (the old behaviour dropped every frame during the
     *  start/sink race → "mic chunks: 0 · bytes sent: 0"). */
    var onAudioSinkAttached: (() -> Unit)? = null

    /** Last status string, replayed to a newly-attached status listener so the
     *  UI never misses the "capture started / error" event due to subscribe race. */
    var lastStatus: String? = null

    /** Called by the EventChannel StreamHandler when Flutter attaches its audio
     *  listener. Wires [audioSink] and notifies the service so it can flush any
     *  pre-buffered frames immediately. */
    fun attachAudioSink(sink: EventChannel.EventSink?) {
        audioSink = sink
        if (sink != null) onAudioSinkAttached?.invoke()
    }
}
