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

    /** Last status string, replayed to a newly-attached status listener so the
     *  UI never misses the "capture started / error" event due to subscribe race. */
    var lastStatus: String? = null
}
