import warnings

warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv*", category=RuntimeWarning)
from pydub import AudioSegment
import librosa
import numpy as np
import scipy.io.wavfile as wavfile
import soundfile as sf
import scipy.signal as signal
import wave
import threading
import time
import simpleaudio as sa


# this file contains the code for all audio operations.

# detects the selected audio files bpm
def detect_bpm(file_path):
    y, sr = librosa.load(file_path, sr=None)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo = tempo.item() if isinstance(tempo, np.ndarray) else tempo
    return f"Detected BPM: {tempo:.2f}"


# normalizes the selected audio file
def normalize_audio(file_path, output_path, headroom=1.0):
    audio = AudioSegment.from_wav(file_path)
    normalized_audio = audio.normalize(headroom=headroom)
    normalized_audio.export(output_path, format="wav")
    return f"Normalized audio saved to {output_path}"


# removes silence from the selected audio file
def remove_silence(input_file, output_file, threshold=-40.0, min_silence_len=1000):
    try:
        sample_rate, data = wavfile.read(input_file)

        if len(data.shape) == 1:
            data = data[:, np.newaxis]

        original_dtype = data.dtype
        data = data.astype(np.float32) / np.iinfo(original_dtype).max

        dBFS = 20 * np.log10(np.abs(data) + 1e-10)
        silence_mask = dBFS < threshold
        silence_mask = np.all(silence_mask, axis=1)

        silence_indices = np.where(silence_mask)[0]
        silence_segments = []
        start = None
        for i in range(len(silence_indices)):
            if start is None:
                start = silence_indices[i]
            if i + 1 < len(silence_indices) and silence_indices[i + 1] - silence_indices[i] > 1:
                end = silence_indices[i]
                if (end - start + 1) * 1000 / sample_rate >= min_silence_len:
                    silence_segments.append((start, end + 1))
                start = None
        if start is not None:
            end = silence_indices[-1]
            if (end - start + 1) * 1000 / sample_rate >= min_silence_len:
                silence_segments.append((start, end + 1))

        if silence_segments:
            indices_to_remove = np.concatenate([np.arange(start, end) for start, end in silence_segments])
            non_silent_data = np.delete(data, indices_to_remove, axis=0)
        else:
            non_silent_data = data

        non_silent_data = (non_silent_data * np.iinfo(original_dtype).max).astype(original_dtype)
        sf.write(output_file, non_silent_data, sample_rate)

        return f"Silence removed and saved to {output_file}"

    except Exception as e:
        return f"Error removing silence: {str(e)}"


# creates EQ for the user to interact with
def design_biquad_filter(frequency, sample_rate, gain, q=1.0):
    w0 = 2 * np.pi * frequency / sample_rate
    alpha = np.sin(w0) / (2 * q)
    A = 10 ** (gain / 40.0)

    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A

    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0

    return b, a


def apply_equalizer(input_file, output_file, bands=None):
    if bands is None:
        # Default EQ settings: mild shaping
        bands = [
            {'frequency': 60, 'gain': 6.0},
            {'frequency': 250, 'gain': -4.0},
            {'frequency': 1000, 'gain': 5.0},
            {'frequency': 4000, 'gain': -5.0},
        ]

    try:
        data, sample_rate = sf.read(input_file)

        if len(data.shape) == 1:
            data = data[:, np.newaxis]

        for channel in range(data.shape[1]):
            for band in bands:
                b, a = design_biquad_filter(band['frequency'], sample_rate, band['gain'])
                data[:, channel] = signal.lfilter(b, a, data[:, channel])

        sf.write(output_file, data, sample_rate)
        return f"Equalized audio saved to {output_file}"

    except Exception as e:
        return f"Error applying equalizer: {str(e)}"


# boosts all bass frequencies for the user
def bass_boost(input_file, output_file, gain_db=10.0, cutoff=150.0):
    try:
        data, sample_rate = sf.read(input_file)

        if len(data.shape) == 1:
            data = data[:, np.newaxis]

        # Create a low-shelf filter
        nyquist = 0.5 * sample_rate
        norm_cutoff = cutoff / nyquist

        # second-order butterworth filter
        sos = signal.butter(N=2, Wn=norm_cutoff, btype='low', output='sos')

        # Convert gain in dB to a linear scale
        gain_factor = 10 ** (gain_db / 20.0)

        # Apply filter and boost
        for ch in range(data.shape[1]):
            low_freq = signal.sosfilt(sos, data[:, ch])
            data[:, ch] += low_freq * gain_factor

        # Prevent clipping
        data = np.clip(data, -1.0, 1.0)

        sf.write(output_file, data, sample_rate)
        return f"Bass boost applied and saved to {output_file}"

    except Exception as e:
        return f"Error applying bass boost: {str(e)}"


def apply_reverb(input_file, output_file, delay_ms=50, decay=0.4):
    try:
        data, sample_rate = sf.read(input_file)
        delay_samples = int(sample_rate * (delay_ms / 1000.0))

        if len(data.shape) == 1:
            data = data[:, np.newaxis]

        output = np.copy(data)

        for ch in range(data.shape[1]):
            for i in range(delay_samples, len(data)):
                output[i, ch] += decay * output[i - delay_samples, ch]

        # Prevent clipping
        output = np.clip(output, -1.0, 1.0)

        sf.write(output_file, output, sample_rate)
        return f"Reverb applied and saved to {output_file}"

    except Exception as e:
        return f"Error applying reverb: {str(e)}"


def reverse_audio(input_path, output_path):
    try:
        audio = AudioSegment.from_wav(input_path)
        reversed_audio = audio.reverse()
        reversed_audio.export(output_path, format="wav")
        return f"Reversed audio saved to {output_path}"
    except Exception as e:
        return f"Error reversing audio: {str(e)}"


def play_with_meter(file_path, window):
    def run():
        try:
            wf = wave.open(file_path, 'rb')
            audio_data = wf.readframes(wf.getnframes())
            samples = np.frombuffer(audio_data, dtype=np.int16)

            num_channels = wf.getnchannels()
            if num_channels == 2:
                samples = samples[::2]  # down mix stereo to mono

            chunk_size = 1024
            step_size = chunk_size // 2  # 50% overlap
            sample_rate = wf.getframerate()

            wave_obj = sa.WaveObject(audio_data, wf.getnchannels(), wf.getsampwidth(), sample_rate)
            play_obj = wave_obj.play()

            smoothed_level = 0
            decay_rate = 2  # lower = slower falloff

            for i in range(0, len(samples) - chunk_size, step_size):
                if not play_obj.is_playing():
                    break

                chunk = samples[i:i + chunk_size]
                rms = np.sqrt(np.mean(chunk ** 2))
                level = int(min(40, rms / 1000))  # scale for 0–40 meter

                # Apply smoothing
                if level > smoothed_level:
                    smoothed_level = level
                else:
                    smoothed_level = max(0, smoothed_level - decay_rate)

                window.write_event_value("-METER-UPDATE-", smoothed_level)
                time.sleep(step_size / sample_rate)

            play_obj.wait_done()
            window.write_event_value("-METER-UPDATE-", 0)

        except Exception as e:
            window.write_event_value("-OUTPUT-APPEND-", f"Error in volume meter: {str(e)}\n")

    threading.Thread(target=run, daemon=True).start()

