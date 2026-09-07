# -*- coding: utf-8 -*-
"""20_城区郊区客流对比: 各环线圈层客流规模 + 早高峰潮汐现象(进出站方向差)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_style import *
import pandas as pd
import numpy as np

apply_style()
OUT = os.path.join(project_root(), "分工4_统计可视化", "图片")
os.makedirs(OUT, exist_ok=True)

df = drop_abnormal_days(load_inout())
cal = load_calendar()
df["isWorkday"] = df["date"].map(cal)
ac = load_area_class()
ndays_wd = df[df.isWorkday == 1]["date"].nunique()

ring_order = ["内环内", "内中环间", "中外环间", "外环外"]
df = df.merge(ac[["stationID", "ring"]], on="stationID", how="left")
nst = ac.groupby("ring")["stationID"].nunique()

# 左: 各圈层站均日客流(工作日)
wd = df[df.isWorkday == 1]
ring_flow = wd.groupby("ring")["total"].sum() / ndays_wd
ring_avg = (ring_flow / nst).loc[ring_order]

# 右: 早高峰(7-9点)进站占比 -> 潮汐指数
am = wd[(wd.hour >= 7) & (wd.hour < 9)]
tide = am.groupby("ring")[["inFlow", "outFlow"]].sum()
tide["in_share"] = tide["inFlow"] / (tide["inFlow"] + tide["outFlow"]) * 100
tide = tide.loc[ring_order]

x = np.arange(len(ring_order))
fig, axes = plt.subplots(1, 2, figsize=(10.12, 4.35))

ax = axes[0]
b = ax.bar(x, ring_avg.values / 1e4, 0.3,
           color=[C_MAIN, C_ACCENT, C_HBO, C_NHB])
for bb, v in zip(b, ring_avg.values):
    ax.text(bb.get_x() + bb.get_width()/2, v / 1e4, f"{v/1e4:.2f}万", ha="center", fontsize=12)
ax.set_xticks(x); ax.set_xticklabels(ring_order)
ax.set_ylabel("站均日客流量(人次/站, 工作日)")
ax.set_title("各圈层站点客流规模(站均, 工作日)")
for xi, n in zip(x, nst.loc[ring_order]):
    ax.text(xi, ax.get_ylim()[1]*0.02, f"{n}站", ha="center", fontsize=11, color="white",
            fontweight="bold")

ax = axes[1]
b = ax.bar(x, tide["in_share"].values, 0.3, color=[C_MAIN, C_ACCENT, C_HBO, C_NHB])
ax.axhline(50, color=C_GRAY, ls="--", lw=1)
for bb, v in zip(b, tide["in_share"].values):
    d = "进站为主" if v > 50 else "出站为主"
    ax.text(bb.get_x() + bb.get_width()/2, v + 0.5, f"{v:.1f}%\n{d}", ha="center", fontsize=11)
ax.set_xticks(x); ax.set_xticklabels(ring_order)
ax.set_ylabel("早高峰进站客流占比(%)")
ax.set_ylim(0, 100)
ax.set_title("早高峰潮汐方向(工作日 07:00-09:00)")

fig.suptitle("城区 / 郊区客流对比: 规模与潮汐", fontsize=17, fontweight="bold")
fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.text(0.99, 0.005, "数据来源: MetroFlow 进出站客流 × 站点区位分类表 | 分工4",
         ha="right", fontsize=10, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-12 城区郊区客流对比.png"))
