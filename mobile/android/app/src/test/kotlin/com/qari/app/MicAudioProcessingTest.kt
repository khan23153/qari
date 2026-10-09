package com.qari.app

import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.PI
import kotlin.math.roundToInt
import kotlin.math.sin
import kotlin.math.sqrt
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MicAudioProcessingTest {
    private fun tone(hz: Double, amplitude: Double = 12000.0): ShortArray =
        ShortArray(44100) { index ->
            (amplitude * sin(2.0 * PI * hz * index / 44100.0)).roundToInt().toShort()
        }

    private fun convert(input: ShortArray, chunkSize: Int): ByteArray {
        val converter = LinearResampler(44100, 16000)
        val output = ByteArrayOutputStream()
        var offset = 0
        while (offset < input.size) {
            val end = minOf(offset + chunkSize, input.size)
            val chunk = input.copyOfRange(offset, end)
            output.write(converter.resample(chunk, chunk.size))
            offset = end
        }
        return output.toByteArray()
    }

    private fun rms(bytes: ByteArray): Double {
        val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer()
        // Exclude filter startup. This compares sustained waveform energy.
        var sum = 0.0
        var count = 0
        for (index in 512 until buffer.limit()) {
            val value = buffer.get(index).toDouble()
            sum += value * value
            count++
        }
        return sqrt(sum / count)
    }

    @Test
    fun samplesAndWaveformDoNotDependOnRecorderReadSizes() {
        val input = tone(1000.0)
        val whole = convert(input, input.size)
        assertEquals("One second stays one second", 32000, whole.size)
        for (chunkSize in listOf(1, 441, 512, 882, 1024, 2048)) {
            assertArrayEquals("read size=$chunkSize", whole, convert(input, chunkSize))
        }
    }

    @Test
    fun rejectsUltrasonicInputBeforeItAliasesIntoSpeech() {
        for (frequency in listOf(10000.0, 13000.0, 18000.0)) {
            val outputRms = rms(convert(tone(frequency), 1024))
            val inputRms = 12000.0 / sqrt(2.0)
            assertTrue("$frequency Hz alias must be rejected: ${outputRms / inputRms}",
                outputRms / inputRms < 0.03)
        }
    }

    @Test
    fun retainsSpeechBandEnergy() {
        for (frequency in listOf(200.0, 1000.0, 4000.0)) {
            val ratio = rms(convert(tone(frequency), 512)) / (12000.0 / sqrt(2.0))
            assertTrue("$frequency Hz speech amplitude changed: $ratio", ratio in 0.9..1.1)
        }
    }

    @Test
    fun emptyReadDoesNotInventAudioOrResetPhase() {
        val converter = LinearResampler(44100, 16000)
        val input = tone(1000.0)
        val output = ByteArrayOutputStream()
        output.write(converter.resample(input.copyOfRange(0, 512), 512))
        assertEquals(0, converter.resample(shortArrayOf(), 0).size)
        output.write(converter.resample(input.copyOfRange(512, input.size), input.size - 512))
        assertArrayEquals(convert(input, input.size), output.toByteArray())
    }

    @Test
    fun silentInputStaysSilent() {
        val output = convert(ShortArray(44100), 512)
        assertEquals(32000, output.size)
        assertTrue(output.all { it == 0.toByte() })
    }
}
