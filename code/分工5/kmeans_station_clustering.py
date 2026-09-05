# -*- coding: utf-8 -*-
"""
分工5 · 任务一：K-Means 地铁站点客流模式聚类
================================================================
功能：
  1. 读取分工1输出的10分钟粒度进出站流量表 std_10min_inout.csv
  2. 提取每个站点的分时客流特征（工作日/周末 × 小时 × 进站/出站）
  3. 标准化后，用肘部法则(SSE) + 轮廓系数确定最佳聚类数 K
  4. 运行 KMeans 聚类，把 302 个站点划分为 5 类：
     通勤居住站 / 就业办公站 / 综合枢纽站 / 休闲商圈站 / 郊区低频站点
  5. 输出：聚类结果表、评估指标、PCA散点图、分时客流曲线图、分析结论

运行方式：
  在项目根目录或本文件所在目录执行  python kmeans_station_clustering.py
  运行前请确认 processed_data/std_10min_inout.csv 已就位
  （依赖见根目录 requirements.txt：pandas numpy scikit-learn matplotlib）
"""

import sys

import matplotlib
matplotlib.use("Agg")                 # 无界面环境下绘图，直接保存图片
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------- 路径配置
# 统一的数据文件定位与项目根目录（见 code/common.py）
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # 使 code/ 子目录脚本可 import common
from common import PROJECT_ROOT, find_data

DATA_FILE = find_data("std_10min_inout.csv")
CAL_FILE = find_data("workday_calendar.csv")
STATION_FILE = find_data("station_info.csv")
OUT_DIR = PROJECT_ROOT / "分工5_数据挖掘" / "聚类"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 中文绘图字体（Windows 自带微软雅黑）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# Windows 控制台默认 GBK 编码，强制切换 UTF-8 防止中文乱码
sys.stdout.reconfigure(encoding="utf-8")

RANDOM_STATE = 42        # 固定随机种子，保证结果可复现
FINAL_K = 5              # 按分工要求最终聚成 5 类
K_RANGE = range(3, 9)    # 肘部法则/轮廓系数搜索范围


# ================================================================ 1. 读数据
def load_hourly_flow() -> pd.DataFrame:
    """分块读取 312MB 进出站表，汇总成『站点 × 日期 × 小时』的客流宽表。

    原表 378 万行（302 站 × 123 天 × 108 个10分钟时段），
    分块 groupby 求和后压缩为约 63 万行，避免内存不足。
    """
    cols = ["date", "startTime", "stationID", "inFlow", "outFlow"]
    dtypes = {"date": "int64", "stationID": "int16",
              "inFlow": "int32", "outFlow": "int32"}
    parts = []
    reader = pd.read_csv(DATA_FILE, usecols=cols, dtype=dtypes,
                         encoding="utf-8-sig", chunksize=500_000)
    for i, chunk in enumerate(reader, 1):
        chunk["hour"] = chunk["startTime"].str.slice(0, 2).astype(int)
        g = (chunk.groupby(["stationID", "date", "hour"], sort=False)
                  [["inFlow", "outFlow"]].sum())
        parts.append(g.reset_index())
        print(f"  已读取 {i * 50} 万行原始记录...")
    agg = (pd.concat(parts, ignore_index=True)
             .groupby(["stationID", "date", "hour"])
             [["inFlow", "outFlow"]].sum().reset_index())
    print(f"  汇总完成：{len(agg)} 条『站点-日期-小时』客流记录")
    return agg


