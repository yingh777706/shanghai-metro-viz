# -*- coding: utf-8 -*-
"""16_出行距离分布直方图: 基于OD客流与站点坐标的出行距离分布(客流加权,分块读取大文件)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_style import *
import pandas as pd
import numpy as np

apply_style()
OUT = os.path.join(project_root(), "分工4_统计可视化", "图片")
os.makedirs(OUT, exist_ok=True)

info = load_station_info().set_index("stationID")
od_path = load_od()

dist_sum, flow_sum = None, 0
bins = np.arange(0, 60.5, 1.0)   # 1km 间隔,0~60km
hist = np.zeros(len(bins) - 1)

for chunk in pd.read_csv(od_path, chunksize=2_000_000):
    chunk.columns = [c.strip() for c in chunk.columns]
    oc = "originStation" if "originStation" in chunk.columns else "origin"
    dc = "destinationStation" if "destinationStation" in chunk.columns else "destination"
    sub = chunk[[oc, dc, "Flow"]].dropna()
    sub = sub[sub[oc] != sub[dc]]
    o = info.loc[sub[oc].values]; d = info.loc[sub[dc].values]
    dist = haversine_km(o["lon"].values, o["lat"].values,
                        d["lon"].values, d["lat"].values)
    h, _ = np.histogram(dist, bins=bins, weights=sub["Flow"].values)
    hist += h
    flow_sum += sub["Flow"].sum()

fig, ax = plt.subplots(figsize=(11, 6))
centers = (bins[:-1] + bins[1:]) / 2
ax.bar(centers, hist / 1e4, width=0.9, color=C_MAIN, alpha=0.85)
mean_d = (centers * hist).sum() / hist.sum()
ax.axvline(mean_d, color=C_C, ls="--", lw=1.5, label=f"客流加权平均距离 {mean_d:.1f} km")
ax.set_title("乘客出行距离分布(OD客流加权)")
ax.set_xlabel("出行距离(km, 起终点球面距离)")
ax.set_ylabel("客流量(万人次, 2017-05~08 合计)")
ax.legend()
fig.text(0.99, 0.01, "数据来源: MetroFlow OD客流 + 站点坐标 | 分工4",
         ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-8 出行距离分布直方图.png"))
print("总OD客流:", flow_sum)
