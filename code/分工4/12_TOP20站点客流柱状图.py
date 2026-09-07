# -*- coding: utf-8 -*-
"""12_TOP20站点客流柱状图: 全周期总进出站客流TOP20站点(进站/出站堆叠)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_style import *
import pandas as pd
import numpy as np

apply_style()
OUT = os.path.join(project_root(), "分工4_统计可视化", "图片")
os.makedirs(OUT, exist_ok=True)

df = drop_abnormal_days(load_inout())
info = load_station_info()
name_map = dict(zip(info["stationID"], info["name"]))

st = df.groupby("stationID")[["inFlow", "outFlow"]].sum()
st["total"] = st.sum(axis=1)
top = st.sort_values("total", ascending=False).head(20)
top["name"] = top.index.map(name_map)

y = np.arange(len(top))[::-1]
fig, ax = plt.subplots(figsize=(11, 8))
ax.barh(y, top["inFlow"] / 1e4, color=C_MAIN, label="进站客流")
ax.barh(y, top["outFlow"] / 1e4, left=top["inFlow"] / 1e4, color=C_ACCENT, label="出站客流")
for yi, t in zip(y, top["total"] / 1e4):
    ax.text(t + 5, yi, f"{t:.0f}", va="center", fontsize=9)
ax.set_yticks(y); ax.set_yticklabels(top["name"])
ax.set_xlabel("客流量(万人次, 2017-05~08 合计)")
ax.set_title("TOP20 大客流站点(进站/出站构成)")
ax.legend(loc="lower right")
fig.text(0.99, 0.01, "数据来源: MetroFlow 刷卡数据集 | 分工4", ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-4 TOP20站点客流柱状图.png"))
