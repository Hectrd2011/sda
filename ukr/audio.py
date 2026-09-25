"""Audio for the video: TTS speech re-creations, a procedurally composed score, and the final mix.

All sound is generated locally:
  * speeches  - Kokoro TTS (Apache-2.0 model) with an "old gramophone" filter,
  * music     - additive-synthesis strings/brass/timpani written in numpy,
  * mix       - music ducked under the speeches, armistice bells at the end.
"""
import json
import os

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
SR = 44100
KOKORO_MODEL = os.path.join(BUILD, "downloads", "kokoro-v1.0.int8.onnx")
KOKORO_VOICES = os.path.join(BUILD, "downloads", "voices-v1.0.bin")
KOKORO_URLS = {
    KOKORO_MODEL: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx",
    KOKORO_VOICES: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}


# ----------------------------------------------------------------------------- speeches
def gramophone(x, sr, seed=0):
    rng = np.random.default_rng(seed)
    sos = signal.butter(4, [220, 4200], btype="band", fs=sr, output="sos")
    y = signal.sosfilt(sos, x)
    y = y / (np.abs(y).max() + 1e-9)
    y = np.tanh(y * 1.4) / np.tanh(1.4)
    # surface noise: soft hiss + sparse crackles
    hiss = signal.sosfilt(signal.butter(2, [1500, 6000], btype="band", fs=sr, output="sos"),
                          rng.normal(0, 1, len(y))) * 0.004
    crackle = np.zeros(len(y))
    idx = rng.integers(0, len(y), size=int(len(y) / sr * 4))
    crackle[idx] = rng.normal(0, 0.08, len(idx))
    crackle = signal.sosfilt(signal.butter(2, 3000, fs=sr, output="sos"), crackle)
    y = y + hiss + crackle * 0.35
    return (y / (np.abs(y).max() + 1e-9) * 0.9).astype(np.float32)


