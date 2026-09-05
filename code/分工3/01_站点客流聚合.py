# -*- coding: utf-8 -*-
"""分工3 · 站点级客流聚合
从10分钟粒度进出站数据聚合出全天/早高峰/晚高峰/工作日日均/周末日均客流。
输出: 分工3_空间可视化/空间数据/station_flow_agg.csv
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import pandas as pd

# ---------- 配置 ----------
MORNING_PEAK = (7, 9)    # 早高峰 7:00-9:00
EVENING_PEAK = (17, 19)  # 晚高峰 17:00-19:00
OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "空间数据"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "station_flow_agg.csv"

# ---------- 读取数据 ----------
inout_path = find_data("std_10min_inout.csv")
calendar_path = find_data("workday_calendar.csv")
station_path = find_data("station_info.csv")

print(f"读取进出站数据: {inout_path}")
workday = pd.read_csv(calendar_path)
workday["date"] = workday["date"].astype(str)
workday_dict = dict(zip(workday["date"], workday["isWorkday"]))

station_info = pd.read_csv(station_path)
station_info = station_info[["stationID", "name", "lon", "lat"]]

# 分块读取聚合
chunk_list = []
for chunk in pd.read_csv(inout_path, chunksize=1_000_000):
    chunk["date"] = chunk["date"].astype(str)
    chunk["hour"] = pd.to_datetime(chunk["datetime"]).dt.hour
    chunk["is_workday"] = chunk["date"].map(workday_dict)
    chunk["total_flow"] = chunk["inFlow"] + chunk["outFlow"]  # 进出站合计
    chunk_list.append(chunk)
df = pd.concat(chunk_list, ignore_index=True)
print(f"共 {len(df)} 条记录, {df['stationID'].nunique()} 个站点")

# ---------- 多维度聚合 ----------
def agg_flow(mask=None, suffix=""):
    d = df[mask] if mask is not None else df
    return d.groupby("stationID")["total_flow"].sum().reset_index().rename(columns={"total_flow": suffix})

station_total = agg_flow(None, "全天总客流")
station_morning = agg_flow((df["hour"] >= MORNING_PEAK[0]) & (df["hour"] < MORNING_PEAK[1]), "早高峰客流")
station_evening = agg_flow((df["hour"] >= EVENING_PEAK[0]) & (df["hour"] < EVENING_PEAK[1]), "晚高峰客流")

# 工作日日均
wd = df[df["is_workday"] == 1].groupby(["stationID", "date"])["total_flow"].sum().reset_index()
station_workday = wd.groupby("stationID")["total_flow"].mean().reset_index().rename(columns={"total_flow": "工作日日均"})

# 周末日均
we = df[df["is_workday"] == 0].groupby(["stationID", "date"])["total_flow"].sum().reset_index()
station_weekend = we.groupby("stationID")["total_flow"].mean().reset_index().rename(columns={"total_flow": "周末日均"})

# 合并
station_flow = station_info.merge(station_total, on="stationID", how="left")
for s in [station_morning, station_evening, station_workday, station_weekend]:
    station_flow = station_flow.merge(s, on="stationID", how="left")

station_flow.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
print(f"站点客流聚合完成: {OUT_FILE} ({len(station_flow)} 站)")
