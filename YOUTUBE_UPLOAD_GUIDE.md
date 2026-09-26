# YouTube upload guide

Everything to copy and paste for each video: title, description with chapters, tags and settings.
The chapter times come from the videos' own timelines, so they match the videos exactly.

---

## Settings for every video

| Setting | What to choose |
|---|---|
| File | the **4K** file if you can join the parts (see below); otherwise the **1080p** file |
| Thumbnail | the matching `*_thumbnail.jpg` |
| Playlist | make one called **"Every Day with Army Sizes"** and add every video |
| Audience | **No, it's not made for kids** |
| Altered or synthetic content | **Yes** for videos 1–5 (real quotations read by an AI voice); **No** for the Russia–Ukraine video (original recordings) |
| Category | **Education** |
| Language | English |
| Captions | leave the automatic ones |
| Comments | On |
| Visibility | upload as **Unlisted** first, check it once, then switch to **Public** |
| Best time to publish | Friday–Sunday afternoon (your local time) |

**4K parts:** the 4K videos are split into parts only because of GitHub's size limit. For YouTube,
join them into one file with the free app **Shotcut**, or with `ffmpeg -f concat` on a computer. Or
just upload the 1080p file, which already looks sharp.

**Copyright:** the 1898 Puerto Rico video uses *La Marcha Real* and *Die Toten Erwachen* from other
people's uploads. It may get a copyright claim. That usually only means the ad money goes to the owner,
and the video stays up. If you'd rather avoid that, ask for the synthesized-band version.

---

## Step by step: uploading from your phone

Do this in the **YouTube** app, then finish in the **YouTube Studio** app, which is free. Chapters, tags and the
"altered content" question are easier in Studio.

1. Get the video onto your phone. In this chat, tap the video file and save it to Photos. For the full-quality
   file, open the repo on GitHub, tap the `_1080p.mp4` file, then **View raw** / **Download**.
2. Save the thumbnail (`*_thumbnail.jpg`) to Photos the same way.
3. In the YouTube app, tap **+**, then **Video**, and pick the video.
4. **Title:** paste the title from this guide.
5. **Description:** tap it and paste the whole description block from this guide, chapters included.
6. **Visibility:** choose **Unlisted** for now.
7. **Audience:** "No, it's not made for kids".
8. Tap **Upload** and wait until it says processing is finished (HD can take 10–30 minutes).
9. Open **YouTube Studio**, then **Content**, and tap the new video, then the pencil icon to edit:
   - **Thumbnail:** tap it, then choose the saved `*_thumbnail.jpg`.
   - **Tags** (under "Show more"): paste the tags line.
   - **Altered or synthetic content:** use the answer listed for that video below.
   - **Category:** Education.
   - **Playlist:** "Every Day with Army Sizes". Create it the first time.
   - Save.
10. Watch it once, all the way through, as Unlisted. Check that the chapters show under the video and the sound is fine.
11. Check **Studio, Content, Restrictions**. "Copyright claim" is normal for the videos with game or band music:
    the video stays up and the ads money goes to the music owner. Don't dispute it.
12. Set a **publish time:** Studio, Visibility, **Schedule**, and pick the date and time from the schedule below.
13. When it goes live, post a comment and **pin** it:
    `Which war should I map next? 👇`
14. Share the link in places where map fans hang out, such as r/MapPorn or r/europe for the WW1 and Ukraine
    videos, and Puerto Rico groups for the PR videos. Don't spam the same link everywhere on the same day.

---

## Posting schedule (your local time, around 3 pm is good)

| Date | Video | Why |
|---|---|---|
| Sat 26 Sep 2026 | **6. Russia–Ukraine War** | biggest search topic right now; post it first |
| (already up) | **3. Spanish–American War** | |
| Sat 3 Oct | **1. WW1 – Europe** | |
| Sat 10 Oct | **5. 1898 Puerto Rican Campaign** | |
| Sat 17 Oct | **2. WW1 – World** | |
| **Fri 30 Oct** | **4. 1950 Nationalist uprisings** | the anniversary of the Jayuya uprising (30 Oct 1950) |

After that, one video a week on the same day and time. YouTube rewards channels that post regularly.

---

## 1. WW1 – Europe

**Title**
```
World War I: Every Day with Army Sizes (1914–1918)
```

