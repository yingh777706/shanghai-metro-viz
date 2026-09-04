import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

station_flow = pd.read_csv("station_flow_agg.csv")

# 转为空间点数据（WGS84坐标系）
geometry = [Point(xy) for xy in zip(station_flow["lon"], station_flow["lat"])]
station_geo = gpd.GeoDataFrame(station_flow, geometry=geometry, crs="EPSG:4326")

station_geo.to_file("station_flow_geo.geojson", driver="GeoJSON", encoding="utf-8")
print("站点空间数据构建完成，共", len(station_geo), "个站点")
