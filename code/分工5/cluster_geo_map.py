# -*- coding: utf-8 -*-
"""
分工5 · 补充：站点聚类地理分布气泡图（图6）
================================================================
在灰色上海地铁线网底图上，用气泡展示 KMeans 聚类结果：
  - 底图：302 站按 neighbour 邻接关系连成线网，浅灰色，不显示站名
  - 气泡：颜色 = 站点类型（与图2/图3 配色一致），
          面积 ∝ 日均总客流（工作日+周末平均之和）
  - 防重叠：城市中心站点密集，圆圈按『大圈优先』迭代外推，
            保证两两不重叠，同时尽量贴近真实位置
  - 图例：右侧类型图例（含站数）+ 尺寸参照图例

输入：分工5_数据挖掘/聚类/表2_聚类结果表.csv（kmeans_station_clustering.py 产出）
      data/station_info.csv（经纬度 + neighbour 邻接表）
输出：分工5_数据挖掘/聚类/图6_聚类地理分布图.png
运行：python cluster_geo_map.py   （只读小表，秒级完成，不碰 312MB 大表）
"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROJECT_ROOT, find_data

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

# 中文绘图字体（Windows 自带微软雅黑）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

RESULT_FILE = PROJECT_ROOT / "分工5_数据挖掘" / "聚类" / "表2_聚类结果表.csv"
OUT_FILE = PROJECT_ROOT / "分工5_数据挖掘" / "聚类" / "图6_聚类地理分布图.png"
STATION_FILE = find_data("station_info.csv")

sys.stdout.reconfigure(encoding="utf-8")

# 与 kmeans_station_clustering.py 保持一致的五类配色
TYPE_COLORS = {
    "通勤居住站": "#1f77b4",
    "综合枢纽站": "#ff7f0e",
    "就业办公站": "#2ca02c",
    "休闲商圈站": "#d62728",
    "郊区低频站点": "#9467bd",
}

R_MIN, R_MAX = 0.32, 1.25     # 气泡半径范围（公里）
SIL = 0.3070                  # K=5 轮廓系数（表1），仅用于图内标注


def load_stations() -> pd.DataFrame:
    res = pd.read_csv(RESULT_FILE, encoding="utf-8-sig")
    info = pd.read_csv(STATION_FILE, encoding="utf-8-sig")
    df = res.merge(info[["stationID", "lon", "lat", "neighbour"]],
                   on="stationID", how="left")
    assert df["lon"].notna().all(), "有站点缺少经纬度，请检查 station_info.csv"
    # 经纬度 → 以人民广场为原点的平面公里坐标（等距近似）
    LAT0, LON0 = 31.235, 121.470
    df["x"] = (df["lon"] - LON0) * 111.32 * np.cos(np.radians(LAT0))
    df["y"] = (df["lat"] - LAT0) * 110.57
    return df


def build_edges(df: pd.DataFrame) -> list:
    """按 neighbour 邻接表把线网连成边（去重），返回公里坐标线段列表。"""
    idset = set(df["stationID"])
    pos = dict(zip(df["stationID"], zip(df["x"], df["y"])))
    edges = set()
    for sid, nb in zip(df["stationID"], df["neighbour"]):
        for n in ast.literal_eval(nb):
            if n in idset and n != sid:
                edges.add((min(sid, n), max(sid, n)))
    return [[pos[a], pos[b]] for a, b in sorted(edges)]


def resolve_overlap(pos: np.ndarray, r: np.ndarray) -> np.ndarray:
    """迭代碰撞避让：两两重叠的圆圈沿连线方向互相推开。

    第一阶段带弱回复力，让圆圈整体尽量贴近真实位置；
    第二阶段去掉回复力做纯推开，直到完全无重叠为止。"""
    p = pos.copy()
    for it in range(2000):
        diff = p[:, None, :] - p[None, :, :]
        dist = np.hypot(diff[..., 0], diff[..., 1])
        np.fill_diagonal(dist, np.inf)
        overlap = (r[:, None] + r[None, :]) - dist
        if it >= 1000:
            if overlap.max() <= 1e-4:
                print(f"  第 {it} 轮迭代后完全无重叠")
                break
            w = np.maximum(overlap, 0.0) / dist
            p += (diff * w[..., None]).sum(axis=1) * 0.5
        else:
            if overlap.max() <= 1e-3:
                print(f"  第 {it} 轮迭代后无重叠")
                break
            w = np.maximum(overlap, 0.0) / dist
            push = (diff * w[..., None]).sum(axis=1) * 0.5
            p += push + 0.02 * (pos - p)
    else:
        print("  警告：达到迭代上限，仍存在微小重叠")
    return p


def km_to_points(pt_per_km: float, r_km: np.ndarray) -> np.ndarray:
    """把公里半径换算成 matplotlib 散点的 s 参数（点径平方）。

    比例尺按最终坐标轴宽度精确计算，保证公里坐标系里的
    『无重叠』在屏幕上同样成立。"""
    return (2 * r_km * pt_per_km) ** 2


def main() -> None:
    print("=" * 60)
    print("站点聚类地理分布气泡图（灰色线网底图）")
    print("=" * 60)

    df = load_stations()
    print(f"已加载 {len(df)} 个站点（含聚类标签与客流）")

    segments = build_edges(df)
    print(f"线网共 {len(segments)} 条邻接边")

    flow = df["日均总客流"].to_numpy(float)
    r = R_MIN + (R_MAX - R_MIN) * np.sqrt(flow / flow.max())
    pos = resolve_overlap(df[["x", "y"]].to_numpy(float), r)
    shift = np.hypot(*(pos - df[["x", "y"]].to_numpy(float)).T)
    print(f"位移统计：中位数 {np.median(shift):.2f} km，"
          f"最大 {shift.max():.2f} km")

    # 固定边距：坐标轴宽度 = (right-left)*figwidth，等比 aspect 下宽度不变，
    # 因此 km→点径 换算在整个绘图流程中保持一致
    left, right = 0.055, 0.80
    fig, ax = plt.subplots(figsize=(12.5, 10.2), dpi=150)
    fig.subplots_adjust(left=left, right=right, top=0.94, bottom=0.075)

    ax.add_collection(LineCollection(segments, colors="#c8c8c8",
                                     linewidths=0.9, zorder=1))
    pad = 4
    ax.set_xlim(df["x"].min() - pad, df["x"].max() + pad)
    ax.set_ylim(df["y"].min() - pad, df["y"].max() + pad + 2)
    pt_per_km = (right - left) * fig.get_figwidth() * 72.0 / \
        (df["x"].max() - df["x"].min() + 2 * pad)

    for t, color in TYPE_COLORS.items():
        m = (df["站点类型"] == t).to_numpy()
        ax.scatter(pos[m, 0], pos[m, 1], s=km_to_points(pt_per_km, r[m]),
                   facecolor=color, edgecolor="white", linewidth=0.5,
                   alpha=0.85, zorder=3,
                   label=f"{t}（{m.sum()}站）")
    ax.set_aspect("equal")
    ax.set_title("上海地铁站点聚类结果地理分布", fontsize=14, pad=12)
    ax.set_xlabel("距人民广场东西距离（公里）", fontsize=9)
    ax.set_ylabel("距人民广场南北距离（公里）", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, ls=":", lw=0.4, color="#e0e0e0", zorder=0)
    for spine in ax.spines.values():
        spine.set_color("#bbbbbb")

    # 右侧图例：站点类型（上，统一标记大小）+ 尺寸参照（下）
    counts = df["站点类型"].value_counts()
    type_handles = [
        Line2D([], [], marker="o", ls="", markersize=9,
               markerfacecolor=c, markeredgecolor="white",
               label=f"{t}（{counts[t]}站）")
        for t, c in TYPE_COLORS.items()]
    leg_type = ax.legend(handles=type_handles, loc="upper left",
                         bbox_to_anchor=(1.01, 1.0), fontsize=9,
                         frameon=False, title="站点类型（K=5）",
                         title_fontsize=10)
    ax.add_artist(leg_type)

    ref_vals = sorted({min(v, flow.max()) for v in (20000, 100000, flow.max())})
    ref_r = R_MIN + (R_MAX - R_MIN) * np.sqrt(
        np.array(ref_vals) / flow.max())
    ref_handles = [plt.scatter([], [], s=km_to_points(pt_per_km, np.array([rr]))[0],
                               facecolor="#aaaaaa", edgecolor="white",
                               linewidth=0.5, alpha=0.85)
                   for rr in ref_r]
    ref_labels = [f"{v / 10000:.1f} 万人次/日" for v in ref_vals]
    ax.legend(ref_handles, ref_labels, loc="lower left",
              bbox_to_anchor=(1.01, 0.0), fontsize=9, frameon=False,
              labelspacing=2.2, borderpad=1.2,
              title="圆面积 ∝ 日均总客流", title_fontsize=10)

    fig.text(0.01, 0.012,
             f"注：底图为上海地铁线网邻接图（不标注站名）；颜色对应 KMeans 聚类类型"
             f"（K=5，轮廓系数 {SIL:.4f}）；\n"
             f"城市中心密集站点的圆圈为避免重叠做了小幅位移，位置略有偏移；"
             f"客流为工作日+周末日均之和。",
             fontsize=7.5, color="#666666", va="bottom")
    fig.savefig(OUT_FILE)
    plt.close(fig)
    print(f"已保存：{OUT_FILE}")


if __name__ == "__main__":
    main()
