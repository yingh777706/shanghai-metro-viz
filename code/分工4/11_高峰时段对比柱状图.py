# -*- coding: utf-8 -*-
"""11_高峰时段对比柱状图: 早高峰/午间/晚高峰/其他 时段客流占比(工作日 vs 周末)"""
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

def period(h):
    if 7 <= h < 9: return "早高峰\n07:00-09:00"
    if 17 <= h < 19: return "晚高峰\n17:00-19:00"
    if 11 <= h < 14: return "午间\n11:00-14:00"
    return "其他时段"
df["period"] = df["hour"].map(period)

g = df.groupby(["isWorkday", "period"])["total"].sum().unstack(0)
order = ["早高峰\n07:00-09:00", "午间\n11:00-14:00", "晚高峰\n17:00-19:00", "其他时段"]
g = g.loc[order]
share = g / g.sum() * 100

x = np.arange(len(order)); w = 0.36
fig, ax = plt.subplots(figsize=(10, 6))
b1 = ax.bar(x - w/2, share[1], w, color=C_MAIN, label="工作日")
b2 = ax.bar(x + w/2, share[0], w, color=C_ACCENT, label="周末")
for bs in (b1, b2):
    for b in bs:
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.4,
                f"{b.get_height():.1f}%", ha="center", fontsize=10)
ax.set_xticks(x); ax.set_xticklabels(order)
ax.set_ylabel("客流占比(%)")
ax.set_title("高峰时段客流占比对比:工作日 vs 周末")
ax.legend()
fig.text(0.99, 0.01, "数据来源: MetroFlow 刷卡数据集 | 分工4", ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-3 高峰时段对比柱状图.png"))
