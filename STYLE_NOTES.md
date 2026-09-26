# Style notes: "Every Day with Army Sizes"

What Christopher (the original *World War II Every Day with Army Sizes*) and Italian Mapper (the WW1 and
Napoleonic variations) do.
- The WW2 video was studied frame by frame in **4K** (archive.org copy of YouTube 1CqGeAmVu1I).
- WW1 and the Napoleonic Wars were studied at 144p, together with vidIQ's scene analysis.

This is how the renderers in this repo should behave.

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

## How an advance looks (Christopher's WW2 in 4K: Barbarossa, June–July 1941)
- The attacker pushes in **long, rounded spearheads**, like fingers reaching deep into enemy land, instead of
  one line moving forward evenly.
- Enemy **pockets** are left behind as islands inside the attacker's land (Białystok, Minsk). They get the same
  outline and shrink smoothly, with a spinning dashed circle and a fading "300.000 Encircled" label.
- The **front line** is a soft white/cream line, about 2 px at 1080p.
- **Fresh ground** first shows a pale cream fringe that fades into the conqueror's colour over a few days
  (what our capture band does).
- **Pre-war borders** stay visible as thin pink lines inside conquered land.
- Base map: satellite-style terrain under a see-through bloc colour, cities as dark dots, roads and rails as
  thin dark lines. The sea has fine diagonal hatching.
- Captions cross-fade when one replaces another.
- To do: our fronts are single keyframed lines, so fast advances don't show spearheads unless they're drawn
  into the keyframes. A generator that bulges an advancing front into rounded thrusts would help.

## Measured values (Christopher's WW2 in 4K vs our renderer; tools in study/)
These were measured with `study/ref_metrics.py` and `study/fitcap.py` and fitted into `ww1/render.py`.

| What | Christopher | Ours now |
|---|---|---|
| Pace | 2.76 days/s, steady, no slow-downs | 2.75 days/s, steady |
| Soviet colour on land | (183,130,103) | (183,129,103) |
| Axis / Central Powers | (120,125,108) | (121,124,106) |
| Western Allies | (111,155,204) | set to blend to (111,155,204) |
| Sea | (219,230,242) | (219,230,242) |
| Captured pixel, old → new colour | ~30% at +0.1 s, 72% at +0.6 s, 90% at +1.0 s | within about ±0.05 of that |
| Pale fringe (cream 251,230,218) | peaks ~0.7 at +0.2 s, gone by +0.4 s | peaks ~0.66 at +0.2 s, gone by +0.5 s |
| Front line | ~2 px light line, brightest on the lighter bloc's side | thin light line on the Allied/Soviet side, crisp on moving stretches |
| Advance shape | long, irregular thrusts and pockets | irregular thrusts along the direction of advance, only where the front moves more than ~12 px in 10 days |

How his advance really works: Christopher draws a keyframe roughly every 1.6 days. The ground that the next
keyframe will take shows as a see-through pale patch over the defender's colour, and the front sweeps across
it. Ours does the same (`PREVIEW_STEP`).

## Army numbers
- **Exactly one pair per front.** One number sits on each side, mirrored across the line at the same point
  along it, usually near the middle of the front.
- **Set back from the line** by about 4–5% of the screen width (80–105 px at 1080p), never touching it.
- **Parallel to the front.** On steep north–south fronts, both numbers read **top to bottom** (rotated
  clockwise), so they never flip when the front wobbles around vertical.
- **Every number is the same size**, whatever the army's size, at about 30 px text height at 1080p.
- **Open Sans Bold**, white, with a soft dark outline tinted with the side's own colour (dark red for the
  Soviets). Dots are the thousands separators (3.584.536).
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
- Numbers are one fixed, bigger size in Open Sans Bold, with an outline tinted by the side's colour.
- They're set back from the line (`LABEL_SETBACK`, less on short fronts) and parallel to it.
- Steep fronts read top to bottom. The reading direction is worked out day by day, with a margin so it
  rarely flips; when it does, the numbers fade out and back in.
- A front's two numbers share one anchor and one direction, so they sit as a mirrored pair.
- A number slides back if the nearby stretch of front bends toward it. It moves closer if it would spill
  off its own side's land, and it always stays on screen.
- New "client state" faction (`CPC`) with a lighter tint: Kingdom of Poland (Nov 1916) and Ukraine (1918).
- Steel-blue Entente colour.
