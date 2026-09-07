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
import numpy as np

# 复用分工4统一配色
CMAP_FLOW = "YlOrRd"

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

# 分位数映射点大小（避免魔法数字，极值裁剪到95分位）
flow = station_geo["全天总客流"].values
p95 = np.percentile(flow, 95)
size_clipped = np.clip(flow, None, p95)
markersize = 5 + (size_clipped / p95) * 80  # 5~85 范围，避免重叠糊在一起

fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
ax.set_facecolor("white")

# 绘制行政区边界（简洁底图）
districts.boundary.plot(ax=ax, color="#aaaaaa", linewidth=0.8, zorder=1)

station_geo.plot(
    ax=ax, column="全天总客流", cmap=CMAP_FLOW,
    markersize=markersize, alpha=0.6,
    legend=True, legend_kwds={"shrink": 0.6, "label": "全天客流量（人次）"},
    zorder=2
)

# 标注TOP10站点
top10 = station_geo.sort_values("全天总客流", ascending=False).head(10)
for _, row in top10.iterrows():
    ax.text(row.geometry.x, row.geometry.y, row["name"], fontsize=9, ha="left", va="bottom", zorder=3)

ax.set_title("上海地铁全时段站点客流分布图（2017年5–8月）", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUT_FILE, bbox_inches="tight", facecolor="white")
plt.close()
print(f"已保存: {OUT_FILE}")
