# -*- coding: utf-8 -*-
"""
统一视觉风格模块 —— 分工4 全套图表共用
用法: from 风格 import *  或  import viz_style
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ---------- 配色规范(全项目统一) ----------
C_MAIN   = "#1f77b4"   # 主色:客流/工作日
C_ACCENT = "#ff7f0e"   # 强调色:周末/对比
C_C      = "#d62728"   # 通勤(C)
C_HBO    = "#2ca02c"   # 居家其他(HBO)
C_NHB    = "#9467bd"   # 非居家(NHB)
C_GRAY   = "#7f7f7f"
PALETTE  = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
CMAP_FLOW = "YlOrRd"          # 客流热力类
CMAP_DIFF = "RdBu_r"          # 差异对比类

def apply_style():
    """应用统一图表风格(中文字体/字号/网格/边框)"""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Noto Sans CJK SC", "Source Han Sans SC",
                            "WenQuanYi Zen Hei", "SimHei", "Arial Unicode MS"],
        "axes.unicode_minus": False,
        "figure.dpi": 120,
        "savefig.dpi": 300,          # 高清300DPI,可直接用于报告
        "figure.figsize": (10, 6),
        "axes.titlesize": 15, "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "xtick.labelsize": 10, "ytick.labelsize": 10,
        "legend.fontsize": 10, "legend.frameon": False,
        "axes.grid": True, "grid.alpha": 0.3, "grid.linestyle": "--",
        "axes.spines.top": False, "axes.spines.right": False,
        "savefig.bbox": "tight", "savefig.facecolor": "white",
    })

def savefig(fig, path):
    fig.savefig(path)
    plt.close(fig)
    print("已保存:", path)

# ---------- 数据加载 ----------
import os, pandas as pd

def _data_dirs(root):
    env = os.environ.get("METRO_DATA_DIR")
    dirs = [os.path.join(root, "data"), os.path.join(root, "processed_data"),
            os.path.join(root, "分工4_统计可视化", "data")]
    if env: dirs.insert(0, env)
    return dirs

def _find_file(candidates, dirs):
    for d in dirs:
        for c in candidates:
            p = os.path.join(d, c)
            if os.path.exists(p):
                return p
    raise FileNotFoundError("未找到数据文件,请将数据集放入 data/ 或 processed_data/: "
                            + ",".join(candidates))

def project_root():
    # 源代码位于 分工4_统计可视化/源代码/,项目根目录为上两级
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))

def load_inout():
    """读取10分钟粒度站点进出站客流(优先分工1标准化数据)"""
    root = project_root()
    p = _find_file(["std_10min_inout.csv", "metroData_InOutFlow.csv"], _data_dirs(root))
    df = pd.read_csv(p)
    df.columns = [c.strip() for c in df.columns]
    ren = {}
    if "station" in df.columns: ren["station"] = "stationID"
    if "HBOinFlow" in df.columns: ren["HBOinFlow"] = "HB0inFlow"
    if "HBOoutFlow" in df.columns: ren["HBOoutFlow"] = "HB0outFlow"
    df = df.rename(columns=ren)
    df["date"] = df["date"].astype(str)
    st = df["startTime"].astype(str).str.zfill(6)
    df["datetime"] = pd.to_datetime(df["date"] + st, format="%Y%m%d%H%M%S")
    df["hour"] = df["datetime"].dt.hour + df["datetime"].dt.minute / 60.0
    # 注意: 原始timeslot为跨天全局编号, 日内时段需用startTime计算(06:00起每10分钟一格)
    df["slot"] = ((df["hour"] - 6) * 6).round().astype(int)
    df["total"] = df["inFlow"] + df["outFlow"]
    return df

# 源数据集中6天刷卡记录近乎缺失(日总客流<百万级), 统计均值时剔除
ABNORMAL_DATES = ["20170504", "20170508", "20170509",
                  "20170616", "20170627", "20170628"]

def drop_abnormal_days(df):
    return df[~df["date"].isin(ABNORMAL_DATES)]

def load_station_info():
    root = project_root()
    p = _find_file(["station_info.csv", "stationInfo.csv"], _data_dirs(root))
    df = pd.read_csv(p)
    df.columns = [c.strip() for c in df.columns]
    return df

def load_calendar():
    root = project_root()
    p = _find_file(["workday_calendar.csv", "work_calendar.csv"], _data_dirs(root))
    cal = pd.read_csv(p)
    cal.columns = [c.strip() for c in cal.columns]
    cal = cal.rename(columns={"isWorday": "isWorkday"})
    cal["date"] = cal["date"].astype(str)
    return dict(zip(cal["date"], cal["isWorkday"]))

def load_od():
    """读取10分钟粒度OD客流(约4GB,请确保内存充足;距离分布直方图用)"""
    root = project_root()
    p = _find_file(["std_10min_od.csv", "metroData_ODFlow.csv"], _data_dirs(root))
    return p  # 返回路径,由调用方分块读取

def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2*R*np.arcsin(np.sqrt(a))