def make_speeches(speeches):
    out_dir = os.path.join(BUILD, "speech")
    os.makedirs(out_dir, exist_ok=True)
    meta_path = os.path.join(out_dir, "speeches.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    todo = [s for s in speeches if meta.get(s["date"], {}).get("text") != s["text"]]
    if todo:
        for p, url in KOKORO_URLS.items():
            if not os.path.exists(p):
                import urllib.request
                print("downloading", url)
                urllib.request.urlretrieve(url, p)
        from kokoro_onnx import Kokoro
        k = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
        for i, s in enumerate(todo):
            lang = s.get("lang") or ("en-us" if s["voice"].startswith("a") else "en-gb")
            y, sr = k.create(s["text"], voice=s["voice"], speed=0.88, lang=lang)
            y = signal.resample_poly(y, SR, sr).astype(np.float32)
            y = gramophone(y, SR, seed=i)
            y = np.concatenate([np.zeros(int(0.25 * SR), np.float32), y, np.zeros(int(0.35 * SR), np.float32)])
            path = os.path.join(out_dir, s["date"] + ".npy")
            np.save(path, y)
            meta[s["date"]] = dict(text=s["text"], duration=len(y) / SR, path=path)
            print("speech", s["date"], s["speaker"], round(len(y) / SR, 1), "s")
        json.dump(meta, open(meta_path, "w"), indent=1)
    return meta


# ----------------------------------------------------------------------------- music
A4 = 440.0
NOTE = {"C": -9, "C#": -8, "Db": -8, "D": -7, "D#": -6, "Eb": -6, "E": -5, "F": -4, "F#": -3, "Gb": -3,
        "G": -2, "G#": -1, "Ab": -1, "A": 0, "A#": 1, "Bb": 1, "B": 2}


def hz(name):
    n, octv = name[:-1], int(name[-1])
    return A4 * 2 ** ((NOTE[n] + 12 * (octv - 4)) / 12)


def adsr(n, a, r, sr=SR):
    env = np.ones(n, np.float32)
    na, nr = min(int(a * sr), n // 2), min(int(r * sr), n // 2)
    if na:
        env[:na] = np.linspace(0, 1, na) ** 1.5
    if nr:
        env[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return env


def strings(f, dur, rng, bright=0.5, sr=SR):
    """Ensemble string pad: detuned band-limited saws with vibrato, low-passed."""
    n = int(dur * sr)
    t = np.arange(n) / sr
    y = np.zeros(n, np.float32)
    for v in range(5):
        det = f * (1 + rng.normal(0, 0.0035))
        vib = 1 + 0.004 * np.sin(2 * np.pi * (4.8 + rng.random()) * t + rng.random() * 6)
        ph = 2 * np.pi * np.cumsum(det * vib) / sr + rng.random() * 6
        nh = int(min(24, (sr / 2.2) / f))
        for h in range(1, nh + 1):
            y += (np.sin(h * ph) / h * (1.0 if h < 4 else bright ** (h / 4))).astype(np.float32)
    return y / 5


def brass(f, dur, sr=SR):
    n = int(dur * sr)
    t = np.arange(n) / sr
    y = np.zeros(n, np.float32)
    swell = np.minimum(1, t / 0.25)
    for h in range(1, 12):
        y += (np.sin(2 * np.pi * f * h * t) * (swell ** (h * 0.5)) / h ** 1.1).astype(np.float32)
    return y


def timpani(f, dur, sr=SR):
    n = int(dur * sr)
    t = np.arange(n) / sr
    env = np.exp(-t * 3.2)
    y = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t * 6)
         + 0.3 * np.sin(2 * np.pi * f * 1.99 * t) * np.exp(-t * 8)) * env
    noise = np.random.default_rng(int(f)).normal(0, 1, n) * np.exp(-t * 40) * 0.3
    return (y + noise).astype(np.float32)


def snare_roll(dur, sr=SR, seed=1):
    rng = np.random.default_rng(seed)
    n = int(dur * sr)
    y = rng.normal(0, 1, n).astype(np.float32)
    y = signal.sosfilt(signal.butter(2, [800, 7000], btype="band", fs=sr, output="sos"), y)
    t = np.arange(n) / sr
    am = 0.6 + 0.4 * np.abs(np.sin(np.pi * 14 * t))
    return (y * am * np.linspace(0.2, 1, n)).astype(np.float32)


def reverb(x, sr=SR, seconds=3.2, mix=0.35, seed=5):
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    t = np.arange(n) / sr
    ir = rng.normal(0, 1, n) * np.exp(-t * 6.9 / seconds)
    ir = signal.sosfilt(signal.butter(1, 5000, fs=sr, output="sos"), ir)
    ir /= np.sqrt((ir ** 2).sum())
    wet = signal.fftconvolve(x, ir)[:len(x)]
    return (x * (1 - mix) + wet * mix * 3.0).astype(np.float32)


# Chord progressions (voicings as note names) for the sections of the score.
PROG_DARK = [["D2", "A2", "D3", "F3", "A3"], ["Bb1", "F2", "D3", "F3", "Bb3"], ["G1", "D2", "G2", "Bb2", "D3"],
             ["A1", "E2", "C#3", "E3", "A3"]]
PROG_MARCH = [["D2", "A2", "D3", "F3", "A3"], ["C2", "G2", "C3", "E3", "G3"], ["Bb1", "F2", "Bb2", "D3", "F3"],
              ["A1", "E2", "A2", "C#3", "E3"]]
PROG_LAMENT = [["F2", "C3", "F3", "Ab3", "C4"], ["Db2", "Ab2", "Db3", "F3", "Ab3"],
               ["Bb1", "F2", "Bb2", "Db3", "F3"], ["C2", "G2", "C3", "E3", "G3"]]
PROG_HOPE = [["D2", "A2", "D3", "F#3", "A3"], ["B1", "F#2", "B2", "D3", "F#3"], ["G1", "D2", "G2", "B2", "D3"],
             ["A1", "E2", "A2", "C#3", "E3"]]
MELODY_DARK = ["A4", "F4", "E4", "D4", "F4", "E4", "C#4", "D4"]
MELODY_HOPE = ["F#4", "A4", "B4", "A4", "D5", "C#5", "B4", "A4"]


def section(prog, bars, bar_len, rng, intensity, melody=None, drums=False, sr=SR):
    total = bars * bar_len
    n = int(total * sr)
    y = np.zeros(n, np.float32)
    for b in range(bars):
        chord = prog[b % len(prog)]
        s0 = int(b * bar_len * sr)
        dur = bar_len * 1.25
        for i, note in enumerate(chord):
            tone = strings(hz(note), dur, rng, bright=0.35 + 0.25 * intensity)
            tone *= adsr(len(tone), 1.4, 1.6) * (0.9 if i == 0 else 0.55)
            e = min(n, s0 + len(tone))
            y[s0:e] += tone[:e - s0]
        if intensity > 0.45:  # low brass doubling the root
            tone = brass(hz(chord[0]) * 2, bar_len * 0.95) * adsr(int(bar_len * 0.95 * sr), 0.4, 0.8)
            e = min(n, s0 + len(tone))
            y[s0:e] += tone[:e - s0] * 0.18 * intensity
        if drums:
            for k in range(4):
                p = s0 + int(k * bar_len / 4 * sr)
                hit = timpani(hz(chord[0]) * (2 if k % 2 else 1), 1.2) * (0.9 if k == 0 else 0.45)
                e = min(n, p + len(hit))
                y[p:e] += hit[:e - p] * 0.55 * intensity
        if melody is not None and b % 2 == 1:
            for k in range(2):
                note = melody[(b * 2 + k) % len(melody)]
                p = s0 + int(k * bar_len / 2 * sr)
                tone = strings(hz(note), bar_len * 0.6, rng, bright=0.5) * adsr(int(bar_len * 0.6 * sr), 0.3, 0.9)
                e = min(n, p + len(tone))
                y[p:e] += tone[:e - p] * 0.35
    return y


def make_music(total_seconds, cues, seed=11):
    """cues: [(video_second, name)] choosing the section style from that point on."""
    path = os.path.join(BUILD, "music.npy")
    key = json.dumps([round(total_seconds, 2), cues])
    if os.path.exists(path) and os.path.exists(path + ".key") and open(path + ".key").read() == key:
        return np.load(path)
    rng = np.random.default_rng(seed)
    styles = {
        "intro": (PROG_DARK, 0.25, None, False),
        "march": (PROG_MARCH, 0.75, MELODY_DARK, True),
        "dark": (PROG_DARK, 0.5, MELODY_DARK, False),
        "lament": (PROG_LAMENT, 0.4, None, False),
        "tension": (PROG_MARCH, 0.85, None, True),
        "hope": (PROG_HOPE, 0.55, MELODY_HOPE, False),
    }
    bar = 4.0
    out = np.zeros(int((total_seconds + 8) * SR), np.float32)
    cues = sorted(cues) + [(total_seconds + 8, None)]
    for (t0, name), (t1, _) in zip(cues, cues[1:]):
        if name is None:
            continue
        prog, inten, mel, drums = styles[name]
        bars = max(1, int(np.ceil((t1 - t0) / bar)) + 1)
        y = section(prog, bars, bar, rng, inten, mel, drums)
        s0 = int(t0 * SR)
        n = min(len(y), int((t1 - t0 + 3.0) * SR), len(out) - s0)
        fade = np.ones(n, np.float32)
        nf = min(int(3.0 * SR), n // 3)
        fade[:nf] = np.linspace(0, 1, nf)
        fade[-nf:] = np.linspace(1, 0, nf)
        out[s0:s0 + n] += y[:n] * fade
    out = reverb(out)
    out = signal.sosfilt(signal.butter(2, 30, btype="high", fs=SR, output="sos"), out).astype(np.float32)
    out /= np.abs(out).max() + 1e-9
    out = out[:int(total_seconds * SR)]
    np.save(path, out)
    open(path + ".key", "w").write(key)
    return out


def bells(dur=9.0, sr=SR):
    n = int(dur * sr)
    t = np.arange(n) / sr
    y = np.zeros(n, np.float32)
    for k, f in enumerate([hz("D4"), hz("A3"), hz("F#4"), hz("D4"), hz("A3"), hz("D3")]):
        p = int(k * 1.3 * sr)
        tt = t[:n - p]
        partials = [(1, 1.0), (2.0, 0.5), (2.4, 0.35), (3.0, 0.25), (4.2, 0.15), (0.5, 0.4)]
        tone = sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * (1.2 + r * 0.6)) for r, a in partials)
        y[p:] += tone.astype(np.float32) * 0.5
    return reverb(y, seconds=4.0, mix=0.45)


