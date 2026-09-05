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
import contextily as ctx
import numpy as np

CMAP_DIFF = "RdBu_r"  # 复用分工4差异配色
AMAP_URL = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "图片"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "图3-3 工作日周末客流差异图.png"

geo_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "station_flow_geo.geojson"
if not geo_path.exists():
    geo_path = find_data("station_flow_geo.geojson")
station_geo = gpd.read_file(geo_path).to_crs(epsg=3857)

station_geo["flow_diff"] = station_geo["工作日日均"] - station_geo["周末日均"]

# 分位数点大小
diff_abs = station_geo["flow_diff"].abs().values
p95 = np.percentile(diff_abs, 95)
size_clipped = np.clip(diff_abs, None, p95)
markersize = 15 + (size_clipped / p95) * 250

# 对称色阶
vmax_abs = np.percentile(station_geo["flow_diff"].abs(), 95)

fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
station_geo.plot(
    ax=ax, column="flow_diff", cmap=CMAP_DIFF,
    markersize=markersize, alpha=0.8,
    vmin=-vmax_abs, vmax=vmax_abs,
    legend=True, legend_kwds={"shrink": 0.6, "label": "客流差值（工作日 − 周末，人次/日）"}
)
ctx.add_basemap(ax, source=AMAP_URL, zoom=11)

ax.set_title("上海地铁工作日与周末客流空间差异图", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUT_FILE, bbox_inches="tight")
plt.close()
print(f"已保存: {OUT_FILE}")
