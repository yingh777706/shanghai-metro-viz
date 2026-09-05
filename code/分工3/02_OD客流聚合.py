# -*- coding: utf-8 -*-
"""分工3 · OD客流聚合
从10分钟粒度OD数据聚合出TOP_N客流对，匹配起终点经纬度。
输出: 分工3_空间可视化/空间数据/od_flow_agg.csv
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import pandas as pd

# ---------- 配置 ----------
TOP_N = 50
OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "空间数据"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "od_flow_agg.csv"

# ---------- 读取数据 ----------
od_path = find_data("std_10min_od.csv")
station_path = find_data("station_info.csv")
print(f"读取OD数据: {od_path}")

station_info = pd.read_csv(station_path)
station_info = station_info[["stationID", "name", "lon", "lat"]]

# 分块读取聚合
od_agg = pd.DataFrame()
for chunk in pd.read_csv(od_path, chunksize=1_000_000):
    chunk_agg = chunk.groupby(["originStation", "destinationStation"])["Flow"].sum().reset_index()
    od_agg = pd.concat([od_agg, chunk_agg], ignore_index=True)
    od_agg = od_agg.groupby(["originStation", "destinationStation"])["Flow"].sum().reset_index()

# 取TOP_N
od_top = od_agg.sort_values("Flow", ascending=False).head(TOP_N)

# 匹配起点
od_top = od_top.merge(station_info, left_on="originStation", right_on="stationID", how="left") \
    .rename(columns={"name": "o_name", "lon": "o_lon", "lat": "o_lat"}).drop(columns=["stationID"])
# 匹配终点
od_top = od_top.merge(station_info, left_on="destinationStation", right_on="stationID", how="left") \
    .rename(columns={"name": "d_name", "lon": "d_lon", "lat": "d_lat"}).drop(columns=["stationID"])

od_top.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
print(f"OD聚合完成: {OUT_FILE} (TOP{TOP_N})")