**Description**
```
Every day of the First World War in Europe and the Middle East, from 28 July 1914 to the Armistice on 11 November 1918 – with the size of every army on every front.

Watch the Western Front freeze into trenches, Russia collapse into revolution, and the Central Powers fall one by one.

⏱ Chapters
0:00 Intro
0:08 1914 – The war begins
0:36 The Battle of the Marne
1:22 1915
2:03 Gorlice–Tarnów & the Great Retreat
3:26 1916
3:43 Verdun
4:18 The Brusilov Offensive & the Somme
5:30 1917
6:02 The USA enters the war
7:15 The Russian Revolution
7:33 1918
8:02 The German Spring Offensive
8:53 The Hundred Days Offensive
9:37 The Armistice

📌 Notes
• Army sizes are rounded estimates of the forces on each front, based on standard histories.
• Front lines are simplified to what is visible at this scale.
• Speeches are real historical quotations performed by an AI voice (translated where needed).
• Map data: Natural Earth, historical-basemaps (1914 borders).

Which front do you want to see next? Tell me in the comments 👇

#ww1 #history #maps
```

**Tags**
```
ww1, world war 1, world war i, ww1 every day, world war 1 every day, army sizes, every day with army sizes, ww1 map, western front, eastern front, map animation, history, 1914, 1918, great war, battle of the somme, verdun, brusilov offensive, armistice
```

---

## 2. WW1 – World (all fronts)

**Title**
```
World War I on Every Front of the World – Every Day with Army Sizes
```

**Description**
```
The whole First World War on one world map – Europe, the Middle East, Africa, Asia and the Pacific – every day from 1914 to 1918, with army sizes on every front.

See the German colonies fall one by one, Japan take Tsingtao, Lettow-Vorbeck's army fight on in East Africa until after the Armistice, and country after country join the Allies.

⏱ Chapters
0:00 Intro
0:08 1914 – The war begins
0:36 The Battle of the Marne
1:22 1915
2:03 Gorlice–Tarnów & the Great Retreat
3:26 1916
3:43 Verdun
4:18 The Brusilov Offensive & the Somme
5:30 1917
6:02 The USA enters the war
7:15 The Russian Revolution
7:33 1918
8:02 The German Spring Offensive
8:53 The Hundred Days Offensive
9:37 The Armistice

📌 Notes
• Army sizes are rounded estimates, based on standard histories.
• Colonial campaigns are shown as the area each side held, simplified for a world map.
• Speeches are real historical quotations performed by an AI voice (translated where needed).
• Map data: Natural Earth, historical-basemaps (1914 borders).

Watch the Europe-only version for a closer look at the Western and Eastern Fronts.

#ww1 #history #maps
```

**Tags**
```
ww1, world war 1, world war i, ww1 every day, ww1 every front, army sizes, every day with army sizes, ww1 world map, world war 1 map, east africa campaign, tsingtao, ottoman empire, map animation, history, great war, 1914, 1918
```

---

## 3. Spanish–American War & Philippine–American War

**Title**
```
The Spanish–American & Philippine–American War – Every Day with Army Sizes
```

**Description**
```
The Spanish–American War and the Philippine–American War day by day, from 1898 to 1902, with the size of every army – in Cuba, Puerto Rico and the Philippines.

From Dewey at Manila Bay and San Juan Hill to the long guerrilla war in the Philippines.

⏱ Chapters
0:00 Intro
0:08 War is declared
0:21 The Battle of Manila Bay
1:42 San Juan Hill
2:15 The Puerto Rico campaign
2:40 The fall of Manila
3:17 The Treaty of Paris
3:34 The Philippine–American War begins
5:24 The guerrilla war
7:38 Aguinaldo is captured
8:26 Balangiga
9:26 Cuban independence
9:37 The end of the war

📌 Notes
• Army sizes are rounded estimates from standard histories.
• Areas of control are simplified – the guerrilla war had no fixed front lines.
• Speeches are real historical quotations performed by an AI voice.
• Map data: Natural Earth.

#history #spanishamericanwar #maps
```

**Tags**
```
spanish american war, philippine american war, 1898, every day with army sizes, army sizes, map animation, cuba, philippines, puerto rico, san juan hill, manila bay, aguinaldo, history, american history, filipino history
```

---

## 4. 1950 Puerto Rican Nationalist uprisings

**Title**
```
The 1950 Puerto Rican Nationalist Uprisings – Hour by Hour
```

**Description**
```
The Nationalist uprisings of 30 October 1950 across Puerto Rico, hour by hour – Jayuya, Utuado, Naranjito, Mayagüez, Arecibo, Ponce, La Fortaleza and the attack on Blair House in Washington.

The day Blanca Canales proclaimed the Free Republic of Puerto Rico in Jayuya, and the National Guard answered with troops and planes.

⏱ Chapters
0:00 Intro
0:19 Peñuelas
0:31 The uprising begins
0:43 Jayuya & La Fortaleza
1:00 The National Guard is called out
1:39 Air attacks on Jayuya & Utuado
2:30 The Blair House attack
3:16 The arrest of Albizu Campos

📌 Notes
• Force sizes are rounded estimates; times of day are approximate.
• Quotations are performed by an AI voice (Spanish originals where they were spoken in Spanish).
• Map data: Natural Earth; elevation: AWS Terrain Tiles.

#puertorico #history #maps
```

