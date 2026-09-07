# -*- coding: utf-8 -*-
"""10_分时段客流曲线: 典型工作日 vs 周末 10分钟粒度分时客流曲线"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_style import *
import pandas as pd

apply_style()
OUT = os.path.join(project_root(), "分工4_统计可视化", "图片")
os.makedirs(OUT, exist_ok=True)

df = load_inout()
cal = load_calendar()
df["isWorkday"] = df["date"].map(cal)
df = drop_abnormal_days(df)

prof = df.groupby(["isWorkday", "slot"], as_index=False)[["inFlow", "outFlow"]].sum()
days = df.groupby(["isWorkday"])["date"].nunique().to_dict()
prof["flow"] = (prof["inFlow"] + prof["outFlow"]) / prof["isWorkday"].map(days)  # 日均
prof["hour"] = 6 + prof["slot"] / 6.0

fig, ax = plt.subplots(figsize=(11, 6))
for flag, name, color in [(1, "工作日", C_MAIN), (0, "周末", C_ACCENT)]:
    s = prof[prof.isWorkday == flag]
    ax.plot(s["hour"], s["flow"] / 1e4, color=color, lw=2, label=name)
ax.axvspan(7, 9, color=C_C, alpha=0.08); ax.axvspan(17, 19, color=C_HBO, alpha=0.08)
ax.text(8, ax.get_ylim()[1]*0.97, "早高峰", ha="center", color=C_C, fontsize=11)
ax.text(18, ax.get_ylim()[1]*0.97, "晚高峰", ha="center", color=C_HBO, fontsize=11)
ax.set_title("上海地铁分时段客流曲线(10分钟粒度,日均)")
ax.set_xlabel("时刻"); ax.set_ylabel("客流量(万人次/10分钟)")
ax.set_xticks(range(6, 24))
ax.legend()
fig.text(0.99, 0.01, "数据来源: MetroFlow 刷卡数据集 | 分工4", ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-2 分时段客流曲线.png"))
