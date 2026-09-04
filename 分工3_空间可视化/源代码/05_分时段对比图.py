import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import contextily as ctx

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

station_geo = gpd.read_file("station_flow_geo.geojson").to_crs(epsg=3857)

periods = [
    ("早高峰客流", "Morning Peak (7:00-9:00)"),
    ("晚高峰客流", "Evening Peak (17:00-19:00)"),
    ("工作日日均", "Workday Daily Average"),
    ("周末日均", "Weekend Daily Average")
]

fig, axes = plt.subplots(2, 2, figsize=(20, 16), dpi=300)
axes = axes.flatten()
vmax = station_geo["早高峰客流"].max()

for i, (col, title) in enumerate(periods):
    ax = axes[i]
    station_geo.plot(
        ax=ax, column=col, cmap="YlOrRd",
        markersize=station_geo[col]/3000, alpha=0.8, vmin=0, vmax=vmax
    )
    amap_url = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
    ctx.add_basemap(ax, source=amap_url, zoom=11)
    ax.set_title(title, fontsize=14)
    ax.set_axis_off()

plt.suptitle("Shanghai Metro Passenger Flow Spatial Distribution by Time Period", fontsize=18, y=0.95)
plt.tight_layout()
plt.savefig("图3-2 分时段客流空间对比图.png", bbox_inches="tight")
plt.close()
print("分时段对比图已生成")
