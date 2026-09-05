# -*- coding: utf-8 -*-
"""分工3 · 可交互客流地图（Folium）
输出: 分工3_空间可视化/交互地图/上海地铁客流交互地图.html
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import folium
import geopandas as gpd
import numpy as np

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "交互地图"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "上海地铁客流交互地图.html"

geo_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "station_flow_geo.geojson"
if not geo_path.exists():
    geo_path = find_data("station_flow_geo.geojson")
station_geo = gpd.read_file(geo_path)

m = folium.Map(location=[31.2304, 121.4737], zoom_start=11, tiles="CartoDB positron")

# 分位数裁剪半径，避免极值点过大
flow = station_geo["全天总客流"].values
p95 = np.percentile(flow, 95)
p05 = np.percentile(flow, 5)

for _, row in station_geo.iterrows():
    r = np.clip(row["全天总客流"], p05, p95)
    radius = 3 + (r / p95) * 15  # 3~18 范围
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=radius,
        popup=folium.Popup(
            f"<b>{row['name']}</b><br>"
            f"全天客流：{int(row['全天总客流']):,} 人次<br>"
            f"早高峰：{int(row['早高峰客流']):,} 人次<br>"
            f"晚高峰：{int(row['晚高峰客流']):,} 人次<br>"
            f"工作日日均：{int(row['工作日日均']):,} 人次<br>"
            f"周末日均：{int(row['周末日均']):,} 人次",
            max_width=300
        ),
        color="#c0392b",
        fill=True,
        fill_color="#e74c3c",
        fill_opacity=0.6,
    ).add_to(m)

# 图例
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
    background: white; padding: 12px 16px; border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15); font-size: 13px; font-family: sans-serif;">
    <b>图例</b><br>
    <span style="display:inline-block;width:12px;height:12px;border-radius:50%;
        background:#e74c3c;opacity:0.6;border:1px solid #c0392b;"></span>
    站点全天客流量（点大小映射客流规模）
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

folium.LayerControl().add_to(m)
m.save(OUT_FILE)
print(f"已保存: {OUT_FILE}")
