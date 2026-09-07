# -*- coding: utf-8 -*-
"""17_出行时长分布直方图: OD客流加权估计出行时长 + 网络距离分布
   数据: od_travel_time.csv(分工1补充) × std_10min_od.csv(12GB分块聚合)
   若已存在 /tmp/data/od_flow_agg.csv(按OD对聚合的客流)则直接复用"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_style import *
import pandas as pd
import numpy as np

apply_style()
OUT = os.path.join(project_root(), "分工4_统计可视化", "图片")
os.makedirs(OUT, exist_ok=True)

# ---- 按OD对聚合实际客流(分块读12GB OD表; 有缓存则秒读) ----
cache = os.path.join(os.path.dirname(load_od()), "od_flow_agg.csv")
if os.path.exists(cache):
    flow = pd.read_csv(cache)
else:
    acc = {}
    od_path = load_od()
    for chunk in pd.read_csv(od_path, chunksize=2_000_000,
                             usecols=["originStation", "destinationStation", "Flow"],
                             skipinitialspace=True):
        chunk = chunk[chunk.originStation != chunk.destinationStation]
        g = chunk.groupby(["originStation", "destinationStation"])["Flow"].sum()
        for k, v in g.items():
            acc[k] = acc.get(k, 0) + v
    flow = pd.Series(acc).rename("Flow").reset_index()
    flow.columns = ["originStation", "destinationStation", "Flow"]
    flow.to_csv(cache, index=False)
print("OD对(有客流):", len(flow), "总客流:", flow.Flow.sum())

# ---- 与时长/距离表合并 ----
tt = load_od_travel_time()
m = flow.merge(tt, on=["originStation", "destinationStation"], how="inner")
print("合并后OD对:", len(m))

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.35))

# 左: 出行时长分布
ax = axes[0]
bins = np.arange(0, 180, 5)
wgt = m["Flow"].values
h, edges = np.histogram(m["est_time_min"], bins=bins, weights=wgt)
centers = (edges[:-1] + edges[1:]) / 2
ax.bar(centers, h / 1e4, width=4.4, color=C_MAIN, alpha=0.85)
mean_t = (m["est_time_min"] * wgt).sum() / wgt.sum()
ax.axvline(mean_t, color=C_C, ls="--", lw=1.5,
           label=f"客流加权平均时长 {mean_t:.0f} 分钟")
ax.set_title("乘客出行时长分布(OD客流加权)")
ax.set_xlabel("估计乘车时长(分钟)"); ax.set_ylabel("客流量(万人次)")
ax.legend()

# 右: 网络距离分布(对比直线距离更真实)
ax = axes[1]
bins = np.arange(0, 110, 2)
h, edges = np.histogram(m["distance_km"], bins=bins, weights=wgt)
centers = (edges[:-1] + edges[1:]) / 2
ax.bar(centers, h / 1e4, width=1.76, color=C_ACCENT, alpha=0.85)
mean_d = (m["distance_km"] * wgt).sum() / wgt.sum()
ax.axvline(mean_d, color=C_C, ls="--", lw=1.5,
           label=f"客流加权平均距离 {mean_d:.1f} km")
ax.set_title("乘客出行距离分布(沿地铁网络, OD客流加权)")
ax.set_xlabel("出行距离(km, 网络路径距离)"); ax.set_ylabel("客流量(万人次)")
ax.legend()

fig.suptitle("乘客出行时长与距离分布", fontsize=17, fontweight="bold")
fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.text(0.99, 0.005, "数据来源: MetroFlow OD客流 × OD时长估计表 | 分工4",
         ha="right", fontsize=10, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-9 出行时长与距离分布.png"))
