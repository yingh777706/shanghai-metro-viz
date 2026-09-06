# -*- coding: utf-8 -*-
"""18_换乘次数分布图: 乘客平均换乘次数/直达比例(OD客流加权)
   复用 17 生成的 od_flow_agg.csv 缓存; 不存在则自动分块聚合"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_style import *
import pandas as pd
import numpy as np

apply_style()
OUT = os.path.join(project_root(), "分工4_统计可视化", "图片")
os.makedirs(OUT, exist_ok=True)

cache = os.path.join(os.path.dirname(load_od()), "od_flow_agg.csv")
if os.path.exists(cache):
    flow = pd.read_csv(cache)
else:  # 与17相同的聚合逻辑
    acc = {}
    for chunk in pd.read_csv(load_od(), chunksize=2_000_000,
                             usecols=["originStation", "destinationStation", "Flow"],
                             skipinitialspace=True):
        chunk = chunk[chunk.originStation != chunk.destinationStation]
        g = chunk.groupby(["originStation", "destinationStation"])["Flow"].sum()
        for k, v in g.items():
            acc[k] = acc.get(k, 0) + v
    flow = pd.Series(acc).rename("Flow").reset_index()
    flow.columns = ["originStation", "destinationStation", "Flow"]
    flow.to_csv(cache, index=False)

tt = load_od_travel_time()
m = flow.merge(tt, on=["originStation", "destinationStation"], how="inner")

by_nt = m.groupby("n_transfers")["Flow"].sum()
share = by_nt / by_nt.sum() * 100
avg_nt = (m["n_transfers"] * m["Flow"]).sum() / m["Flow"].sum()
direct = share.get(0, 0)

fig, ax = plt.subplots(figsize=(10, 6))
colors = [PALETTE[i] for i in range(len(share))]
b = ax.bar(share.index.astype(str), share.values, 0.6, color=colors)
for bb, v in zip(b, share.values):
    ax.text(bb.get_x() + bb.get_width()/2, v + 0.3, f"{v:.1f}%", ha="center", fontsize=11)
ax.set_xlabel("换乘次数(次)"); ax.set_ylabel("客流占比(%)")
ax.set_title("乘客换乘次数分布(OD客流加权)")
ax.text(0.98, 0.92, f"客流加权平均换乘 {avg_nt:.2f} 次\n无需换乘(同线直达)客流占 {direct:.1f}%",
        transform=ax.transAxes, ha="right", fontsize=11,
        bbox=dict(boxstyle="round,pad=0.4", fc="#f5f5f5", ec=C_GRAY, lw=0.5))
fig.text(0.99, 0.01, "数据来源: MetroFlow OD客流 × OD时长估计表 | 分工4",
         ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-10 换乘次数分布.png"))
print(f"平均换乘{avg_nt:.2f}次, 直达占比{direct:.1f}%")
