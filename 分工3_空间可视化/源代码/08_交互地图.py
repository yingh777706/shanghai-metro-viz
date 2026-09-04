import folium
import geopandas as gpd

station_geo = gpd.read_file("station_flow_geo.geojson")

m = folium.Map(location=[31.2304, 121.4737], zoom_start=11, tiles="CartoDB positron")

for _, row in station_geo.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=row["全天总客流"] / 5000,
        popup=f"""
        <b>{row['name']}</b><br>
        Total Flow: {int(row['全天总客流'])}<br>
        Morning Peak: {int(row['早高峰客流'])}<br>
        Evening Peak: {int(row['晚高峰客流'])}
        """,
        color="#c0392b",
        fill=True,
        fill_color="#e74c3c",
        fill_opacity=0.6
    ).add_to(m)

folium.LayerControl().add_to(m)
m.save("上海地铁客流交互地图.html")
print("交互地图已生成")
