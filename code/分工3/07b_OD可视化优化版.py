# -*- coding: utf-8 -*-
"""分工3 · OD客流可视化（更直观版本）
输出两张图：
  图3-4a OD客流矩阵热力图.png —— TOP12站点×TOP12站点矩阵，无重叠
  图3-4b TOP15 OD简化流向图.png —— 带箭头直线，替代50条贝塞尔弧线
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import FancyArrowPatch
import geopandas as gpd
from pyproj import Transformer

# 从RdBu截取0.1~0.9范围：中蓝→白→中红，去掉最深的两端
_rdbu = plt.get_cmap("RdBu_r", 256)
_colors = [_rdbu(i) for i in np.linspace(0.1, 0.9, 256)]
CMAP_FLOW = LinearSegmentedColormap.from_list("RdBu_mid", _colors)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "图片"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 读取OD数据
od_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "od_flow_agg.csv"
if not od_path.exists():
    od_path = find_data("od_flow_agg.csv")
od = pd.read_csv(od_path)
print(f"读取OD数据: {od_path}, {len(od)}条")

# ============================================================
# 图1: OD矩阵热力图（TOP12站点）
# ============================================================
# 按总客流（起点+终点）取TOP12站点
station_flow = {}
for _, r in od.iterrows():
    station_flow[r["o_name"]] = station_flow.get(r["o_name"], 0) + r["Flow"]
    station_flow[r["d_name"]] = station_flow.get(r["d_name"], 0) + r["Flow"]
top_stations = sorted(station_flow, key=station_flow.get, reverse=True)[:12]
print(f"TOP12站点: {top_stations}")

# 构建矩阵
n = len(top_stations)
matrix = np.zeros((n, n))
for _, r in od.iterrows():
    if r["o_name"] in top_stations and r["d_name"] in top_stations:
        i = top_stations.index(r["o_name"])
        j = top_stations.index(r["d_name"])
        matrix[i][j] = r["Flow"]

fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
im = ax.imshow(matrix, cmap=CMAP_FLOW, aspect="auto")

# 标注数值
for i in range(n):
    for j in range(n):
        if matrix[i][j] > 0:
            val = matrix[i][j]
            color = "white" if val > matrix.max() * 0.5 else "black"
            ax.text(j, i, f"{int(val/10000)}万", ha="center", va="center",
                    fontsize=8, color=color, fontweight="bold")

ax.set_xticks(range(n))
ax.set_yticks(range(n))
ax.set_xticklabels(top_stations, rotation=45, ha="right", fontsize=9)
ax.set_yticklabels(top_stations, fontsize=9)
ax.set_xlabel("终点站点", fontsize=13, fontweight="bold")
ax.set_ylabel("起点站点", fontsize=13, fontweight="bold")
ax.set_title("上海地铁TOP12站点间OD客流矩阵热力图（TOP50 OD对）", fontsize=15, pad=15, fontweight="bold")

cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label("客流量（人次）", fontsize=11)

plt.tight_layout()
out1 = OUT_DIR / "图3-4a OD客流矩阵热力图.png"
plt.savefig(out1, bbox_inches="tight")
plt.close()
print(f"已保存: {out1}")

# ============================================================
# 图2: TOP15简化流向图（带箭头直线）
# ============================================================
geo_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "station_flow_geo.geojson"
if not geo_path.exists():
    geo_path = find_data("station_flow_geo.geojson")
station_geo = gpd.read_file(geo_path).to_crs(epsg=3857)

# 上海行政区边界
dist_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "shanghai_districts.geojson"
districts = gpd.read_file(dist_path).to_crs(epsg=3857)

# 上海地铁线路
metro_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "shanghai_metro_lines.geojson"
metro_lines = gpd.read_file(metro_path).to_crs(epsg=3857)

trans = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

top15 = od.head(15).copy()
fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
ax.set_facecolor("white")
districts.boundary.plot(ax=ax, color="#cccccc", linewidth=0.6, zorder=1)
# 地铁线路
for _, line in metro_lines.iterrows():
    line_color = line["color"] if line["color"] else "#999999"
    gpd.GeoSeries([line.geometry]).plot(ax=ax, color=line_color, linewidth=1.2, alpha=0.55, zorder=2)

# 线宽分位数映射
flow_vals = top15["Flow"].values
p95 = np.percentile(flow_vals, 95)
linewidths = 1.5 + (np.clip(flow_vals, None, p95) / p95) * 7

# OD流向线统一用深红色，线宽映射客流量级
colors = ["#b2182b"] * len(top15)

# 计算市中心（所有站点几何中心），用于标注向外偏移
city_center = station_geo.geometry.unary_union.centroid
cx, cy = city_center.x, city_center.y
offset_dist = 18000  # 标注偏移距离（米，Web墨卡托单位）

for idx, (_, r) in enumerate(top15.iterrows()):
    ox, oy = trans.transform(r["o_lon"], r["o_lat"])
    dx, dy = trans.transform(r["d_lon"], r["d_lat"])
    # 带箭头直线
    arrow = FancyArrowPatch(
        (ox, oy), (dx, dy),
        arrowstyle="-|>", mutation_scale=15,
        linewidth=linewidths[idx],
        color=colors[idx],
        alpha=0.85,
        zorder=3
    )
    ax.add_patch(arrow)
    # 标注起终点名称（拉远标注，加细引线，不挡站点）
    if idx < 8:
        # 起点：沿从市中心向外方向偏移
        angle_o = np.arctan2(oy - cy, ox - cx)
        o_tx = ox + offset_dist * np.cos(angle_o)
        o_ty = oy + offset_dist * np.sin(angle_o)
        ax.annotate(r["o_name"], xy=(ox, oy), xytext=(o_tx, o_ty),
                    fontsize=7, fontweight="bold", zorder=5,
                    arrowprops=dict(arrowstyle="-", color="#888888", lw=0.6),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.85, edgecolor="none"))
        # 终点：沿从市中心向外方向偏移
        angle_d = np.arctan2(dy - cy, dx - cx)
        d_tx = dx + offset_dist * np.cos(angle_d)
        d_ty = dy + offset_dist * np.sin(angle_d)
        ax.annotate(r["d_name"], xy=(dx, dy), xytext=(d_tx, d_ty),
                    fontsize=7, fontweight="bold", zorder=5,
                    arrowprops=dict(arrowstyle="-", color="#888888", lw=0.6),
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.85, edgecolor="none"))

# 绘制站点（颜色映射全天总客流，和其他图风格一致）
station_flow = station_geo["全天总客流"].values
sp95 = np.percentile(station_flow, 95)
sizes_clipped = np.clip(station_flow, None, sp95)
station_markersize = 8 + (sizes_clipped / sp95) * 35
station_plot = station_geo.plot(
    ax=ax, column="全天总客流", cmap=CMAP_FLOW,
    markersize=station_markersize, alpha=0.8, zorder=4,
    vmin=0, vmax=station_flow.max()
)
ax.autoscale()

# 添加站点客流量颜色条
sm_station = ScalarMappable(cmap=CMAP_FLOW, norm=Normalize(vmin=0, vmax=station_flow.max()))
sm_station.set_array([])
cbar = fig.colorbar(sm_station, ax=ax, shrink=0.6, pad=0.02)
cbar.set_label("站点全天客流量（人次）", fontsize=12)

ax.set_title("上海地铁TOP15 OD客流流向图（带箭头，线宽=客流量级）", fontsize=15, pad=15, fontweight="bold")
ax.set_axis_off()
plt.tight_layout()
out2 = OUT_DIR / "图3-4b TOP15 OD简化流向图.png"
plt.savefig(out2, bbox_inches="tight", facecolor="white")
plt.close()
print(f"已保存: {out2}")

print("全部完成！")