**Tags**
```
puerto rico, jayuya uprising, 1950 nationalist uprising, puerto rico history, nationalist party, pedro albizu campos, blanca canales, utuado, la fortaleza, blair house, historia de puerto rico, grito de jayuya, map animation, history
```

---

## 5. 1898 Puerto Rican Campaign

**Title**
```
The US Invasion of Puerto Rico (1898) – Hour by Hour with Army Sizes
```

**Description**
```
The Puerto Rican Campaign of the Spanish–American War, hour by hour – from the bombardment of San Juan to the landing at Guánica, the march inland, the armistice and the handover of the island on 18 October 1898.

Watch the four American columns push up the island's roads against the Spanish army, with the size of every force.

⏱ Chapters
0:00 Intro
0:10 The bombardment of San Juan
1:30 The landing at Guánica
2:03 Ponce surrenders
2:49 The landing at Arroyo
3:32 The Battle of Guayama
4:14 The Battle of Coamo
4:27 Silva Heights & Mayagüez
4:50 Asomante & the armistice
5:39 The handover

📌 Notes
• Army sizes are rounded estimates; small detachments and times of day are approximate.
• US-held ground spreads along the roads of 1898 from the towns held on each date.
• Speeches are historical quotations performed by an AI voice.
• Music: La Marcha Real; J. P. Sousa, The Pride of the Wolverines (US Marine Band); Die Toten Erwachen.
• Map data: Natural Earth; elevation: AWS Terrain Tiles.

#puertorico #history #spanishamericanwar
```

**Tags**
```
puerto rico, puerto rican campaign, 1898, spanish american war, invasion of puerto rico, puerto rico history, historia de puerto rico, guanica, coamo, army sizes, every day with army sizes, map animation, history, nelson miles
```

---

## 6. Russia–Ukraine War (2022–2026)

**Title**
```
Russia's Invasion of Ukraine: Every Day with Troop Numbers (2022–2026)
```

**Description**
```
The Russian invasion of Ukraine every day from 24 February 2022 to September 2026 – the front line, the occupied territory and the number of troops on each side.

From the battle for Kyiv and the fall of Mariupol to the Kharkiv and Kherson counteroffensives, Bakhmut, the Kursk incursion, Pokrovsk and the fighting of 2026.

⏱ Chapters
0:00 The invasion begins
0:09 The battle for Kyiv
0:42 Russia withdraws from the north – Bucha
1:07 The fall of Mariupol
1:19 The battle for the Donbas
1:42 The Kharkiv counteroffensive
2:08 Kherson is liberated
2:29 Soledar & Bakhmut
3:13 The Kakhovka dam & the 2023 counteroffensive
4:34 Avdiivka
4:55 US aid & the Kharkiv offensive
5:28 Ukraine invades Kursk
6:01 North Korean troops arrive
6:38 The Oval Office clash & the fall of the Kursk salient
7:07 Operation Spiderweb
7:31 The Alaska summit
8:00 The battle for Pokrovsk
8:23 Ukraine's 2026 counteroffensive
9:04 The Kramatorsk fortress belt
9:38 The war so far

📌 Notes
• Troop numbers are rounded estimates of the forces committed along each front, based on published estimates; the real numbers are uncertain and disputed.
• Front lines are simplified to what is visible at this scale, based on daily situation maps.
• Speeches are the original recordings: Vladimir Putin (24 Feb 2022), Volodymyr Zelenskyy (Feb 2022 and his address to the US Congress, Dec 2022) and Joe Biden in Warsaw (Feb 2023).
• Music: GosT – Behemoth (Perturbator remix); Hearts of Iron IV – Katyusha; Hearts of Iron III – Well Oiled War Machine; Hearts of Iron IV – The End of the War.
• Map data: Natural Earth; elevation: AWS Terrain Tiles.

Which war should I map next? Tell me in the comments 👇

#ukraine #russia #maps
```

**Tags**
```
russia ukraine war, ukraine war map, war in ukraine, russian invasion of ukraine, every day, troop numbers, army sizes, every day with army sizes, map animation, ukraine front line, kharkiv counteroffensive, kherson, bakhmut, kursk, pokrovsk, zelensky, putin, 2022, 2026, history
```

**Settings for this video**
- Altered or synthetic content: **No**. The speeches are the original recordings.
- It will likely get **copyright claims** for the music (Paradox and GosT). The video stays up and the ad money goes to them.
- YouTube often gives war videos **limited ads** (yellow $ icon). That's normal for this topic. Don't edit the video to fight it.

---
