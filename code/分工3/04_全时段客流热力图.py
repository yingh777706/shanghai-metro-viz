# -*- coding: utf-8 -*-
"""分工3 · 全时段站点客流热力图
输出: 分工3_空间可视化/图片/图3-1 全时段站点客流热力图.png
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

# 自定义深蓝→深紫→深红深色渐变（全程无浅色）
CMAP_FLOW = LinearSegmentedColormap.from_list(
    "blue_red_dark",
    ["#053061", "#2166ac", "#40004b", "#b2182b", "#67001f"],
    N=256
)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "图片"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "图3-1 全时段站点客流热力图.png"

# 读取空间数据
geo_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "station_flow_geo.geojson"
if not geo_path.exists():
    geo_path = find_data("station_flow_geo.geojson")
station_geo = gpd.read_file(geo_path).to_crs(epsg=3857)

# 读取上海行政区边界（简洁底图：白色背景+灰色边界）
dist_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "shanghai_districts.geojson"
districts = gpd.read_file(dist_path).to_crs(epsg=3857)

# 读取上海地铁线路
metro_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "shanghai_metro_lines.geojson"
metro_lines = gpd.read_file(metro_path).to_crs(epsg=3857)

# 分位数映射点大小（避免魔法数字，极值裁剪到95分位）
flow = station_geo["全天总客流"].values
p95 = np.percentile(flow, 95)
size_clipped = np.clip(flow, None, p95)
markersize = 2 + (size_clipped / p95) * 33  # 2~35范围，缩小避免重叠

fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
ax.set_facecolor("white")

# 绘制行政区边界（简洁底图）
districts.boundary.plot(ax=ax, color="#cccccc", linewidth=0.6, zorder=1)

# 绘制地铁线路（官方颜色，中等线宽，较高可见度）
for _, line in metro_lines.iterrows():
    line_color = line["color"] if line["color"] else "#999999"
    gpd.GeoSeries([line.geometry]).plot(ax=ax, color=line_color, linewidth=1.3, alpha=0.65, zorder=2)

station_geo.plot(
    ax=ax, column="全天总客流", cmap=CMAP_FLOW,
    markersize=markersize, alpha=0.8,
    legend=True, legend_kwds={"shrink": 0.6, "label": "全天客流量（人次）"},
    zorder=3
)

# 标注TOP5站点（避免重叠）
top5 = station_geo.sort_values("全天总客流", ascending=False).head(5)
for _, row in top5.iterrows():
    ax.text(row.geometry.x, row.geometry.y, row["name"], fontsize=10, ha="left", va="bottom",
            fontweight="bold", zorder=4,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"))

ax.set_title("上海地铁全时段站点客流分布图（2017年5–8月）", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUT_FILE, bbox_inches="tight", facecolor="white")
plt.close()
print(f"已保存: {OUT_FILE}")