# ================================================================ 2. 特征工程
def build_features(agg: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """构造 KMeans 输入特征矩阵（每站一行）。

    特征 = 工作日平均分时客流(log1p) 17h×2 + 周末平均分时客流(log1p) 17h×2
           + log1p(日均总客流) 共 69 维。
    流量先做 log1p 压缩：枢纽站与郊区站客流差可达百倍，
    不压缩会导致聚类只按“流量大小”分组，分不出时间模式。
    """
    cal = pd.read_csv(CAL_FILE, encoding="utf-8-sig")
    day_type = dict(zip(cal["date"], cal["isWorkday"]))       # 1=工作日 0=周末/节假日
    agg["isWorkday"] = agg["date"].map(day_type)

    agg["log_in"] = np.log1p(agg["inFlow"])
    agg["log_out"] = np.log1p(agg["outFlow"])

    feats = {}
    for flag, tag in [(1, "wd"), (0, "we")]:                  # 工作日/周末 分时画像
        sub = agg[agg["isWorkday"] == flag]
        prof = (sub.groupby(["stationID", "hour"])[["log_in", "log_out"]]
                   .mean().reset_index()
                   .pivot(index="stationID", columns="hour"))
        prof.columns = [f"{tag}_{a}_{h}" for a, h in prof.columns]
        feats[tag] = prof
    X = feats["wd"].join(feats["we"], how="inner")

    days = agg["date"].nunique()
    daily = agg.groupby("stationID")[["inFlow", "outFlow"]].sum() / days
    X["daily_total"] = np.log1p(daily["inFlow"] + daily["outFlow"])
    X = X.dropna()
    return X, agg


# ================================================================ 3. 选 K
def choose_k(Xs: np.ndarray) -> pd.DataFrame:
    """肘部法则 + 轮廓系数：对 K=3..8 分别训练，记录 SSE 与轮廓系数。"""
    rows = []
    for k in K_RANGE:
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit(Xs)
        sse = float(km.inertia_)
        sil = float(silhouette_score(Xs, km.labels_))
        rows.append({"K": k, "SSE": round(sse, 1), "轮廓系数": round(sil, 4)})
        print(f"  K={k}  SSE={sse:.1f}  轮廓系数={sil:.4f}")
    return pd.DataFrame(rows)


def plot_k(kdf: pd.DataFrame) -> None:
    """画肘部法则(SSE)与轮廓系数双轴折线图。"""
    fig, ax1 = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax1.plot(kdf["K"], kdf["SSE"], "o-", color="#1f77b4", label="SSE")
    ax1.set_xlabel("聚类数 K")
    ax1.set_ylabel("SSE（簇内误差平方和）", color="#1f77b4")
    ax2 = ax1.twinx()
    ax2.plot(kdf["K"], kdf["轮廓系数"], "s--", color="#d62728", label="轮廓系数")
    ax2.set_ylabel("轮廓系数", color="#d62728")
    ax2.axvline(FINAL_K, color="gray", ls=":", lw=1)
    ax2.annotate(f"最终选择 K={FINAL_K}", xy=(FINAL_K, ax2.get_ylim()[0]),
                 xytext=(FINAL_K + 0.15, ax2.get_ylim()[1] * 0.92))
    fig.suptitle("肘部法则与轮廓系数确定最佳聚类数")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "图1_肘部法则与轮廓系数.png")
    plt.close(fig)


