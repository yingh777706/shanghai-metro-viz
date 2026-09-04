import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.collections import LineCollection
import numpy as np
from pyproj import Transformer

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

od = pd.read_csv("od_flow_agg.csv")
station_geo = gpd.read_file("station_flow_geo.geojson").to_crs(epsg=3857)

# 坐标转换
trans = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

def generate_arc(o_lon, o_lat, d_lon, d_lat, num=50):
    ox, oy = trans.transform(o_lon, o_lat)
    dx, dy = trans.transform(d_lon, d_lat)
    mx, my = (ox+dx)/2, (oy+dy)/2
    dist = np.sqrt((dx-ox)**2 + (dy-oy)**2)
    if dist == 0:
        return np.column_stack([[ox, dx], [oy, dy]])
    perp_x = -(dy-oy) / dist * dist * 0.2
    perp_y = (dx-ox) / dist * dist * 0.2
    cx, cy = mx + perp_x, my + perp_y
    t = np.linspace(0, 1, num)
    x = (1-t)**2 * ox + 2*(1-t)*t * cx + t**2 * dx
    y = (1-t)**2 * oy + 2*(1-t)*t * cy + t**2 * dy
    return np.column_stack([x, y])

arcs = [generate_arc(row.o_lon, row.o_lat, row.d_lon, row.d_lat) for _, row in od.iterrows()]

fig, ax = plt.subplots(figsize=(18, 14), dpi=300)

lc = LineCollection(arcs, cmap="YlOrRd", alpha=0.7)
lc.set_array(od["Flow"].values)
lc.set_linewidths(od["Flow"] / 800)
ax.add_collection(lc)

station_geo.plot(ax=ax, color="#333333", markersize=15, zorder=5)
amap_url = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
ctx.add_basemap(ax, source=amap_url, zoom=11)
ax.autoscale()

cbar = plt.colorbar(lc, ax=ax, shrink=0.6)
cbar.set_label("OD Passenger Flow", fontsize=12)

ax.set_title("Shanghai Metro TOP50 OD Passenger Flow Direction Map (All Day)", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig("图3-4 全时段OD客流流向图.png", bbox_inches="tight")
plt.close()
print("OD流向图已生成")
