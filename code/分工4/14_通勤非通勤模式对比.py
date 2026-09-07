# -*- coding: utf-8 -*-
"""14_通勤非通勤模式对比: C(通勤)/HBO(居家其他)/NHB(非居家)出行目的分时段结构"""
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

purp = ["CinFlow", "HB0inFlow", "NHBinFlow"]
names = ["通勤 C", "居家其他 HBO", "非居家 NHB"]
colors = [C_C, C_HBO, C_NHB]

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
for ax, flag, ttl in [(axes[0], 1, "工作日"), (axes[1], 0, "周末")]:
    sub = df[df.isWorkday == flag]
    ndays = sub["date"].nunique()
    g = sub.groupby("slot")[purp].sum() / ndays
    hours = 6 + g.index / 6.0
    for col, nm, c in zip(purp, names, colors):
        ax.plot(hours, g[col] / 1e4, lw=2, color=c, label=nm)
    ax.set_title(ttl)
    ax.set_xlabel("时刻"); ax.set_xticks(range(6, 24))
    ax.axvspan(7, 9, color=C_C, alpha=0.06); ax.axvspan(17, 19, color=C_HBO, alpha=0.06)
axes[0].set_ylabel("进站客流量(万人次/10分钟, 日均)")
axes[1].legend(loc="upper left")
fig.suptitle("通勤 vs 非通勤出行模式: 出行目的分时段结构(进站)", fontsize=15, fontweight="bold")
fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.text(0.99, 0.005, "数据来源: MetroFlow 刷卡数据集 | 分工4", ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-6 通勤非通勤模式对比.png"))
