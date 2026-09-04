import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import contextily as ctx

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

station_geo = gpd.read_file("station_flow_geo.geojson").to_crs(epsg=3857)

station_geo["flow_diff"] = station_geo["工作日日均"] - station_geo["周末日均"]

fig, ax = plt.subplots(figsize=(16, 12), dpi=300)

station_geo.plot(
    ax=ax, column="flow_diff", cmap="coolwarm",
    markersize=abs(station_geo["flow_diff"])/2000, alpha=0.8,
    legend=True, legend_kwds={"shrink": 0.6, "label": "Flow Difference (Workday - Weekend)"}
)

amap_url = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
ctx.add_basemap(ax, source=amap_url, zoom=11)
ax.set_title("Shanghai Metro Passenger Flow Difference: Workday vs Weekend", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig("图3-3 工作日周末客流差异图.png", bbox_inches="tight")
plt.close()
print("差异图已生成")
