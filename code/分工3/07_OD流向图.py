# -*- coding: utf-8 -*-
"""分工3 · 全时段TOP50 OD客流流向图
输出: 分工3_空间可视化/图片/图3-4 全时段OD客流流向图.png
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.collections import LineCollection
import numpy as np
from pyproj import Transformer

CMAP_FLOW = "YlOrRd"
AMAP_URL = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "图片"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "图3-4 全时段OD客流流向图.png"

# 读取OD数据
od_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "od_flow_agg.csv"
if not od_path.exists():
    od_path = find_data("od_flow_agg.csv")
od = pd.read_csv(od_path)

geo_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "station_flow_geo.geojson"
if not geo_path.exists():
    geo_path = find_data("station_flow_geo.geojson")
station_geo = gpd.read_file(geo_path).to_crs(epsg=3857)

trans = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

def generate_arc(o_lon, o_lat, d_lon, d_lat, num=50):
    ox, oy = trans.transform(o_lon, o_lat)
    dx, dy = trans.transform(d_lon, d_lat)
    mx, my = (ox + dx) / 2, (oy + dy) / 2
    dist = np.sqrt((dx - ox) ** 2 + (dy - oy) ** 2)
    if dist == 0:
        return np.column_stack([[ox, dx], [oy, dy]])
    perp_x = -(dy - oy) / dist * dist * 0.2
    perp_y = (dx - ox) / dist * dist * 0.2
    cx, cy = mx + perp_x, my + perp_y
    t = np.linspace(0, 1, num)
    x = (1 - t) ** 2 * ox + 2 * (1 - t) * t * cx + t ** 2 * dx
    y = (1 - t) ** 2 * oy + 2 * (1 - t) * t * cy + t ** 2 * dy
    return np.column_stack([x, y])

arcs = [generate_arc(r.o_lon, r.o_lat, r.d_lon, r.d_lat) for _, r in od.iterrows()]

# 分位数线宽
flow_vals = od["Flow"].values
p95 = np.percentile(flow_vals, 95)
linewidths = 1 + (np.clip(flow_vals, None, p95) / p95) * 8

fig, ax = plt.subplots(figsize=(16, 13), dpi=300)
lc = LineCollection(arcs, cmap=CMAP_FLOW, alpha=0.7)
lc.set_array(flow_vals)
lc.set_linewidths(linewidths)
ax.add_collection(lc)

station_geo.plot(ax=ax, color="#333333", markersize=12, zorder=5)
ctx.add_basemap(ax, source=AMAP_URL, zoom=11)
ax.autoscale()

cbar = plt.colorbar(lc, ax=ax, shrink=0.6)
cbar.set_label("OD客流量（人次）", fontsize=12)

ax.set_title("上海地铁全时段TOP50 OD客流流向图", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUT_FILE, bbox_inches="tight")
plt.close()
print(f"已保存: {OUT_FILE}")
