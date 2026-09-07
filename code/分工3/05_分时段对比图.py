# -*- coding: utf-8 -*-
"""分工3 · 分时段客流空间对比图（参考图风格）
输出: 分工3_空间可视化/图片/图3-2 分时段客流空间对比图.png
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
import numpy as np

# 参考图风格
CMAP_FLOW = "YlOrRd"
BG_COLOR = "#d6e4f0"
LINE_COLOR = "#777777"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "图片"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "图3-2 分时段客流空间对比图.png"

geo_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "station_flow_geo.geojson"
if not geo_path.exists():
    geo_path = find_data("station_flow_geo.geojson")
station_geo = gpd.read_file(geo_path).to_crs(epsg=3857)

dist_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "shanghai_districts.geojson"
districts = gpd.read_file(dist_path).to_crs(epsg=3857)

metro_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "shanghai_metro_lines.geojson"
metro_lines = gpd.read_file(metro_path).to_crs(epsg=3857)

periods = [
    ("早高峰客流", "早高峰 (7:00–9:00)"),
    ("晚高峰客流", "晚高峰 (17:00–19:00)"),
    ("工作日日均", "工作日日均"),
    ("周末日均", "周末日均"),
]

vmax = station_geo["早高峰客流"].max()

fig, axes = plt.subplots(2, 2, figsize=(20, 15), dpi=300)
axes = axes.flatten()

for i, (col, title) in enumerate(periods):
    ax = axes[i]
    ax.set_facecolor(BG_COLOR)
    districts.boundary.plot(ax=ax, color="#888888", linewidth=0.5, zorder=1)
    # 地铁线路（深灰色）
    for _, line in metro_lines.iterrows():
        gpd.GeoSeries([line.geometry]).plot(ax=ax, color=LINE_COLOR, linewidth=0.9, alpha=0.75, zorder=2)
    # 站点（固定大小，带黑色描边）
    station_geo.plot(ax=ax, column=col, cmap=CMAP_FLOW, markersize=35, alpha=0.9,
                      edgecolor="#333333", linewidth=0.4, vmin=0, vmax=vmax, zorder=3)
    ax.set_title(title, fontsize=14)
    ax.set_axis_off()

plt.suptitle("上海地铁分时段客流空间分布对比", fontsize=18, y=0.96)

# 手动布局：右侧留空间给colorbar
fig.subplots_adjust(left=0.02, right=0.88, top=0.92, bottom=0.02, wspace=0.05, hspace=0.05)

# 共享颜色条
cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
sm = ScalarMappable(cmap=CMAP_FLOW, norm=plt.Normalize(vmin=0, vmax=vmax))
sm.set_array([])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label("客流量（人次）", fontsize=12)

plt.savefig(OUT_FILE, bbox_inches="tight", facecolor=BG_COLOR)
plt.close()
print(f"已保存: {OUT_FILE}")
