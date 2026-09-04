import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import contextily as ctx

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# 读取数据
station_geo = gpd.read_file("station_flow_geo.geojson").to_crs(epsg=3857)

fig, ax = plt.subplots(figsize=(16, 12), dpi=300)

# 绘制站点客流：大小+颜色双编码映射客流量
station_geo.plot(
    ax=ax,
    column="全天总客流",
    cmap="YlOrRd",
    markersize=station_geo["全天总客流"] / 3000,
    alpha=0.8,
    legend=True,
    legend_kwds={"shrink": 0.6, "label": "Total Passenger Flow"}
)

# 叠加高德浅色底图（自带地铁线路）
amap_url = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
ctx.add_basemap(ax, source=amap_url, zoom=11)

# 标注TOP10站点
top10 = station_geo.sort_values("全天总客流", ascending=False).head(10)
for idx, row in top10.iterrows():
    ax.text(row.geometry.x, row.geometry.y, row["name"], fontsize=9, ha="left", va="bottom")

ax.set_title("Shanghai Metro Station Passenger Flow Distribution (All Day)", fontsize=16, pad=20)
ax.set_axis_off()
plt.tight_layout()
plt.savefig("图3-1 全时段站点客流热力图.png", bbox_inches="tight")
plt.close()
print("全时段热力图已生成")
