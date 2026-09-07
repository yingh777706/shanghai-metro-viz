# -*- coding: utf-8 -*-
"""21_天气客流影响: 雨天vs晴天客流对比 + 气温-客流关系"""
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
w = load_weather()
w["date"] = w["date"].astype(str)

# 按日聚合天气: 运营时段(6-23点)降雨量合计/平均气温
w6 = w[(w.hour >= 6) & (w.hour < 23)]
wdaily = w6.groupby("date").agg(rain_sum=("rain", "sum"),
                                rain_hours=("rain", lambda s: (s > 0).sum()),
                                temp_mean=("temperature_2m", "mean")).reset_index()
daily = df.groupby(["date", "isWorkday"])["total"].sum().reset_index()
m = daily.merge(wdaily, on="date")

work = m[m.isWorkday == 1].copy()
work["rainy"] = work["rain_hours"] >= 3   # 运营时段>=3小时有雨 记为雨天

fig, axes = plt.subplots(1, 2, figsize=(10.12, 4.35))

# 左: 雨天vs晴天 工作日客流
ax = axes[0]
grp = work.groupby("rainy")["total"]
vals = [grp.get_group(False) / 1e4, grp.get_group(True) / 1e4]
bp = ax.boxplot(vals, tick_labels=[f"晴天\n({len(vals[0])}天)", f"雨天\n({len(vals[1])}天)"],
                patch_artist=True, widths=0.45)
for patch, c in zip(bp["boxes"], [C_MAIN, "#17becf"]):
    patch.set_facecolor(c); patch.set_alpha(0.75)
for i, v in enumerate(vals):
    ax.text(i + 1, v.median(), f"中位 {v.median():.0f}万", ha="center", va="bottom", fontsize=12)
ax.set_ylabel("工作日全网日客流(万人次)")
ax.set_title("雨天 vs 晴天: 工作日客流")

# 右: 平均气温 vs 工作日客流散点
ax = axes[1]
sc = ax.scatter(work["temp_mean"], work["total"] / 1e4,
                c=work["rain_sum"], cmap="Blues", s=45, edgecolor="white", lw=0.5)
z = np.polyfit(work["temp_mean"], work["total"] / 1e4, 1)
xs = np.linspace(work.temp_mean.min(), work.temp_mean.max(), 50)
ax.plot(xs, np.polyval(z, xs), color=C_C, ls="--", lw=1.5,
        label=f"线性趋势(斜率 {z[0]:.1f} 万/°C)")
cb = fig.colorbar(sc, ax=ax); cb.set_label("日降雨量(mm)")
ax.set_xlabel("运营时段平均气温(°C)"); ax.set_ylabel("工作日全网日客流(万人次)")
ax.set_title("气温与客流的关系(工作日)")
ax.legend(loc="lower right")

fig.suptitle("天气对地铁客流的影响", fontsize=17, fontweight="bold")
fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.text(0.99, 0.005, "数据来源: MetroFlow 进出站客流 × 逐小时天气 | 分工4",
         ha="right", fontsize=10, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-13 天气客流影响.png"))
