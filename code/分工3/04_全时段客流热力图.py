# -*- coding: utf-8 -*-
"""分工3 · 全时段站点客流热力图（参考图风格）
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
import numpy as np

# 参考图风格：YlOrRd（浅黄→橙→红→深红）
CMAP_FLOW = "YlOrRd"
BG_COLOR = "#d6e4f0"  # 浅蓝底图
LINE_COLOR = "#777777"  # 深灰地铁线路

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

# 读取上海行政区边界
dist_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "shanghai_districts.geojson"
districts = gpd.read_file(dist_path).to_crs(epsg=3857)

# 读取上海地铁线路
metro_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "shanghai_metro_lines.geojson"
metro_lines = gpd.read_file(metro_path).to_crs(epsg=3857)

fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
ax.set_facecolor(BG_COLOR)

# 绘制行政区边界
districts.boundary.plot(ax=ax, color="#888888", linewidth=0.7, zorder=1)

# 绘制地铁线路（深灰色，参考图风格）
for _, line in metro_lines.iterrows():
    gpd.GeoSeries([line.geometry]).plot(ax=ax, color=LINE_COLOR, linewidth=1.0, alpha=0.8, zorder=2)

# 绘制站点（固定大小，带黑色描边，YlOrRd配色）
station_geo.plot(
    ax=ax, column="全天总客流", cmap=CMAP_FLOW,
    markersize=45, alpha=0.9,
    edgecolor="#333333", linewidth=0.5,
    legend=True, legend_kwds={"shrink": 0.6, "label": "全天客流量（人次）"},
    zorder=3
)

# 标注TOP5站点（拉远标注，加细引线，不挡站点）
top5 = station_geo.sort_values("全天总客流", ascending=False).head(5)
city_center = station_geo.geometry.union_all().centroid
cx, cy = city_center.x, city_center.y
offset_dist = 22000  # 偏移距离（米）
for _, row in top5.iterrows():
    sx, sy = row.geometry.x, row.geometry.y
    angle = np.arctan2(sy - cy, sx - cx)
    tx = sx + offset_dist * np.cos(angle)
    ty = sy + offset_dist * np.sin(angle)
    ax.annotate(row["name"], xy=(sx, sy), xytext=(tx, ty),
                fontsize=10, fontweight="bold", zorder=4, color="#222222",
                arrowprops=dict(arrowstyle="-", color="#555555", lw=0.8),
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9, edgecolor="none"))

ax.set_title("上海地铁全时段站点客流分布图（2017年5–8月）", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUT_FILE, bbox_inches="tight", facecolor=BG_COLOR)
plt.close()
print(f"已保存: {OUT_FILE}")
