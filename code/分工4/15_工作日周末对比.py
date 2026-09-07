# -*- coding: utf-8 -*-
"""15_工作日周末对比: 多维对比(日均客流/高峰占比/通勤占比/站点TOP对比)"""
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
info = load_station_info()
name_map = dict(zip(info["stationID"], info["name"]))

ndays = df.groupby("isWorkday")["date"].nunique()

# 指标1: 日均总客流
daily = df.groupby(["isWorkday", "date"])["total"].sum().groupby("isWorkday").mean()
# 指标2: 高峰(7-9,17-19)进站占比
df["peak"] = ((df.hour >= 7) & (df.hour < 9)) | ((df.hour >= 17) & (df.hour < 19))
peak_in = df[df.peak].groupby("isWorkday")["inFlow"].sum()
all_in = df.groupby("isWorkday")["inFlow"].sum()
peak_share = peak_in / all_in * 100
# 指标3: 通勤出行占比(CinFlow占进站)
c_share = df.groupby("isWorkday")["CinFlow"].sum() / all_in * 100
# 指标4: TOP10站点工作日/周末日均对比
st = df.groupby(["isWorkday", "stationID"])["total"].sum()
st = (st / ndays).unstack(0)
top10 = st.sum(axis=1).nlargest(10).index
st10 = st.loc[top10].sort_values(1)
st10.index = [name_map.get(i, str(i)) for i in st10.index]

fig, axes = plt.subplots(2, 2, figsize=(13, 9))
labels = ["工作日", "周末"]; x = np.arange(2); cols = [C_MAIN, C_ACCENT]

ax = axes[0, 0]
vals = np.array([daily.loc[1], daily.loc[0]]) / 1e4
b = ax.bar(x, vals, 0.5, color=cols)
for bb in b: ax.text(bb.get_x()+0.25, bb.get_height(), f"{bb.get_height():.0f}万", ha="center")
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_title("日均全网客流量")
ax.set_ylabel("万人次")

ax = axes[0, 1]
b = ax.bar(x, [peak_share[1], peak_share[0]], 0.5, color=cols)
for bb in b: ax.text(bb.get_x()+0.25, bb.get_height(), f"{bb.get_height():.1f}%", ha="center")
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_title("早晚高峰进站客流占比"); ax.set_ylabel("%")

ax = axes[1, 0]
b = ax.bar(x, [c_share[1], c_share[0]], 0.5, color=cols)
for bb in b: ax.text(bb.get_x()+0.25, bb.get_height(), f"{bb.get_height():.1f}%", ha="center")
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_title("通勤出行(C)占进站客流比例"); ax.set_ylabel("%")

ax = axes[1, 1]
y = np.arange(len(st10)); h = 0.36
ax.barh(y + h/2, st10[1] / 1e4, h, color=C_MAIN, label="工作日日均")
ax.barh(y - h/2, st10[0] / 1e4, h, color=C_ACCENT, label="周末日均")
ax.set_yticks(y); ax.set_yticklabels(st10.index, fontsize=9)
ax.set_xlabel("万人次"); ax.set_title("TOP10站点 工作日/周末日均客流")
ax.legend()

fig.suptitle("工作日 vs 周末 多维对比", fontsize=15, fontweight="bold")
fig.tight_layout(rect=[0, 0.02, 1, 0.96])
fig.text(0.99, 0.005, "数据来源: MetroFlow 刷卡数据集 | 分工4", ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-7 工作日周末多维对比.png"))
