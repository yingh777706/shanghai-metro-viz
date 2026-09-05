# 上海地铁数据可视化

基于 2017 年 5–8 月上海地铁刷卡数据集的客流分析与可视化项目（《软件开发实践1》课程项目）。

## 项目简介

地铁系统在城市出行中的作用日益重要。本项目基于上海地铁刷卡数据集（302 个地铁站、超 7 亿条智能卡刷卡记录，附站点属性与天气等辅助信息），通过数据预处理、统计分析、地图可视化等方式，计算描述性统计特征，分析客流时空规律，可视化呈现乘客出行模式，并可进一步采用聚类、预测等算法进行深度挖掘。

## 数据来源

- 数据集：<https://github.com/Ariza-Sun/MetroFlow>
- 参考论文：Sun P, Yang J, Huang Z, et al. *Human mobility datasets in the complex metro system of Shanghai*. Scientific Data, 2025, 12(1): 1061.

## 团队成员及分工

| 分工 | 姓名 | GitHub | 方向 | 核心职责 |
| --- | --- | --- | --- | --- |
| 1 | pzq | [@Panzhongqiong](https://github.com/Panzhongqiong) | 数据工程 | 数据下载清洗、行程识别/OD 配对、构建共享分析数据集 |
| 2 | hy | [@yingh777706](https://github.com/yingh777706) | 业务分析 | 全局描述性统计、时间/空间维度客流规律 |
| 3 | lks | [@kaishuiliang](https://github.com/kaishuiliang) | 空间可视化 | 站点线路底图、热力图、OD 流向图、动态可视化 |
| 4 | ly | [@lyy11234](https://github.com/lyy11234) | 统计可视化 | 标准统计图表、出行模式提炼、统一视觉风格 |
| 5 | ycl | [@guaovo](https://github.com/guaovo) | 算法 + 总装 | K-Means 站点聚类、客流预测、报告/PPT 整合交付 |

## 开发环境

- 开发语言：Python 3.10 及以上（分工5 代码在 Python 3.12 下开发测试）
- 主要开发库：pandas、numpy、scikit-learn、statsmodels、matplotlib（详见 `requirements.txt`）
- 开发工具：PyCharm Community Edition、Jupyter Notebook

## 安装说明

```bash
# 克隆仓库
git clone https://github.com/yingh777706/shanghai-metro-viz.git
cd shanghai-metro-viz

# 创建虚拟环境并安装依赖
python -m venv .venv
# Windows 激活
.venv\Scripts\activate
pip install -r requirements.txt
```

## 数据获取说明

**本仓库不包含大体积数据文件**（原始/中间数据集达数 GB，由分工1 维护与分发）。
复现步骤：

1. 从 [MetroFlow](https://github.com/Ariza-Sun/MetroFlow)（Figshare）下载上海地铁
   2017.05–2017.08 刷卡数据与辅助数据；
2. 按分工1 的《数据预处理说明文档》（暂存 `readme合集（之后合并）/`，待分工1 迁入）
   的规则完成清洗，得到标准化数据表；
3. 将 `std_10min_inout.csv`（必需）与 `station_info.csv`、`workday_calendar.csv`
   放入项目根目录的 `data/` 文件夹，或设置环境变量 `METRO_DATA_DIR` 指向数据所在目录
   （`common.find_data()` 按 `METRO_DATA_DIR` > `data/` > `processed_data/` >
   `docs/processed_data/` > `docs/data/` 顺序查找，详见 `docs/项目路径与协作规范.md`）；
4. 运行下方脚本即可复现全部结果。

## 使用说明

> 全员遵守 `docs/项目路径与协作规范.md`：数据一律经 `common.find_data()` 定位（禁止硬编码绝对路径），
> 脚本输出直接写入各分工交付目录（运行即交付）。

### 1. K-Means 站点聚类（分工5）

```bash
python code/分工5/kmeans_station_clustering.py     # 约 1~3 分钟
```

提取 302 个站点的分时客流特征（工作日/周末 × 17 运营小时 × 进出站，log1p+标准化），
肘部法则+轮廓系数确定 K，最终聚为 5 类站点：
**综合枢纽站 / 就业办公站 / 通勤居住站 / 休闲商圈站 / 郊区低频站点**。

### 2. ARIMA/SARIMA 短时客流预测（分工5）

```bash
python code/分工5/arima_station_forecast.py        # 约 5~15 分钟
```

对典型站点（人民广场·枢纽、莘庄·通勤）的小时级进站客流：
ADF 平稳性检验 → AIC 网格定阶 → 普通 ARIMA 与季节 SARIMA(s=17) 对比 →
预留最后 7 天做样本外检验，输出 MAE / MSE / RMSE / MAPE 与预测对比曲线。

### 3. 其他分工脚本（需先按上文准备 data/）

| 分工 | 运行方式 | 详细说明 |
| --- | --- | --- |
| 分工2 统计分析 | `python code/分工2/statistical_analysis.py` | `分工2_统计分析/统计分析结论.md` |
| 分工3 空间可视化 | 按 `code/分工3/` 内 01~08 编号顺序执行 | `分工3_空间可视化/README.md` |
| 分工4 统计图表 | 见 `分工4_统计可视化/源代码/` 内 09~16 脚本 | `分工4_统计可视化/README.md` |

### 4. 分工5 结果文件对照表

| 文件 | 内容 |
| --- | --- |
| `分工5_数据挖掘/聚类/表1_K值评估指标.csv` | 各K值的SSE与轮廓系数 |
| `分工5_数据挖掘/聚类/表2_聚类结果表.csv` | 302个站点的类型标签与业务指标 |
| `分工5_数据挖掘/聚类/图1~图3` | 选K图、PCA散点图、分时客流画像 |
| `分工5_数据挖掘/预测/表4~表6` | ADF检验、模型定阶、预测误差指标 |
| `分工5_数据挖掘/预测/图4` | 预测对比曲线 |

> 运行即交付：脚本输出直接写入 `分工5_数据挖掘/`，重跑脚本即更新仓库内结果快照。

## 项目结构

```
shanghai-metro-viz/
├── README.md
├── requirements.txt
├── code/
│   ├── common.py                       # 公共工具：PROJECT_ROOT / find_data（唯一路径解析入口）
│   ├── 分工1/                          # 数据清洗脚本（待补入库）
│   ├── 分工2/statistical_analysis.py   # 客流时空特征统计分析
│   ├── 分工3/                          # 01~08 空间可视化脚本（聚合/热力图/OD 流向/交互地图）
│   ├── 分工4/                          # viz_style.py + 09~16 统计图表脚本
│   └── 分工5/                          # kmeans_station_clustering.py / arima_station_forecast.py
├── 分工2_统计分析/                      # 表1~6、统计分析结论、数据需求单
├── 分工3_空间可视化/                    # 交互地图、图片、空间数据、README
├── 分工4_统计可视化/                    # 图片、源代码、README
├── 分工5_数据挖掘/                      # 聚类/、预测/、README（算法与使用说明）
├── data/                               # 数据文件不入库（.gitignore 已排除）
├── docs/
│   └── 项目路径与协作规范.md             # 全员路径/目录/提交规范（必读）
├── 任务清单/                            # 各分工待办、行动边界与提交要求
├── readme合集（之后合并）/               # 历史文档暂存（待各分工迁回后删除）
└── 报告/
    └── 小组期末报告.docx                # 期末报告（已填分工1/5部分，持续更新）
```

## 当前进展

- [x] 分工1 数据治理：标准化数据集已交付组员（数据文件不入库；清洗脚本与文档待迁入）
- [x] 分工2 客流时空统计分析（代码、结果、结论已入库）
- [x] 分工3 空间地图可视化（热力图、OD 流向图、交互地图已入库）
- [x] 分工4 统计图表与出行模式可视化（图 4-1~4-8 已入库）
- [x] 分工5 K-Means 站点聚类（代码、结果、说明已入库）
- [x] 分工5 ARIMA 短时客流预测（代码、结果、说明已入库）
- [x] 期末报告：数据说明、数据处理、数据挖掘章节已完成
- [ ] 总装：报告并稿、汇报 PPT、最终打包

## 分工5 成果速览

- **站点聚类**：302 个站点分为 5 类——综合枢纽 26 站（人民广场、上海火车站等）、
  就业办公 75 站、通勤居住 98 站、休闲商圈 79 站（迪士尼、中华艺术宫等）、
  郊区低频 24 站；K=5 轮廓系数 0.307。
- **短时预测**：SARIMA(1,0,2)×(1,1,1,17) 相比普通 ARIMA，人民广场 MAE
  由 2185 降至 1204 人次/小时（下降约 45%），预测曲线峰形与相位基本同步。

## 分工2 成果速览

- **全局**：统计 123 天（2017-05-01 ~ 08-31），总进站量 7.29 亿人次，日均 592.6 万。
- **时间**：工作日日均 651.1 万 vs 周末 451.0 万；早高峰 8:00、晚高峰 17:00。
- **空间**：进站量 Top3 People's Square（人民广场，1800 万）> Xujiahui（徐家汇，1194 万）> Jing'an Temple（静安寺，1189 万）。
- **出行距离**：加权平均直线距离 16.06 km（起终点站经纬度球面距离，非轨道路径）。