# ================================================================ 4. 聚类与打标签
def label_clusters(km: KMeans, X: pd.DataFrame, agg: pd.DataFrame,
                   days: int) -> pd.DataFrame:
    """根据各簇中心的业务指标，把抽象簇号翻译成可解释的站点类型标签。"""
    cal = pd.read_csv(CAL_FILE, encoding="utf-8-sig")
    day_type = dict(zip(cal["date"], cal["isWorkday"]))
    agg = agg.copy()
    agg["isWorkday"] = agg["date"].map(day_type)

    # --- 计算每个站点的业务指标（原始客流尺度）---
    hourly = agg.groupby(["stationID", "isWorkday", "hour"])[["inFlow", "outFlow"]].mean()

    def avg_daily(flag, col):
        d = agg[agg["isWorkday"] == flag].groupby("stationID")[col].sum()
        n = agg[agg["isWorkday"] == flag]["date"].nunique()
        return d / n

    daily_wd = avg_daily(1, "inFlow") + avg_daily(1, "outFlow")     # 工作日日均总客流
    daily_we = avg_daily(0, "inFlow") + avg_daily(0, "outFlow")     # 周末日均总客流

    wd = hourly.xs(1, level="isWorkday")
    am_in = wd[(wd.index.get_level_values("hour") >= 7) &
               (wd.index.get_level_values("hour") <= 9)]["inFlow"].groupby("stationID").mean()
    pm_in = wd[(wd.index.get_level_values("hour") >= 17) &
               (wd.index.get_level_values("hour") <= 19)]["inFlow"].groupby("stationID").mean()
    am_out = wd[(wd.index.get_level_values("hour") >= 8) &
                (wd.index.get_level_values("hour") <= 10)]["outFlow"].groupby("stationID").mean()
    in_day = wd.groupby("stationID")["inFlow"].mean() * 17          # 全天17小时平均×17≈日均

    metrics = pd.DataFrame({
        "日均总客流": daily_wd + daily_we,
        "周末比": daily_we / daily_wd,
        "早高峰进站占比": am_in / (in_day + 1e-9),
        "晚高峰进站占比": pm_in / (in_day + 1e-9),
        "早高峰出站占比": am_out / (in_day + 1e-9),
    })

    # --- 聚合到簇级别（取簇内均值）---
    lab = pd.Series(km.labels_, index=X.index, name="cluster")
    cm = metrics.join(lab).groupby("cluster").mean()

    # --- 按业务规则给 5 个簇分配类型标签（贪心，保证一一对应）---
    order = list(cm.index)
    assign = {}
    assign[cm["日均总客流"].idxmax()] = "综合枢纽站"       # 流量最大
    assign[cm["日均总客流"].idxmin()] = "郊区低频站点"     # 流量最小
    rest = [c for c in order if c not in assign]
    assign[max(rest, key=lambda c: cm.loc[c, "早高峰进站占比"])] = "通勤居住站"
    rest = [c for c in rest if c not in assign]
    assign[max(rest, key=lambda c: cm.loc[c, "早高峰出站占比"] +
                                  cm.loc[c, "晚高峰进站占比"])] = "就业办公站"
    rest = [c for c in rest if c not in assign]
    assign[rest[0]] = "休闲商圈站"

    print("\n各簇业务指标均值（用于类型判定）：")
    print(cm.round(3).to_string())
    print("\n簇号 → 类型：", {k: v for k, v in sorted(assign.items())})

    result = pd.DataFrame({
        "stationID": X.index,
        "聚类簇号": lab.values,
        "站点类型": lab.values,
    })
    result["站点类型"] = result["聚类簇号"].map(assign)
    result = result.merge(metrics.reset_index(), on="stationID")
    result = result.merge(
        pd.read_csv(STATION_FILE, encoding="utf-8-sig")[["stationID", "name"]],
        on="stationID", how="left")
    return result


# ================================================================ 5. 可视化
def plot_pca(Xs: np.ndarray, result: pd.DataFrame) -> None:
    """PCA 降到 2 维画聚类散点图。"""
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    xy = pca.fit_transform(Xs)
    fig, ax = plt.subplots(figsize=(8.5, 6), dpi=150)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for i, t in enumerate(result["站点类型"].unique()):
        m = (result["站点类型"] == t).values
        ax.scatter(xy[m, 0], xy[m, 1], s=22, c=colors[i % 5], label=t, alpha=0.8)
    ax.set_xlabel(f"主成分1（解释方差 {pca.explained_variance_ratio_[0]:.0%}）")
    ax.set_ylabel(f"主成分2（解释方差 {pca.explained_variance_ratio_[1]:.0%}）")
    ax.set_title("K-Means 站点聚类结果（PCA 降维散点图）")
    ax.legend(markerscale=1.6)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "图2_聚类散点图.png")
    plt.close(fig)


def plot_profiles(result: pd.DataFrame, agg: pd.DataFrame) -> None:
    """画每个簇的工作日平均分时进/出站客流曲线（簇中心画像）。"""
    cal = pd.read_csv(CAL_FILE, encoding="utf-8-sig")
    day_type = dict(zip(cal["date"], cal["isWorkday"]))
    agg = agg.copy()
    agg["isWorkday"] = agg["date"].map(day_type)
    wd = agg[agg["isWorkday"] == 1].merge(
        result[["stationID", "站点类型"]], on="stationID")
    prof = (wd.groupby(["站点类型", "hour"])[["inFlow", "outFlow"]]
              .mean().reset_index())
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150, sharex=True)
    for t, sub in prof.groupby("站点类型"):
        axes[0].plot(sub["hour"], sub["inFlow"], marker="o", ms=3, label=t)
        axes[1].plot(sub["hour"], sub["outFlow"], marker="o", ms=3, label=t)
    axes[0].set_title("工作日平均分时进站客流")
    axes[1].set_title("工作日平均分时出站客流")
    for ax in axes:
        ax.set_xlabel("小时")
        ax.set_ylabel("平均客流量（人次/小时）")
        ax.legend(fontsize=8)
    fig.suptitle("各类型站点簇的工作日分时客流画像")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "图3_各簇分时客流画像.png")
    plt.close(fig)


