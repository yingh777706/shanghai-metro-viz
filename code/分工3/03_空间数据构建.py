# -*- coding: utf-8 -*-
"""分工3 · 站点空间数据构建
将站点客流CSV转为带geometry的GeoJSON，供后续可视化脚本使用。
输出: 分工3_空间可视化/空间数据/station_flow_geo.geojson
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "空间数据"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "station_flow_geo.geojson"

# 优先读聚合后的CSV（在分工3交付目录内），其次走 find_data
csv_path = OUT_DIR / "station_flow_agg.csv"
if not csv_path.exists():
    csv_path = find_data("station_flow_agg.csv")

print(f"读取站点客流: {csv_path}")
station_flow = pd.read_csv(csv_path)

geometry = [Point(xy) for xy in zip(station_flow["lon"], station_flow["lat"])]
station_geo = gpd.GeoDataFrame(station_flow, geometry=geometry, crs="EPSG:4326")
station_geo.to_file(OUT_FILE, driver="GeoJSON", encoding="utf-8")
print(f"空间数据构建完成: {OUT_FILE} ({len(station_geo)} 站)")
