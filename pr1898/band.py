"""Turns public-domain piano scores of Sousa marches into a military-band recording.

The scores come from the Mutopia Project (LilyPond sources, public domain); LilyPond turns them into
MIDI, and this module re-orchestrates the two piano staves for a band and renders it with the
GeneralUser GS soundfont (free licence):
  * melody (top voice of the right hand)    -> cornets/trumpets, doubled by clarinets an octave up
  * inner notes of the right hand            -> French horns
  * left hand: upper notes / lowest note     -> trombones / tubas
  * drums from the metre: bass drum on the beat, snare on the off-beats, a cymbal crash on strains
"""
import os

import mido
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SF2 = os.path.join(HERE, "build", "downloads", "GeneralUser-GS.sf2")
SR = 44100

# channel -> (GM program, volume)
BAND = {0: (56, 110), 1: (71, 80), 2: (60, 78), 3: (57, 92), 4: (58, 105), 5: (72, 55)}
DRUM_CH = 9
BASS_DRUM, SNARE, CRASH, CYMBAL = 36, 38, 49, 57


def load_notes(path):
    """-> list of (start_s, end_s, key, velocity, staff) and beat times (s)."""
    mf = mido.MidiFile(path)
    tpb = mf.ticks_per_beat
    # tempo map from all tracks
    tempo_changes = [(0, 500000)]
    meter = [(0, 2, 4)]
    for tr in mf.tracks:
        t = 0
        for m in tr:
            t += m.time
            if m.type == "set_tempo":
                tempo_changes.append((t, m.tempo))
            elif m.type == "time_signature":
                meter.append((t, m.numerator, m.denominator))
    tempo_changes.sort()
    meter.sort()

    def tick2s(tick):
        s, last_t, last_tempo = 0.0, 0, tempo_changes[0][1]
        for t, tempo in tempo_changes[1:]:
            if t >= tick:
                break
            s += (t - last_t) * last_tempo / tpb / 1e6
            last_t, last_tempo = t, tempo
        return s + (tick - last_t) * last_tempo / tpb / 1e6

    notes = []
    for staff, tr in enumerate(mf.tracks):
        t, on = 0, {}
        for m in tr:
            t += m.time
            if m.type == "note_on" and m.velocity > 0:
                on[m.note] = (t, m.velocity)
            elif m.type in ("note_off", "note_on") and m.note in on:
                t0, v = on.pop(m.note)
                notes.append((tick2s(t0), tick2s(t), m.note, v, staff))
    end_tick = max(t for tr in mf.tracks for t in [sum(m.time for m in tr)])
    # beats: dotted quarter in compound metres (6/8), quarter otherwise
    beats = []
    for i, (t0, num, den) in enumerate(meter):
        t1 = meter[i + 1][0] if i + 1 < len(meter) else end_tick
        step = int(tpb * 1.5) if (den == 8 and num % 3 == 0) else tpb * 4 // den
        beats += [tick2s(t) for t in range(t0, t1, max(step, 1))]
    staves = sorted({n[4] for n in notes})
    notes = [(a, b, k, v, staves.index(s)) for a, b, k, v, s in notes]  # 0 = right hand, 1 = left hand
    return sorted(notes), sorted(set(round(b, 4) for b in beats))


def orchestrate(notes, beats):
    """-> list of (time_s, 'on'|'off', channel, key, velocity)."""
    ev = []

    def add(ch, a, b, k, v):
        if 21 <= k <= 108 and b > a:
            ev.append((a, 1, ch, k, v))
            ev.append((b, 0, ch, k, 0))

    # group notes that start together (chords)
    groups = {}
    for a, b, k, v, st in notes:
        groups.setdefault((st, round(a, 3)), []).append((a, b, k, v))
    for (st, _), chord in groups.items():
        chord.sort(key=lambda n: n[2])
        if st == 0:
            a, b, k, v = chord[-1]                   # melody
            add(0, a, b, k, 100)
            add(1, a, b, k + 12 if k < 84 else k, 78)
            if k >= 76:
                add(5, a, b, k + 12, 60)             # piccolo sparkle on high passages
            for a2, b2, k2, v2 in chord[:-1]:       # harmony
                add(2, a2, b2, k2, 70)
        else:
            a, b, k, v = chord[0]                    # bass line
            add(4, a, b, k - 12 if k >= 52 else k, 100)
            for a2, b2, k2, v2 in chord[1:] or chord:
                add(3, a2, b2, k2 if k2 >= 48 else k2 + 12, 80)
    # drums
    end = max(n[1] for n in notes)
    for i, t in enumerate(beats):
        if t >= end:
            break
        nxt = beats[i + 1] if i + 1 < len(beats) else t + 0.3
        ev.append((t, 1, DRUM_CH, BASS_DRUM, 100 if i % 2 == 0 else 80))
        ev.append((t + 0.1, 0, DRUM_CH, BASS_DRUM, 0))
        mid = t + (nxt - t) / 2
        ev.append((mid, 1, DRUM_CH, SNARE, 70))
        ev.append((mid + 0.08, 0, DRUM_CH, SNARE, 0))
        if i % 32 == 0:
            ev.append((t, 1, DRUM_CH, CRASH, 75))
            ev.append((t + 1.0, 0, DRUM_CH, CRASH, 0))
        elif i % 2 == 0:
            ev.append((t, 1, DRUM_CH, CYMBAL, 45))
            ev.append((t + 0.3, 0, DRUM_CH, CYMBAL, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    return ev


def render(midi_path, seconds=None):
    import tinysoundfont
    notes, beats = load_notes(midi_path)
    ev = orchestrate(notes, beats)
    syn = tinysoundfont.Synth(samplerate=SR, gain=-6)
    sfid = syn.sfload(SF2)
    for ch, (prog, vol) in BAND.items():
        syn.program_select(ch, sfid, 0, prog)
        syn.control_change(ch, 7, vol)
    syn.program_select(DRUM_CH, sfid, 128, 0, True)
    total = (seconds or (max(e[0] for e in ev) + 2.0))
    out = np.zeros((int(total * SR), 2), np.float32)
    pos = 0
    for t, kind, ch, key, vel in ev + [(total, 0, 0, 0, 0)]:
        tgt = min(int(t * SR), len(out))
        if tgt > pos:
            buf = np.frombuffer(syn.generate(tgt - pos), np.float32).reshape(-1, 2)
            out[pos:tgt] = buf
            pos = tgt
        if t >= total:
            break
        if kind:
            syn.noteon(ch, key, vel)
        else:
            syn.noteoff(ch, key)
    peak = np.abs(out).max() + 1e-9
    return out / peak * 0.9


if __name__ == "__main__":
    import sys
    import soundfile as sf
    y = render(sys.argv[1], float(sys.argv[3]) if len(sys.argv) > 3 else None)
    sf.write(sys.argv[2], y, SR)
    print(sys.argv[2], len(y) / SR)
