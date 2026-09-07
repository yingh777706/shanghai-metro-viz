# -*- coding: utf-8 -*-
"""09_客流时间序列图: 2017-05~08 全网日客流总量时间序列(区分工作日/周末/节假日)"""
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

daily = df.groupby(["date", "isWorkday"], as_index=False)["total"].sum()
daily["dt"] = pd.to_datetime(daily["date"])
daily = daily.sort_values("dt")

fig, ax = plt.subplots(figsize=(13, 6))
wk = daily[daily.isWorkday == 1]; we = daily[daily.isWorkday == 0]
ax.plot(daily["dt"], daily["total"] / 1e4, color=C_GRAY, lw=1, alpha=0.5, zorder=1)
ax.scatter(wk["dt"], wk["total"] / 1e4, s=16, color=C_MAIN, label="工作日", zorder=2)
ax.scatter(we["dt"], we["total"] / 1e4, s=16, color=C_ACCENT, label="周末/节假日", zorder=2)
# 工作日均值参考线
ax.axhline(wk["total"].mean() / 1e4, color=C_MAIN, ls="--", lw=1,
           label=f"工作日均值 {wk['total'].mean()/1e4:.0f} 万")
ax.set_title("上海地铁全网日客流量时间序列(2017-05-01 ~ 2017-08-31)")
ax.set_xlabel("日期"); ax.set_ylabel("日客流量(万人次·进出站合计)")
# 标注源数据异常日
abn = daily[daily["date"].isin(ABNORMAL_DATES)]
if len(abn):
    ax.scatter(abn["dt"], abn["total"] / 1e4, s=40, facecolor="none",
               edgecolor=C_C, lw=1.5, label="源数据异常日(记录缺失)", zorder=3)
ax.legend(loc="lower right", ncol=2)
fig.text(0.99, 0.01, "数据来源: MetroFlow 刷卡数据集 | 分工4", ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-1 全网日客流时间序列图.png"))