def mix(total_seconds, music, speech_events, bell_time=None):
    """speech_events: [(video_second, samples)]. Returns stereo int16 array."""
    n = int(total_seconds * SR)
    mus = np.zeros(n, np.float32)
    mus[:min(n, len(music))] = music[:n]
    duck = np.ones(n, np.float32)
    voice = np.zeros(n, np.float32)
    for t0, y in speech_events:
        s0 = int(t0 * SR)
        e = min(n, s0 + len(y))
        voice[s0:e] += y[:e - s0]
        a, b = max(0, s0 - int(0.6 * SR)), min(n, e + int(0.8 * SR))
        duck[a:b] = 0.22
    duck = signal.sosfiltfilt(signal.butter(1, 1.5, fs=SR, output="sos"), duck).astype(np.float32)
    out = mus * 0.42 * duck + voice * 1.5
    if bell_time is not None:
        b = bells()
        s0 = int(bell_time * SR)
        e = min(n, s0 + len(b))
        out[s0:e] += b[:e - s0] * 0.35
    # fade in/out
    fi, fo = int(2.0 * SR), int(4.0 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    rms = np.sqrt((out ** 2).mean()) + 1e-9
    out = out * (0.14 / rms)
    out = np.tanh(out * 1.2) / 1.2  # soft limiter
    out = np.clip(out / max(1.0, np.abs(out).max() / 0.97), -1, 1)
    # gentle stereo widening of the music only
    left = out + 0.0
    right = out + 0.0
    return (np.stack([left, right], 1) * 32767).astype(np.int16)


if __name__ == "__main__":
    import timeline
    m = make_speeches(timeline.SPEECHES)
    print(json.dumps({k: round(v["duration"], 2) for k, v in m.items()}, indent=1))
