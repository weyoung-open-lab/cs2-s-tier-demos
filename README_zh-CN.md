<h1 align="center">CS2 S 级赛事录像数据集（Parquet）</h1>

<p align="center"><a href="README.md">English</a> | <b>简体中文</b></p>

2023–2026 年 65 个 S 级赛事、2,298 场职业比赛、5,477 张地图的 *Counter-Strike 2* 录像，用
[awpy](https://github.com/pnxenopoulos/awpy) 2.0.2 解析成 Parquet，每张图 10 张表，共约 134 GB。
本仓库是 Kaggle 上 7 个数据集的完整镜像，另外提供 [CS2 梦幻对决模拟器](https://github.com/weyoung-open-lab/cs2-dream-match)
用到的**清洗后数据**（回合、每人每回合数据、击杀事件、道具、站位、逐秒走位）。

数据文件放在 GitHub Releases 里（每个文件不超过 2 GB），本页是说明文档、文件清单和校验码。

## 下载

```bash
python download.py --list               # 查看有哪些、各多大
python download.py clean                # 只要清洗后的数据（约 1.7 GB），足够重新训练模拟器
python download.py raw-member-a         # 原始数据的某一卷（约 27 GB）
python download.py raw-patch --only E35 # 只下载某个赛事所在的包
python download.py all --out /data/cs2  # 全部（约 135 GB）
```

`download.py` 只需要 Python 3.8 以上，不用装任何包：断了可以接着下，每个文件都按 `SHA256SUMS.txt` 校验，原始数据自动解压，
最后得到 `clean/` 和 7 个 `cs2-s-tier-demos-*` 文件夹，目录结构和 Kaggle 原版完全一样。也可以在
[Releases 页面](https://github.com/weyoung-open-lab/cs2-s-tier-demos/releases) 单独下载某个文件，用 `tar -xf` 解压。

| Release | 内容 | 大小 | 文件数 |
|---|---|---:|---:|
| `clean-v1` | 清洗后的数据和索引（见下文） | 1.7 GB | 29 |
| `raw-member-a` | 第 1/7 卷：13 个赛事、449 场 | 26.7 GB | 16 个包 |
| `raw-member-b` | 第 2/7 卷 | 26.2 GB | 15 个包 |
| `raw-member-c` | 第 3/7 卷 | 23.7 GB | 14 个包 |
| `raw-member-d` | 第 4/7 卷 | 24.1 GB | 14 个包 |
| `raw-member-e` | 第 5/7 卷 | 11.8 GB | 8 个包 |
| `raw-member-e2` | 第 6/7 卷 | 10.6 GB | 7 个包 |
| `raw-patch` | 第 7/7 卷：6 个赛事、202 场 | 10.7 GB | 7 个包 |

每个原始数据 Release 里有：`<卷名>_000_meta.tar`（每个赛事的文件清单，含每个文件的 SHA-256，以及转换报告）；
编号的数据包，例如 `member-a_003_E18.tar`（按包含的赛事命名，同一场比赛不会被拆到两个包里）；
`<卷名>_manifest.csv`（每场比赛、每张图在哪个包里）；`<卷名>_SHA256SUMS.txt`（每个包的校验码）。
文件清单也放在 [`manifests/`](manifests/) 里，下载前就能挑要哪些包。

## 原始数据

```
cs2-s-tier-demos-<卷名>/<上传文件夹>/<赛事文件夹>/<HLTV 比赛编号>/m1_de_mirage/
    header.json  rounds  ticks  kills  damages  shots  grenades  smokes  infernos  bomb  footsteps   （.parquet）
```

| 表 | 内容 |
|---|---|
| `ticks` | 每个 tick 的选手状态（位置、视角、血量、护甲、武器……），约占 84% 的体积 |
| `grenades` | 道具飞行轨迹，约占 12% |
| `kills`、`damages`、`shots`、`footsteps` | 击杀、伤害、开枪、脚步事件 |
| `smokes`、`infernos`、`bomb` | 烟雾、燃烧（开始/结束时间、位置、投掷者），下包和拆包 |
| `rounds` | `round_num, start, freeze_end, end, winner, reason, bomb_plant, bomb_site` |

大多数表有 `round_num`，可以和 `rounds` 关联。只需要回合或事件级数据时可以不下载 `ticks`。

**原始数据的已知问题**（清洗后的数据已处理）：
1. HLTV 拆成多段的录像（`-p1`、`-p2`）会在同一张图下多出 `m2`、`m3` 等文件夹，需要按比赛和地图拼接并去掉重复回合；
2. 部分赛事（例如 PGL）有假的或零时长的开局回合，少数地图的回合数不合法；
3. 不同录像的列类型可能不同（整列为空、没下包时缺少 bomb 列），拼接前要统一类型。

## 清洗后的数据（`clean-v1`）

已经拼接分段录像、按真实回合号对齐（缺失回合按合法比分推断），并识别出两队、队名和阵容。
主键：`map_uid` = `<HLTV 比赛编号>_<地图>`，`real_round` = 比赛中的回合号，`steamid` = 选手。
时间是冻结时间结束后的秒数，坐标是游戏单位。每张表的说明见[英文版](README.md#cleaned-tables-clean-v1)，表名和字段名相同。

| 文件 | 行数 | 每行是 |
|---|---:|---|
| `maps.parquet` | 5,121 | 一张图：赛事、年份、版本、阵容、队名、最终比分、质量标记 |
| `rounds.parquet` | 110,602 | 一个回合：胜方、方式、双方阵营、装备价值、回合前比分、包点 |
| `player_rounds.parquet` | 110 万 | 一名选手的一个回合：击杀、死亡、伤害、道具、首杀、补枪、残局…… |
| `player_years.parquet` / `team_years.parquet` | 1,161 / 216 | 选手-年份 / 战队-年份 的各项比率（分攻防） |
| `player_roles.parquet` | 697 | 选手-年份：角色（狙击手、突破手、步枪手、自由人、辅助）和关键指标 |
| `events.parquet` | 907,712 | 按时间排列的回合事件：击杀（武器、爆头、穿墙、穿烟、双方位置）、下包、回合结束 |
| `utility.parquet` | 2,377,183 | 一颗道具：类型、投掷者、出手/生效/结束时间、出手和落点位置 |
| `positions.parquet` | 830 万 | 冻结结束后 5–70 秒 8 个时刻的选手位置、点位、武器、是否存活 |
| `tracks.npy` | 110,602 | 每回合逐秒走位，float16 `[回合, 160 秒, 10 个位置号, (x, y, 朝向°, 是否存活)]` |
| 其余 | | `round_players`、`round_slots`、`round_bomb`、`players`、`player_places`、`team_habits`、`place_centers`、`map_bounds.json`、`index_*`（原始目录审计）、`p*_report.txt`（清洗报告） |

配合模拟器使用时，把 `clean/` 放到 `$CS2_DATA/clean`（见[模拟器说明](https://github.com/weyoung-open-lab/cs2-dream-match)）。

## 使用条款和引用

**仅限科研使用**，详见 [TERMS.md](TERMS.md)。录像来源 HLTV.org；比赛列表和赛事信息来自
[Liquipedia](https://liquipedia.net/counterstrike/)（CC BY-SA 3.0）。与 Valve、HLTV、Liquipedia 及任何战队无关。

数据集同时以 7 个数据集的形式发布在 Kaggle（作者 [zhangx1ang](https://www.kaggle.com/zhangx1ang)）。引用格式见[英文版](README.md#terms-and-citation)。
