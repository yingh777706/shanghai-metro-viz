# -*- coding: utf-8 -*-
"""22_星期几客流模式: 周一至周日客流柱状图 + 典型日分时曲线对比"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_style import *
import pandas as pd
import numpy as np

apply_style()
OUT = os.path.join(project_root(), "分工4_统计可视化", "图片")
os.makedirs(OUT, exist_ok=True)

df = drop_abnormal_days(load_inout())
caldf = load_calendar_df()
wd_map = dict(zip(caldf["date"], caldf["weekday"]))
df["weekday"] = df["date"].map(wd_map)

order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

daily = df.groupby(["date", "weekday"])["total"].sum().reset_index()
by_wd = daily.groupby("weekday")["total"].mean().loc[order]

# 分时: 周一至四/周五/周六/周日
grp_map = {**{d: "周一至周四" for d in order[:4]},
           "Friday": "周五", "Saturday": "周六", "Sunday": "周日"}
df["daygrp"] = df["weekday"].map(grp_map)
ndays = df.groupby("daygrp")["date"].nunique()
prof = df.groupby(["daygrp", "slot"])["total"].sum().reset_index()
prof["total"] = prof["total"] / prof["daygrp"].map(ndays)
prof["hour"] = 6 + prof["slot"] / 6.0

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.35))

ax = axes[0]
colors = [C_MAIN]*4 + ["#e377c2", C_ACCENT, C_ACCENT]
b = ax.bar(cn, by_wd.values / 1e4, 0.6, color=colors)
for bb, v in zip(b, by_wd.values):
    ax.text(bb.get_x() + bb.get_width()/2, v / 1e4, f"{v/1e4:.0f}", ha="center", fontsize=12)
ax.set_ylabel("平均日客流量(万人次)")
ax.set_title("一周各日平均客流")

ax = axes[1]
for gname, c in [("周一至周四", C_MAIN), ("周五", "#e377c2"), ("周六", C_ACCENT), ("周日", C_HBO)]:
    s = prof[prof.daygrp == gname]
    ax.plot(s["hour"], s["total"] / 1e4, lw=2, color=c, label=gname)
ax.axvspan(7, 9, color=C_C, alpha=0.06); ax.axvspan(17, 19, color=C_HBO, alpha=0.06)
ax.set_title("典型日分时段客流(日均)")
ax.set_xlabel("时刻"); ax.set_ylabel("客流量(万人次/10分钟)")
ax.set_xticks(range(6, 24))
ax.legend()

fig.suptitle("星期几客流模式", fontsize=17, fontweight="bold")
fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.text(0.99, 0.005, "数据来源: MetroFlow 进出站客流 × 工作日日历 | 分工4",
         ha="right", fontsize=10, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-14 星期几客流模式.png"))
