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
2. 按仓库 `docs/数据预处理说明文档.md` 的规则完成清洗，得到标准化数据表；
3. 将 `std_10min_inout.csv`（必需）与 `station_info.csv`、`workday_calendar.csv`
   放入项目根目录的 `data/` 文件夹（或 `processed_data/`，脚本两者都会查找）；
4. 运行下方脚本即可复现全部挖掘结果。

## 使用说明

### 1. K-Means 站点聚类（分工5）

```bash
python code/kmeans_station_clustering.py     # 约 1~3 分钟
```

提取 302 个站点的分时客流特征（工作日/周末 × 17 运营小时 × 进出站，log1p+标准化），
肘部法则+轮廓系数确定 K，最终聚为 5 类站点：
**综合枢纽站 / 就业办公站 / 通勤居住站 / 休闲商圈站 / 郊区低频站点**。

### 2. ARIMA 短时客流预测（分工5）

```bash
python code/arima_station_forecast.py        # 约 5~15 分钟
```

对典型站点（人民广场·枢纽、莘庄·通勤）的小时级进站客流：
ADF 平稳性检验 → AIC 网格定阶 → 普通 ARIMA 与季节 SARIMA(s=17) 对比 →
预留最后 7 天做样本外检验，输出 MAE / MSE / RMSE / MAPE 与预测对比曲线。

### 3. 结果文件对照表

| 文件 | 内容 |
| --- | --- |
| `code/数据挖掘/输出结果/聚类/表1_K值评估指标.csv` | 各K值的SSE与轮廓系数 |
| `code/数据挖掘/输出结果/聚类/表2_聚类结果表.csv` | 302个站点的类型标签与业务指标 |
| `code/数据挖掘/输出结果/聚类/图1~图3` | 选K图、PCA散点图、分时客流画像 |
| `code/数据挖掘/输出结果/预测/表4~表6` | ADF检验、模型定阶、预测误差指标 |
| `code/数据挖掘/输出结果/预测/图4` | 预测对比曲线 |

> 运行脚本会在项目根目录重新生成 `输出结果/` 文件夹；仓库中附带的结果快照
> 存放于 `code/数据挖掘/输出结果/`，二者内容一致。

## 项目结构

```
shanghai-metro-viz/
├── README.md
├── requirements.txt
├── code/
│   ├── kmeans_station_clustering.py   # 分工5：K-Means 站点客流模式聚类
│   ├── arima_station_forecast.py      # 分工5：ARIMA/SARIMA 短时客流预测
│   └── 数据挖掘/                       # 分工5：说明文档 + 运行结果快照
│       ├── 数据挖掘说明文档.md          #   算法原理、运行方式、结果解读
│       └── 输出结果/
│           ├── 聚类/                   #   图1~图3、表1~表3、聚类分析结论
│           └── 预测/                   #   图4、表4~表6、预测明细与模型分析
├── docs/
│   ├── 数据预处理说明文档.md           # 分工1：数据来源、清洗规则、字段说明
│   └── 清洗运行日志.txt                # 分工1：清洗过程运行日志
├── 报告/
│   └── 小组期末报告.docx               # 期末报告（已填分工1/5部分，持续更新）
└── data/                              # 数据文件不入库（.gitignore 已排除）
```

## 当前进展

- [x] 分工1 数据治理：标准化数据集已交付组员（数据文件不入库，文档见 `docs/`）
- [x] 分工5 K-Means 站点聚类（代码、结果、说明已入库）
- [x] 分工5 ARIMA 短时客流预测（代码、结果、说明已入库）
- [x] 期末报告：数据说明、数据处理、数据挖掘章节已完成
- [ ] 分工2 客流时空统计分析
- [ ] 分工3 空间地图可视化
- [ ] 分工4 统计图表与出行模式可视化
- [ ] 总装：报告并稿、汇报 PPT、最终打包

## 分工5 成果速览

- **站点聚类**：302 个站点分为 5 类——综合枢纽 26 站（人民广场、上海火车站等）、
  就业办公 75 站、通勤居住 98 站、休闲商圈 79 站（迪士尼、中华艺术宫等）、
  郊区低频 24 站；K=5 轮廓系数 0.307。
- **短时预测**：SARIMA(1,0,2)×(1,1,1,17) 相比普通 ARIMA，人民广场 MAE
  由 2185 降至 1204 人次/小时（下降约 45%），预测曲线峰形与相位基本同步。
