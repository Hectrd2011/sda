# Style notes: "Every Day with Army Sizes"

What Italian Mapper (Christopher) does in *World War II*, *World War I* and *Napoleonic Wars Every Day with
Army Sizes*. I checked these frame by frame (144p copies) and against vidIQ's scene analysis. This is how
the renderers in this repo should behave.

## Map
- **The camera never moves.** One fixed view of the whole theatre, with no zoom or pan.
- **Muted, matte bloc colours** over a faint hillshade. Rivers and old internal borders show as faint lines.
  - WW1: Central Powers olive, Entente steel blue, Soviet Russia terracotta.
  - WW2: Axis charcoal, USSR terracotta, Western Allies blue.
- **Neutrals** are pale cream. **Sea** is pale grey-blue.
- **Client and puppet states** get a *lighter tint* of their bloc's colour:
  - Kingdom of Poland 1916 and Ukraine 1918 in WW1
  - Vichy France in WW2
  - Duchy of Warsaw in the Napoleonic Wars

  Ordinary occupied land (Belgium, Serbia) keeps the occupier's full colour.
- WW2 turns the base map snowy in winter.

## Borders and fronts
- Fronts move **smoothly on every frame**, never in jumps from one day to the next.
- Conquered land takes the conqueror's colour directly. The reference has no flash. Ours keeps a faint
  light band on freshly taken ground.
- Where two warring blocs meet, the front is a thin, light line.
- Encircled pockets shrink smoothly and carry a small label, e.g. "330.000 Encircled".
- When a country joins or leaves the war, its colour changes quickly. At an armistice, the whole map fades
  to neutral.

## Army numbers
- **Exactly one pair per front.** One number sits on each side, mirrored across the line at the same point
  along it, usually near the middle of the front.
- **Set back from the line** by about 3–4% of the screen width, never touching it.
- **Parallel to the front**, including steep fronts (up to about 75°). Text always reads left to right and
  never flips upside down.
- **Every number is the same size**, whatever the army's size.
- White, clean sans-serif, with dots as thousands separators (2.734.704) and a subtle shadow.
- Numbers count up and down smoothly on every frame. They fade in when a front opens and out when it closes.

## Text
- **Date** top-left in bold (`22 JUN 1941`), with the hour below in small type.
- **Caption** bottom-left in dark bold text directly on the map, with no box. It changes on the event's
  date and stays until the next one.
- A legend is optional. The end is a short "thank you for watching" or the closing card.

## Pacing
- **Steady**, about 2.5–2.8 days per second (WW2: 2.76, WW1: 2.45). The reference doesn't slow down for
  battles; captions and speeches carry the big moments instead.

## What changed in our renderer (ww1/render.py)
- Numbers are one fixed size, set back from the line (`LABEL_SETBACK`), and parallel to the front up to
  about 75°, instead of being capped at 45°.
- A front's two numbers share one anchor, so they sit as a mirrored pair.
- If a front bends toward a number, the number slides further back so no part of it ever touches the line.
- New "client state" faction (`CPC`) with a lighter tint: Kingdom of Poland (Nov 1916) and Ukraine (1918).
- Steel-blue Entente colour.
