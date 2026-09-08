# -*- coding: utf-8 -*-
"""分工3 · 可交互客流地图（改进版）
改进点：
  1. 底图改用高德地图瓦片（国内稳定访问）
  2. 站点颜色改用YlOrRd梯度映射（客流越大颜色越深）
  3. 降低不透明度、缩小点，避免叠加成一片
  4. 添加颜色梯度图例
输出: 分工3_空间可视化/交互地图/上海地铁客流交互地图_改进版.html
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import folium
import geopandas as gpd
import numpy as np
import matplotlib
import math
from matplotlib.colors import Normalize

# ========== WGS-84 → GCJ-02 坐标转换（高德底图用GCJ-02） ==========
_A = 6378245.0
_EE = 0.00669342162296594323

def _transform_lat(x, y):
    ret = -100.0 + 2.0*x + 3.0*y + 0.2*y*y + 0.1*x*y + 0.2*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0/3.0
    ret += (20.0*math.sin(y*math.pi) + 40.0*math.sin(y/3.0*math.pi)) * 2.0/3.0
    ret += (160.0*math.sin(y/12.0*math.pi) + 320*math.sin(y*math.pi/30.0)) * 2.0/3.0
    return ret

def _transform_lon(x, y):
    ret = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0/3.0
    ret += (20.0*math.sin(x*math.pi) + 40.0*math.sin(x/3.0*math.pi)) * 2.0/3.0
    ret += (150.0*math.sin(x/12.0*math.pi) + 300.0*math.sin(x/30.0*math.pi)) * 2.0/3.0
    return ret

def wgs84_to_gcj02(lon, lat):
    if lon < 72.004 or lon > 137.8347 or lat < 0.8293 or lat > 55.8271:
        return lon, lat
    dlat = _transform_lat(lon - 105.0, lat - 35.0)
    dlon = _transform_lon(lon - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - _EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((_A * (1 - _EE)) / (magic * sqrtmagic) * math.pi)
    dlon = (dlon * 180.0) / (_A / sqrtmagic * math.cos(radlat) * math.pi)
    return lon + dlon, lat + dlat

OUT_DIR = PROJECT_ROOT / "分工3_空间可视化" / "交互地图"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "上海地铁客流交互地图_改进版.html"

geo_path = PROJECT_ROOT / "分工3_空间可视化" / "空间数据" / "station_flow_geo.geojson"
if not geo_path.exists():
    geo_path = find_data("station_flow_geo.geojson")
station_geo = gpd.read_file(geo_path)

# 高德地图瓦片URL（国内可访问）
AMAP_TILES = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
AMAP_ATTR = "高德地图"

# 地图中心也转成GCJ-02
_center_lon, _center_lat = wgs84_to_gcj02(121.4737, 31.2304)
m = folium.Map(location=[_center_lat, _center_lon], zoom_start=11,
               tiles=AMAP_TILES, attr=AMAP_ATTR)

# 客流量颜色映射（YlOrRd）
flow = station_geo["全天总客流"].values
p95 = np.percentile(flow, 95)
p05 = np.percentile(flow, 5)
norm = Normalize(vmin=p05, vmax=p95)
cmap = matplotlib.colormaps["YlOrRd"]

def flow_to_color(val):
    """客流量 → YlOrRd颜色（hex）"""
    clipped = np.clip(val, p05, p95)
    rgba = cmap(norm(clipped))
    return "#{:02x}{:02x}{:02x}".format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))

# 点大小映射（像素半径，固定大小不随缩放变化，设得很小避免遮盖）
for _, row in station_geo.iterrows():
    r = np.clip(row["全天总客流"], p05, p95)
    radius = 1 + (r / p95) * 4  # 1~5像素（小半径，缩小不遮盖、放大能看清）
    fill_color = flow_to_color(row["全天总客流"])
    # WGS-84 → GCJ-02 坐标转换，对齐高德底图
    gcj_lon, gcj_lat = wgs84_to_gcj02(row.geometry.x, row.geometry.y)
    folium.CircleMarker(
        location=[gcj_lat, gcj_lon],
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
        color="#333333",          # 描边深灰
        weight=0.5,
        fill=True,
        fill_color=fill_color,     # YlOrRd梯度色
        fill_opacity=0.85,         # 不透明度0.85
    ).add_to(m)

# 颜色梯度图例（HTML渐变条）
legend_html = f"""
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
    background: white; padding: 12px 16px; border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15); font-size: 13px; font-family: sans-serif;">
    <b>站点全天客流量</b><br>
    <div style="display: flex; align-items: center; margin-top: 6px;">
        <span style="font-size: 11px; color: #666;">低</span>
        <div style="width: 120px; height: 14px; margin: 0 8px;
            background: linear-gradient(to right,
                {flow_to_color(p05)},
                {flow_to_color((p05+p95)/2)},
                {flow_to_color(p95)});
            border: 1px solid #ccc; border-radius: 2px;"></div>
        <span style="font-size: 11px; color: #666;">高</span>
    </div>
    <div style="font-size: 11px; color: #999; margin-top: 4px;">
        点大小 + 颜色双编码
    </div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

folium.LayerControl().add_to(m)
m.save(OUT_FILE)
print(f"已保存: {OUT_FILE}")
