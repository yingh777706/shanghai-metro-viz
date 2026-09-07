# -*- coding: utf-8 -*-
"""从高德地图公开API获取上海地铁线路数据，生成GeoJSON
输出: 分工3_空间可视化/空间数据/shanghai_metro_lines.geojson
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT

import json
import urllib.request
import geopandas as gpd
from shapely.geometry import LineString

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "空间数据"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "shanghai_metro_lines.geojson"

# 高德地图公开地铁数据API（上海城市代码3100）
url = "https://map.amap.com/service/subway?_=1757280000000&srhdata=3100_drw_shanghai.json"
print(f"正在获取上海地铁线路数据: {url}")

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))

# 解析线路数据
lines = []
for line_data in data.get("l", []):
    line_name = line_data.get("ln", "未知线路")
    line_color = "#" + line_data.get("cl", "888888")
    # 站点序列
    stations = line_data.get("st", [])
    coords = []
    for st in stations:
        # 高德坐标格式: "lon,lat"
        sl = st.get("sl", "")
        if sl:
            parts = sl.split(",")
            if len(parts) == 2:
                lon, lat = float(parts[0]), float(parts[1])
                coords.append((lon, lat))
    
    if len(coords) >= 2:
        lines.append({
            "line_name": line_name,
            "color": line_color,
            "n_stations": len(coords),
            "geometry": LineString(coords)
        })
    print(f"  {line_name}: {len(coords)}站, 颜色{line_color}")

print(f"\n共获取 {len(lines)} 条线路")

# 生成GeoDataFrame并保存
gdf = gpd.GeoDataFrame(lines, geometry="geometry", crs="EPSG:4326")
gdf.to_file(OUT_FILE, driver="GeoJSON", encoding="utf-8")
print(f"已保存: {OUT_FILE}")
