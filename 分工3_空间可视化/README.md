# 分工3：地铁客流空间地图可视化

## 分工说明

- **成员**：lks（吕可珊）[@kaishuiliang](https://github.com/kaishuiliang)
- **方向**：空间可视化
- **核心职责**：站点线路底图构建、客流热力图、OD流向图、动态交互可视化

## 目录结构

```
code/分工3/                    # 可视化脚本（01~08）
├── 01_站点客流聚合.py          # 从10分钟粒度数据聚合站点多维客流
├── 02_OD客流聚合.py            # 聚合TOP50 OD客流对
├── 03_空间数据构建.py          # CSV → GeoJSON
├── 04_全时段客流热力图.py       # 图3-1
├── 05_分时段对比图.py          # 图3-2（四宫格）
├── 06_工作日周末差异.py        # 图3-3
├── 07_OD流向图.py             # 图3-4
└── 08_交互地图.py             # Folium交互HTML

分工3_空间可视化/              # 交付物（运行即输出到此目录）
├── 图片/                      # 4张300DPI高清PNG
├── 交互地图/                  # Folium HTML
├── 空间数据/                  # GeoJSON + 聚合CSV
└── README.md                  # 本文件
```

## 成果说明

### 静态图片

| 文件名 | 说明 |
|--------|------|
| 图3-1 全时段站点客流热力图.png | 302个站点全天总客流空间分布，点大小+颜色双编码，标注TOP10核心站点 |
| 图3-2 分时段客流空间对比图.png | 早高峰/晚高峰/工作日日均/周末日均四宫格对比，统一色阶便于横向比较 |
| 图3-3 工作日周末客流差异图.png | 双向色阶差值图（工作日−周末），红色=通勤主导站，蓝色=休闲主导站 |
| 图3-4 全时段OD客流流向图.png | TOP50客流对的贝塞尔弧线图，弧线粗细对应客流量级，展示城市主要通勤走廊 |

### 交互地图

`上海地铁客流交互地图.html`：基于Folium构建的可交互网页，双击即可在浏览器打开。支持地图缩放拖拽，点击任意站点可弹出该站全天、早高峰、晚高峰、工作日日均、周末日均的详细客流数据（中文popup）。

### 空间数据

`station_flow_geo.geojson`：带客流属性的站点空间数据（WGS84坐标系），包含站点ID、名称、经纬度、全天总客流、早高峰客流、晚高峰客流、工作日日均、周末日均等字段，可直接用于QGIS、Kepler.gl等GIS工具。

## 数据来源

本分工的可视化基于分工1（数据工程）预处理后的聚合数据：
- `station_flow_agg.csv`：站点级多维度客流聚合表
- `od_flow_agg.csv`：TOP50 OD客流对聚合表

> 注：CSV数据文件因体积较大，按仓库 `.gitignore` 规则不纳入版本控制。如需原始聚合数据，请联系分工1成员获取，或运行 `code/分工3/01_站点客流聚合.py` 和 `02_OD客流聚合.py` 基于 `processed_data` 中的10分钟粒度原始数据重新生成。

## 运行环境

- Python 3.10+
- 依赖库：pandas、geopandas、matplotlib、contextily、pyproj、shapely、folium、numpy

```bash
pip install pandas geopandas matplotlib contextily pyproj shapely folium numpy
```

## 运行步骤

1. 将数据放入 `data/` 或 `processed_data/` 目录（或设置环境变量 `METRO_DATA_DIR` 指向数据目录）
2. 在仓库根目录依次运行：
   ```bash
   python code/分工3/01_站点客流聚合.py      # 生成 station_flow_agg.csv
   python code/分工3/02_OD客流聚合.py        # 生成 od_flow_agg.csv
   python code/分工3/03_空间数据构建.py      # 生成 station_flow_geo.geojson
   python code/分工3/04_全时段客流热力图.py   # 生成图3-1
   python code/分工3/05_分时段对比图.py       # 生成图3-2
   python code/分工3/06_工作日周末差异.py     # 生成图3-3
   python code/分工3/07_OD流向图.py           # 生成图3-4
   python code/分工3/08_交互地图.py           # 生成交互HTML
   ```
3. 所有输出自动写入 `分工3_空间可视化/` 对应子目录

## 技术要点

- **路径规范**：所有脚本通过 `common.find_data()` 定位数据文件，输出基于 `common.PROJECT_ROOT`，禁止硬编码绝对路径
- **底图**：使用高德地图浅色瓦片（自带地铁线路标注），通过 `contextily` 叠加
- **坐标系**：原始数据 WGS84 (EPSG:4326)，叠加底图时自动转换为 Web墨卡托 (EPSG:3857)
- **OD弧线**：使用二次贝塞尔曲线生成弧线，避免直线重叠，提升可读性
- **点大小映射**：采用95分位数裁剪 + 线性映射，避免极值站点导致其他站点不可见
- **交互地图**：基于 Folium + CartoDB 底图，CircleMarker 编码客流量级，中文 popup + 图例
- **配色**：客流热力图使用 `YlOrRd`，差异对比图使用 `RdBu_r`，与分工4 `viz_style.py` 保持一致
