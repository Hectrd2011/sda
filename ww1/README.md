# World War I – Every Front, Every Day with Army Sizes

A ~10-minute animated map of the First World War (28 July 1914 – 11 November 1918), in the
style of *"World War II Every Front with Army Sizes"*: the date ticks forward day by day, front
lines move, army sizes are shown along every front, captions describe each event, and famous
speeches of the war are voiced over a procedurally composed score.

Output: `../WW1_Every_Day_with_Army_Sizes.mp4` (1920×1080, 25 fps, AAC stereo).

## What is in the video

* **Fronts:** Western, Eastern, Italian, Balkan/Salonika, Romanian, Gallipoli, Caucasus,
  Mesopotamia, Sinai & Palestine.
* **Army sizes:** a figure on each side of every front, updated daily.
* **Sieges and battles:** Tannenberg, Przemyśl, Novogeorgievsk, Kut, Verdun, the Somme and others.
* **Captions:** about 150 dated events.
* **Speeches:** Grey, Wilhelm II, Joffre, Mustafa Kemal, Pétain, Wilson, Lenin, Clemenceau,
  Haig and Lloyd George. These are real quotations read by an AI voice (Kokoro TTS), translated
  into English where needed, with an "old gramophone" filter. They are not archival recordings.
* **Music:** composed in code (`audio.py`) with strings, brass and timpani synthesis. Its mood
  follows the war.

Army sizes are rounded estimates of the forces on each front, taken from standard histories.
Front lines are simplified to what shows at this map scale.

## Files

| File | Purpose |
|------|---------|
| `timeline.py` | Historical data: alliances, front-line keyframes, army sizes, events, speeches |
| `basemap.py`  | Static map layers: 1914 borders (with corrections), terrain relief, water, borders |
| `geo.py`      | Helpers to pull shared borders out of the 1914 dataset |
| `audio.py`    | Speech TTS, procedural music, final mix |
| `render.py`   | Frame renderer, pacing, parallel encoding, muxing |

## Rebuilding

```bash
pip install numpy scipy pillow shapely pyproj pyshp imageio-ffmpeg kokoro-onnx soundfile
python3 render.py info                      # timing overview
python3 render.py preview 1916-07-01        # one frame as PNG
python3 render.py video --w 1920 --h 1080   # full video (~30-40 min on 4 cores)
```

Natural Earth data and the Kokoro model download into `build/` automatically the first time
you run it.

## Data credits

* 1914 borders: [historical-basemaps](https://github.com/aourednik/historical-basemaps) (GPL-3.0),
  with corrections in `basemap.BORDER_FIXES`.
* Relief, coastlines, rivers, lakes: [Natural Earth](https://www.naturalearthdata.com) (public domain).
* Voice: [Kokoro-82M](https://github.com/thewh1teagle/kokoro-onnx) (Apache-2.0).
* Font: Open Sans (SIL OFL, see `assets/fonts/OFL.txt`).
