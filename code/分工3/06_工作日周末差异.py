# -*- coding: utf-8 -*-
"""分工3 · 工作日与周末客流差异图
输出: 分工3_空间可视化/图片/图3-3 工作日周末客流差异图.png
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

# 从RdBu截取0.1~0.9范围：中蓝→白→中红，去掉最深的两端
_rdbu = plt.get_cmap("RdBu_r", 256)
_colors = [_rdbu(i) for i in np.linspace(0.1, 0.9, 256)]
CMAP_DIFF = LinearSegmentedColormap.from_list("RdBu_mid", _colors)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "图片"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "图3-3 工作日周末客流差异图.png"

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

station_geo["flow_diff"] = station_geo["工作日日均"] - station_geo["周末日均"]

# 分位数点大小
diff_abs = station_geo["flow_diff"].abs().values
p95 = np.percentile(diff_abs, 95)
size_clipped = np.clip(diff_abs, None, p95)
markersize = 15 + (size_clipped / p95) * 250

# 对称色阶
vmax_abs = np.percentile(station_geo["flow_diff"].abs(), 95)

fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
ax.set_facecolor("white")
districts.boundary.plot(ax=ax, color="#cccccc", linewidth=0.6, zorder=1)
# 地铁线路（提高可见度）
for _, line in metro_lines.iterrows():
    line_color = line["color"] if line["color"] else "#999999"
    gpd.GeoSeries([line.geometry]).plot(ax=ax, color=line_color, linewidth=1.3, alpha=0.7, zorder=2)
station_geo.plot(
    ax=ax, column="flow_diff", cmap=CMAP_DIFF,
    markersize=markersize, alpha=0.85,
    vmin=-vmax_abs, vmax=vmax_abs,
    legend=True, legend_kwds={"shrink": 0.6, "label": "客流差值（工作日 − 周末，人次/日）"},
    zorder=3
)

ax.set_title("上海地铁工作日与周末客流空间差异图", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUT_FILE, bbox_inches="tight", facecolor="white")
plt.close()
print(f"已保存: {OUT_FILE}")
