# -*- coding: utf-8 -*-
"""19_线路客流对比图: 14条线路日均客流柱状图 + 代表线路分时曲线
   换乘站客流按其线路数均摊到各线路,避免重复计数"""
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
lm = load_line_map()
ndays = df["date"].nunique()

# 站点日均总客流
st = df.groupby("stationID")["total"].sum() / ndays
# 站点分时段日均客流
prof = df.groupby(["stationID", "slot"])["total"].sum() / ndays
prof = prof.reset_index()

# 线路客流: 换乘站按 n_lines 均摊
lm2 = lm.copy()
lm2["n_lines"] = lm2.groupby("stationID")["line"].transform("count")
lm2["flow"] = lm2["stationID"].map(st) / lm2["n_lines"]
line_flow = lm2.groupby("line")["flow"].sum().sort_index()

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), gridspec_kw={"width_ratios": [1.1, 1]})

ax = axes[0]
b = ax.bar(line_flow.index.astype(str), line_flow.values / 1e4, 0.65, color=C_MAIN)
top3 = line_flow.nlargest(3).index
for bb, ln, v in zip(b, line_flow.index, line_flow.values):
    ax.text(bb.get_x() + bb.get_width()/2, v / 1e4, f"{v/1e4:.0f}",
            ha="center", fontsize=11,
            color=C_C if ln in top3 else "black",
            fontweight="bold" if ln in top3 else "normal")
ax.set_xlabel("线路"); ax.set_ylabel("日均客流量(万人次)")
ax.set_title("各线路日均客流(换乘站客流均摊)")

# 右: 代表线路分时曲线(2号线主干/1号线/9号线/16号线郊区)
ax = axes[1]
show = [2, 1, 9, 16]
lm_sel = lm2[lm2.line.isin(show)]
prof_l = prof.merge(lm_sel[["stationID", "line", "n_lines"]], on="stationID")
prof_l["w"] = prof_l["total"] / prof_l["n_lines"]
g = prof_l.groupby(["line", "slot"])["w"].sum().reset_index()
g["hour"] = 6 + g["slot"] / 6.0
for ln, c in zip(show, [C_MAIN, C_ACCENT, C_HBO, C_NHB]):
    s = g[g.line == ln]
    ax.plot(s["hour"], s["w"] / 1e4, lw=2, color=c, label=f"{ln}号线")
ax.set_title("代表线路分时段客流(日均)")
ax.set_xlabel("时刻"); ax.set_ylabel("客流量(万人次/10分钟)")
ax.set_xticks(range(6, 24))
ax.axvspan(7, 9, color=C_C, alpha=0.06); ax.axvspan(17, 19, color=C_HBO, alpha=0.06)
ax.legend()

fig.suptitle("线路客流对比", fontsize=17, fontweight="bold")
fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.text(0.99, 0.005, "数据来源: MetroFlow 进出站客流 × 站点线路对照表 | 分工4",
         ha="right", fontsize=10, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-11 线路客流对比.png"))
