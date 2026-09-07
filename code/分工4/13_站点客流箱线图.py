# -*- coding: utf-8 -*-
"""13_站点客流箱线图: 站点日均客流分布(按分工5聚类站点类型分组)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_style import *
import pandas as pd

apply_style()
OUT = os.path.join(project_root(), "分工4_统计可视化", "图片")
os.makedirs(OUT, exist_ok=True)

df = drop_abnormal_days(load_inout())
info = load_station_info()

# 站点日均客流
daily_st = df.groupby(["stationID", "date"])["total"].sum().reset_index()
st_avg = daily_st.groupby("stationID")["total"].mean().rename("avg")
st_days = daily_st.groupby("stationID")["total"].apply(list)

# 分工5聚类标签(可选)
clus_path = os.path.join(project_root(), "code", "数据挖掘", "输出结果", "聚类", "表2_聚类结果表.csv")
use_cluster = os.path.exists(clus_path)

fig, ax = plt.subplots(figsize=(11, 6))
if use_cluster:
    cl = pd.read_csv(clus_path)
    cl.columns = [c.strip() for c in cl.columns]
    label_col = "站点类型" if "站点类型" in cl.columns else \
        [c for c in cl.columns if "类型" in c or "label" in c.lower() or "类" in c][0]
    id_col = "stationID" if "stationID" in cl.columns else \
        [c for c in cl.columns if "station" in c.lower() or "站点" in c][0]
    merged = pd.merge(st_avg.reset_index(), cl[[id_col, label_col]],
                      left_on="stationID", right_on=id_col)
    groups = merged.groupby(label_col)["avg"].apply(list)
    groups = groups.loc[groups.apply(np.mean).sort_values(ascending=False).index]
    data, labels = list(groups.values), list(groups.index)
else:
    data, labels = [st_avg.values], ["全部站点"]

bp = ax.boxplot(data, labels=labels, showfliers=True, patch_artist=True,
                flierprops=dict(marker="o", ms=3, alpha=0.4))
for patch, c in zip(bp["boxes"], PALETTE):
    patch.set_facecolor(c); patch.set_alpha(0.75)
ax.set_ylabel("站点日均客流量(人次)")
ttl = "站点日均客流分布箱线图(按站点类型分组)" if use_cluster else "站点日均客流分布箱线图"
ax.set_title(ttl)
plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
fig.text(0.99, 0.01, "数据来源: MetroFlow 刷卡数据集 + 分工5聚类结果 | 分工4",
         ha="right", fontsize=8, color=C_GRAY)
savefig(fig, os.path.join(OUT, "图4-5 站点客流箱线图.png"))
