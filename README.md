<h1 align="center">CS2 S-Tier Demos (Parquet)</h1>

<p align="center"><b>Professional Counter-Strike 2 match demos from S-tier events, 2023–2026, parsed to Parquet</b></p>

<p align="center">
  <img alt="Matches" src="https://img.shields.io/badge/matches-2%2C298-blue">
  <img alt="Rounds" src="https://img.shields.io/badge/rounds-110k-blue">
  <img alt="Size" src="https://img.shields.io/badge/size-134%20GB-orange">
  <a href="TERMS.md"><img alt="Terms" src="https://img.shields.io/badge/use-research%20only-lightgrey"></a>
</p>

<p align="center"><b>English</b> | <a href="README_zh-CN.md">简体中文</a></p>

This repository distributes the CS2 S-Tier Demos collection: 65 S-tier events, 2,298 matches and 5,477 map
demos (2023–2026), parsed with [awpy](https://github.com/pnxenopoulos/awpy) 2.0.2 into ten Parquet tables per map.
It mirrors the seven Kaggle datasets of the collection and adds the **cleaned tables** (rounds, per-player round
statistics, kill events, grenades, positions and per-second movement) used by the
[CS2 Dream Match simulator](https://github.com/weyoung-open-lab/cs2-dream-match).

The files are GitHub Release assets (each under 2 GB). This page holds the documentation, the file manifests and
the checksums.

## Download

```bash
python download.py --list               # releases and sizes
python download.py clean                # cleaned tables only (~1.7 GB), enough to retrain the simulator
python download.py raw-member-a         # one raw part (~27 GB)
python download.py raw-patch --only E35 # only the chunks of one event
python download.py all --out /data/cs2  # everything (~135 GB)
```

`download.py` needs only Python 3.8+. It resumes interrupted downloads, checks every file against the release's
`SHA256SUMS.txt` and extracts the raw chunks, so the output folder ends up with `clean/` and the seven
`cs2-s-tier-demos-*` folders in the original Kaggle layout. You can also download single assets from the
[Releases page](https://github.com/weyoung-open-lab/cs2-s-tier-demos/releases) and extract them with `tar -xf`.

| Release | Content | Size | Files |
|---|---|---:|---:|
| `clean-v1` | Cleaned tables + index (below) | 1.7 GB | 29 |
| `raw-member-a` | Part 1 of 7: 13 events, 449 matches | 26.7 GB | 16 chunks |
| `raw-member-b` | Part 2 of 7 | 26.2 GB | 15 chunks |
| `raw-member-c` | Part 3 of 7 | 23.7 GB | 14 chunks |
| `raw-member-d` | Part 4 of 7 | 24.1 GB | 14 chunks |
| `raw-member-e` | Part 5 of 7 | 11.8 GB | 8 chunks |
| `raw-member-e2` | Part 6 of 7 | 10.6 GB | 7 chunks |
| `raw-patch` | Part 7 of 7: 6 events, 202 matches | 10.7 GB | 7 chunks |

Each raw release has a `<part>_000_meta.tar` (per-event file lists with the SHA-256 of every file, plus conversion
reports), numbered chunks such as `member-a_003_E18.tar` (named by the events they contain; whole matches are never
split), `<part>_manifest.csv` (which chunk holds each match and map) and `<part>_SHA256SUMS.txt`. The manifests are
also in [`manifests/`](manifests/), so you can choose chunks before downloading anything.

## Raw data

```
cs2-s-tier-demos-<part>/<upload folder>/<EVENT_FOLDER>/<HLTV_MATCH_ID>/m1_de_mirage/
    header.json  rounds  ticks  kills  damages  shots  grenades  smokes  infernos  bomb  footsteps   (.parquet)
```

`HLTV_MATCH_ID` is the HLTV match id. The prefix of the upload folder (`memberA_`, `patch`, …) is only an upload id.

| Table | Content |
|---|---|
| `ticks` | Per-tick player state (position, view angles, health, armour, weapon, …); about 84 % of the bytes |
| `grenades` | Grenade trajectories; about 12 % of the bytes |
| `kills`, `damages`, `shots`, `footsteps` | Player events |
| `smokes`, `infernos`, `bomb` | Smoke clouds and fires (start, end, position, thrower), bomb plants and defuses |
| `rounds` | `round_num, start, freeze_end, end, winner, reason, bomb_plant, bomb_site` |

Most tables have `round_num` and can be joined with `rounds`. If you only need round- or event-level data, skip `ticks`.

**Known issues of the raw conversion** (fixed in the cleaned tables):
1. Matches that HLTV split into several demos (`-p1`, `-p2`) appear as extra `m2`, `m3` … folders for the same map;
   concatenate them by match and map and de-duplicate rounds.
2. Some events have fake or zero-length opening rounds (for example PGL events); a few maps have an invalid round count.
3. Column types differ between demos (all-null columns; bomb columns missing when no bomb was planted); cast before concatenating.

## Cleaned tables (`clean-v1`)

Split demos are merged, rounds are aligned to the real round number (missing rounds are inferred from legal
scores), and both teams, their names and line-ups are identified. Keys: `map_uid` = `<HLTV match id>_<map>`,
`real_round` = round number in the match, `steamid` = player. Times are seconds after the freeze time ends;
coordinates are game units.

| File | Rows | One row per … |
|---|---:|---|
| `maps.parquet` | 5,121 | map played: event, year, patch, line-ups, team names, final score, quality flags |
| `rounds.parquet` | 110,602 | round: winner, reason, side of each team, equipment value, score before the round, bomb site |
| `round_players.parquet` | 1.1 M | player in a round: team, side, equipment, health, armour at freeze end |
| `round_slots.parquet` | 1.1 M | the same, with a stable slot 0–9 per player within a map (0–4 = team 1) |
| `round_bomb.parquet` | 60,200 | bomb plant: site and tick |
| `player_rounds.parquet` | 1.1 M | player in a round: kills, deaths, damage, utility, opening duels, trades, clutches, … |
| `player_years.parquet` | 1,161 | player and year: rates (KPR, ADR, KAST, HS %, …), split by side |
| `team_years.parquet` | 216 | team and year: the same rates aggregated per team |
| `players.parquet` | 574 | player: most common name, aliases, maps, years |
| `player_roles.parquet` | 697 | player and year: role label (in Chinese: 狙击手 AWPer, 突破手 entry, 步枪手 rifler, 自由人 lurker, 辅助 support) and key indicators |
| `player_places.parquet` | 117,653 | player, year, map, side and time (15/30/55 s): most frequent callout places and shares |
| `team_habits.parquet` | 1,257 | team, year and map: plant rate and sites, plant time, CT setups, pistol/eco/force win rates |
| `place_centers.parquet` | 249 | map and callout place: centre coordinates |
| `positions.parquet` | 8.3 M | player in a round at 5, 10, 15, 20, 30, 40, 55 and 70 s: position, place, weapon, alive |
| `events.parquet` | 907,712 | round event in time order: kill (attacker, victim, weapon, headshot, wallbang, through smoke, positions), plant, round end |
| `utility.parquet` | 2,377,183 | grenade: type (smoke/molotov/flash/HE), thrower, throw/start/end time, throw and landing position |
| `tracks.npy` + `tracks_index.parquet` | 110,602 | round: float16 array `[round, 160 s, 10 slots, (x, y, yaw°, alive)]`; frames after the round ends have alive = −1 |
| `map_bounds.json` | | coordinate range of each map (0.1–99.9 % quantiles) |
| `index_*.csv`, `index_summary.txt` | | audit of the raw folders: one row per map folder (`index_maps.csv`) and per player (`index_map_players.csv`), event list, conversion reports. The `path` column starts with the original server prefix `/root/autodl-tmp/cs2/`; drop it to get the path inside the dataset |
| `p*_report.txt` | | cleaning reports (Chinese) |

To use them with the simulator, put `clean/` at `$CS2_DATA/clean` (see the
[simulator README](https://github.com/weyoung-open-lab/cs2-dream-match)).

Coverage by year: 2023: 6 events, 121 matches; 2024: 18 events, 674 matches; 2025: 21 events, 821 matches;
2026: 20 events, 682 matches.

## Terms and citation

Research use only; see [TERMS.md](TERMS.md). Demo recordings: HLTV.org. Match list and event metadata:
[Liquipedia](https://liquipedia.net/counterstrike/), CC BY-SA 3.0. Not affiliated with Valve, HLTV, Liquipedia or any team.

The collection is also published on Kaggle as seven datasets by
[zhangx1ang](https://www.kaggle.com/zhangx1ang) (`cs2-s-tier-demos-member-a` … `-patch`). Please cite:

```bibtex
@misc{cs2_s_tier_demos,
  author       = {zhangx1ang},
  title        = {{CS2 S-Tier Demos (Parquet)}, {Kaggle} datasets {cs2-s-tier-demos-member-a, -b, -c, -d, -e, -e2} and {-patch}},
  howpublished = {\url{https://www.kaggle.com/zhangx1ang}},
  note         = {Mirror: \url{https://github.com/weyoung-open-lab/cs2-s-tier-demos}},
  year         = {2026}
}
```
