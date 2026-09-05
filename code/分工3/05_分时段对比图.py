# -*- coding: utf-8 -*-
"""分工3 · 分时段客流空间对比图（四宫格）
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
import contextily as ctx
import numpy as np

CMAP_FLOW = "YlOrRd"
AMAP_URL = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "图片"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "图3-2 分时段客流空间对比图.png"

geo_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "station_flow_geo.geojson"
if not geo_path.exists():
    geo_path = find_data("station_flow_geo.geojson")
station_geo = gpd.read_file(geo_path).to_crs(epsg=3857)

periods = [
    ("早高峰客流", "早高峰（7:00–9:00）"),
    ("晚高峰客流", "晚高峰（17:00–19:00）"),
    ("工作日日均", "工作日日均"),
    ("周末日均", "周末日均"),
]

# 统一色阶 + 分位数点大小
vmax = station_geo["早高峰客流"].max()
flow_all = station_geo["早高峰客流"].values
p95 = np.percentile(flow_all, 95)

fig, axes = plt.subplots(2, 2, figsize=(18, 15), dpi=300)
axes = axes.flatten()

for i, (col, title) in enumerate(periods):
    ax = axes[i]
    vals = station_geo[col].values
    size_clipped = np.clip(vals, None, np.percentile(vals, 95))
    ms = 15 + (size_clipped / np.percentile(vals, 95)) * 200
    station_geo.plot(ax=ax, column=col, cmap=CMAP_FLOW, markersize=ms, alpha=0.8, vmin=0, vmax=vmax)
    ctx.add_basemap(ax, source=AMAP_URL, zoom=11)
    ax.set_title(title, fontsize=14)
    ax.set_axis_off()

plt.suptitle("上海地铁分时段客流空间分布对比", fontsize=18, y=0.96)
plt.tight_layout()
plt.savefig(OUT_FILE, bbox_inches="tight")
plt.close()
print(f"已保存: {OUT_FILE}")
