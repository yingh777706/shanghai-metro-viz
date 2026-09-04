# 补充数据说明（新增/增强 4 张表）

本目录在原有 5 张 csv 基础上，新增 3 张表、增强 1 张表，用于支撑三项分析：
出行时长、线路客流强度、核心城区 vs 郊区差异。

## 文件清单

| 文件 | 状态 | 内容 |
| --- | --- | --- |
| `station_info.csv` | **增强（替换原表）** | 原 5 列基础上追加 `lines/n_lines/is_transfer/dist_km_center/ring/area/core_suburb` 7 列 |
| `station_line_map.csv` | 新增 | 站点→线路映射（长表，换乘站多行） |
| `station_area_class.csv` | 新增 | 站点城区/郊区标签 + 环线口径 |
| `od_travel_time.csv` | 新增 | OD 对→估算出行时长（模型估算，非实测） |
| `std_10min_od.csv` | 原样 | 10 分钟 OD 客流（未改动，体积巨大） |
| `std_10min_inout.csv` | 原样 | 10 分钟进出站客流 |
| `weather_hourly.csv` / `workday_calendar.csv` | 原样 | 天气 / 工作日标记 |

---

## 1. 站点→线路映射（`station_line_map.csv`、`station_info.csv` 的 `lines` 列）

**来源**：`raw_data/_station_lines_2017.csv`，取自
[beyondsimulations/Metro-Inflow-Optimization](https://github.com/beyondsimulations/Metro-Inflow-Optimization)
（`data_public/Shanghai/station_lines_2017.csv`，该仓库对原 MetroFlow 数据做了站点-线路归属修正）。
按**站名精确匹配**到本数据集的 302 个站点（302/302 全部匹配，仅 1 站名首尾空格差异已清洗）。

**字段**（`station_line_map.csv`，长表，每行 = 一个站点在一条线路上的归属）：

| 字段 | 含义 |
| --- | --- |
| `stationID` | 站点 ID |
| `name` | 站点名 |
| `line` | 线路号（1–13、16，2017.05–08 运营线路） |
| `is_transfer` | 是否换乘站（1=属多条线路） |

`station_info.csv` 中对应 `lines`（逗号分隔线路号，如 `1,2,8`）、`n_lines`（所属线路数）、`is_transfer`（n_lines≥2 记 1）。

**用于「线路客流强度」排序**：把 `station_line_map.csv` 按 `stationID` join 到客流表后按 `line` 分组求和即可。

> ⚠️ 换乘站客流归属：进出站客流（`std_10min_inout`）不区分乘客实际乘坐哪条线，换乘站的客流在按线路汇总时存在归属口径问题——可按「平分到各线」或「仅统计单线站 + 换乘站单独列示」处理，请自行选择口径。

---

## 2. 城区 / 郊区分类（`station_area_class.csv`、`station_info.csv` 的 `ring/area/core_suburb`）

**口径**：以人民广场站（stationID=2035）为城市中心，按**球面距离**分环（近似上海内环/中环/外环）：

| 距离 | 环线标签 `ring` | 三分类 `core_suburb` | 二分类 `area` |
| --- | --- | --- | --- |
| ≤ 5 km | 内环内 | 核心城区 | 城区 |
| 5–10 km | 内中环间 | 城区过渡 | 城区 |
| 10–15 km | 中外环间 | 城区过渡 | 城区 |
| > 15 km | 外环外 | 郊区 | 郊区 |

**字段**（`station_area_class.csv`）：`stationID/name/lon/lat/dist_km_center/ring/area/core_suburb`。

**分布**：内环内 58 站、内中环间 101 站、中外环间 61 站、外环外 82 站（`area` 城区 220 / 郊区 82）。

**用于「核心城区 vs 郊区」差异**：直接按 `area`（城区/郊区，15km 界）或 `core_suburb`（核心城区/郊区，剔中间过渡带）分组对比即可。

> ⚠️ 阈值（5/10/15 km）为**可调口径**，不是官方行政区划。个别边界站（如虹桥火车站 15.6km、莘庄 17km）落在临界处，可按需微调 `build_supplementary_tables.py` 中 `RING_*` 参数重算。

---

## 3. 出行时长（`od_travel_time.csv`）

**重要说明：本数据集无法计算真实出行时长。** 原始刷卡数据已被聚合为 10 分钟粒度的
OD 流量（仅 Flow/CFlow/HBOFlow/NHBFlow 计数），**不含个体乘客的进站/出站时刻**，
因此「平均/中位出行时长」无法从数据中实测。

`od_travel_time.csv` 提供的是**模型估算出行时长**，算法如下：

1. 以 `station_info.neighbour` 为无向图边，边权 = 站点间球面距离（km）；
2. 对每个 OD 对求**最短路径**（Dijkstra，按距离）；
3. 估算时长 = `distance_km / 33 km/h × 60` + `换乘次数 × 4 min`。

**字段**：

| 字段 | 含义 |
| --- | --- |
| `originStation` / `destinationStation` | 起 / 终点站点 ID |
| `origin_name` / `dest_name` | 起 / 终点站名 |
| `n_hops` | 最短路径经过的边数（约等于经停站数） |
| `distance_km` | 路径总里程（球面距离） |
| `n_transfers` | 沿途换乘次数（线路号变化次数，含步行换乘边） |
| `est_time_min` | **估算出行时长（分钟）** |

**参数（可调）**：平均旅速 `AVG_SPEED_KMH=33`、换乘附加 `TRANSFER_PENALTY_MIN=4`，
位于 `script/build_supplementary_tables.py` 顶部。

> ⚠️ 局限：
> - 全程用统一平均旅速 33 km/h，**郊区快线（16 号线等）实际更快**，长距离郊区出行会被略高估；
> - `neighbour` 含少量空间近邻边（步行换乘），最短路径可能走步行捷径，属合理近似；
> - 换乘附加 4 min 为通用经验值。
> 若需更准的「平均出行时长」，需回到原始刷卡明细（含每次行程进出站时间）重新计算，本数据集无法支持。

---

## 复现

所有表由 `script/build_supplementary_tables.py` 生成，重新运行：

```bash
python script/build_supplementary_tables.py
```

依赖仅 pandas。线路映射源文件 `raw_data/_station_lines_2017.csv` 已随附。