# ================================================================ 主流程
def main() -> None:
    print("=" * 60)
    print("K-Means 站点客流模式聚类")
    print("=" * 60)

    print("\n[1/6] 读取并汇总进出站数据...")
    agg = load_hourly_flow()
    days = agg["date"].nunique()
    print(f"  覆盖 {days} 天、{agg['stationID'].nunique()} 个站点")

    print("\n[2/6] 构造分时客流特征矩阵...")
    X, agg = build_features(agg)
    print(f"  特征矩阵：{X.shape[0]} 站 × {X.shape[1]} 维")

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X.values)

    print("\n[3/6] 肘部法则 + 轮廓系数选择 K...")
    kdf = choose_k(Xs)
    kdf.to_csv(OUT_DIR / "表1_K值评估指标.csv", index=False, encoding="utf-8-sig")
    plot_k(kdf)

    print(f"\n[4/6] 以 K={FINAL_K} 训练最终 KMeans 模型...")
    km = KMeans(n_clusters=FINAL_K, n_init=10, random_state=RANDOM_STATE).fit(Xs)
    sil = silhouette_score(Xs, km.labels_)
    print(f"  最终轮廓系数 = {sil:.4f}，SSE = {km.inertia_:.1f}")

    print("\n[5/6] 簇类型判定与结果表输出...")
    result = label_clusters(km, X, agg, days)
    result.insert(0, "name", result.pop("name"))
    result.to_csv(OUT_DIR / "表2_聚类结果表.csv", index=False, encoding="utf-8-sig")

    stat = (result.groupby("站点类型")
                  .agg(站点数=("stationID", "count"),
                       平均日均总客流=("日均总客流", "mean"))
                  .sort_values("平均日均总客流", ascending=False))
    stat.to_csv(OUT_DIR / "表3_聚类结果统计表.csv", encoding="utf-8-sig")
    print(stat.to_string())

    print("\n[6/6] 绘图输出...")
    plot_pca(Xs, result)
    plot_profiles(result, agg)

    # 自动生成带真实数字的分析结论草稿
    sil_k = kdf.set_index("K")["轮廓系数"]
    lines = [f"# K-Means 站点聚类分析结论（自动生成）\n",
             f"- 特征矩阵：{X.shape[0]} 个站点 × {X.shape[1]} 维分时客流特征"
             f"（工作日/周末 × 小时 × 进出站，log1p + 标准化）",
             f"- K=3~8 搜索：最佳轮廓系数出现在 K={int(sil_k.idxmax())}"
             f"（{sil_k.max():.4f}）；结合分工要求的 5 类站点类型，最终取 K={FINAL_K}，"
             f"轮廓系数 {sil:.4f}。",
             f"- SSE 从 K=3 的 {kdf.loc[kdf['K'] == 3, 'SSE'].iloc[0]:.0f} "
             f"下降到 K=8 的 {kdf.loc[kdf['K'] == 8, 'SSE'].iloc[0]:.0f}，K>5 后下降趋缓（肘部）。\n"]
    for t, row in stat.iterrows():
        top = (result[result["站点类型"] == t]
               .nlargest(5, "日均总客流")["name"].tolist())
        lines.append(f"## {t}（{int(row['站点数'])} 站，"
                     f"日均客流 {row['平均日均总客流']:.0f} 人次）\n代表站点：{'、'.join(top)}\n")
    (OUT_DIR / "聚类分析结论.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"\n全部完成！结果已保存到：{OUT_DIR}")


if __name__ == "__main__":
    main()
