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

- 开发语言：Python（版本待定）
- 主要开发库：pandas、numpy、matplotlib、pyecharts 等（待补充）

## 安装说明

```bash
# 克隆仓库
git clone https://github.com/yingh777706/ShanghaiMetro-Visualization.git
cd ShanghaiMetro-Visualization

# 创建虚拟环境并安装依赖
python -m venv .venv
# Windows 激活
.venv\Scripts\activate
pip install -r requirements.txt
```

## 使用说明

（待补充：数据处理、分析、可视化的运行步骤）

## 项目结构

（待补充）
