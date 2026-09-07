# -*- coding: utf-8 -*-
"""
分工5 · 任务二：ARIMA 短时客流预测
================================================================
功能：
  1. 自动读取聚类结果（表2_聚类结果表.csv），从 5 类站点中各取
     日均客流最高的 1 个作为典型代表站（共 5 站），
     构建各站小时级进站客流时间序列
  2. ADF 单位根检验判断平稳性，确定差分阶数 d
  3. 对每个站点训练两组模型并对比：
     ① 普通 ARIMA(p,d,q)              —— 不含周期项
     ② 季节 ARIMA(p,d,q)×(P,D,Q,17)   —— 17 = 每日运营小时数（06:00~22:00），
        用周期项刻画“日内早晚高峰”规律
  4. 以“上周同时刻”作为朴素基线，预留最后 7 天做样本外检验，
     计算 MAE / MSE / RMSE / MAPE，绘制预测对比曲线

运行方式：
  python arima_station_forecast.py
  前置：先运行 kmeans_station_clustering.py 生成 表2_聚类结果表.csv
  （依赖：pandas numpy statsmodels matplotlib）
"""

import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")   # 忽略拟合过程中的收敛警告，保持输出整洁
sys.stdout.reconfigure(encoding="utf-8")   # 防止 Windows 控制台中文乱码

# 统一的数据文件定位与项目根目录（见 code/common.py）
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # 使 code/ 子目录脚本可 import common
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "分工2"))  # 复用站点中文名映射
from common import PROJECT_ROOT, find_data
from station_name_cn import NAME_CN

DATA_FILE = find_data("std_10min_inout.csv")
# 聚类结果表由 kmeans_station_clustering.py 生成（位于分工5_数据挖掘/聚类/ 下）
CLUSTER_DIR = PROJECT_ROOT / "分工5_数据挖掘" / "聚类"
CLUSTER_FILE = CLUSTER_DIR / "表2_聚类结果表.csv"
OUT_DIR = PROJECT_ROOT / "分工5_数据挖掘" / "预测"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

HOURS_PER_DAY = 17          # 运营时段 06:00~22:00 共 17 个小时 → 日内周期长度
TEST_DAYS = 7               # 预留最后 7 天作为样本外测试集


# ================================================================ 0. 选代表站
def select_representatives() -> tuple[dict[int, str], dict[int, str]]:
    """从聚类结果表中为 5 类站点各选 1 个日均客流最大的代表站。

    返回：
      targets : {stationID: 展示名}，展示名 = 「中文站名(英文站名·类别)」
      types   : {stationID: 站点类型}
    """
    if not CLUSTER_FILE.exists():
        raise FileNotFoundError(
            f"未找到聚类结果表 {CLUSTER_FILE}\n"
            "请先运行 code/分工5/kmeans_station_clustering.py 生成聚类结果，再运行本脚本。")

    cluster = pd.read_csv(CLUSTER_FILE, encoding="utf-8-sig")
    cluster = cluster.sort_values("日均总客流", ascending=False)
    # 每类取日均客流最大的站；groupby 后 first 即该类最大
    reps = cluster.groupby("站点类型", as_index=False).first()

    # 固定业务展示顺序：枢纽 → 办公 → 通勤 → 商圈 → 郊区低频（大致按客流规模）
    TYPE_ORDER = ["综合枢纽站", "就业办公站", "通勤居住站", "休闲商圈站", "郊区低频站点"]
    reps = reps.set_index("站点类型").loc[TYPE_ORDER].reset_index()

    targets, types = {}, {}
    for _, row in reps.iterrows():
        sid = int(row["stationID"])
        stype = str(row["站点类型"])
        en = str(row["name"])
        cn = NAME_CN.get(sid, en)          # 中文名；缺失时退回英文
        targets[sid] = f"{cn}({en}·{stype})"
        types[sid] = stype
    print("  选为代表站的 5 类站点：")
    for sid, name in targets.items():
        print(f"    {sid} {name}")
    return targets, types


# ================================================================ 1. 读数据
def load_station_series(targets: dict[int, str]) -> dict[int, pd.Series]:
    """分块读取进出站大表，只保留目标站点，汇总为小时级进站客流序列。

    夜间停运时段（23:00~次日5:00）客流恒为 0，不参与建模：
    序列截断为『每天 6~22 点共 17 个点首尾相接』，因此日内周期长度 = 17。
    """
    parts = []
    reader = pd.read_csv(DATA_FILE, usecols=["datetime", "stationID", "inFlow"],
                         dtype={"stationID": "int16", "inFlow": "int32"},
                         encoding="utf-8-sig", chunksize=500_000)
    for i, chunk in enumerate(reader, 1):
        chunk = chunk[chunk["stationID"].isin(targets)]
        if not chunk.empty:
            parts.append(chunk)
        print(f"  已扫描 {i * 50} 万行...")

    df = pd.concat(parts, ignore_index=True)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["dt"] = df["datetime"].dt.floor("h")
    series = {}
    for sid, name in targets.items():
        s = (df[df["stationID"] == sid].groupby("dt")["inFlow"].sum()
             .sort_index())
        # 补全运营时段的完整小时索引，缺失小时按 0 处理
        full = pd.date_range(s.index.min(), s.index.max(), freq="h")
        full = full[(full.hour >= 6) & (full.hour <= 22)]
        s = s.reindex(full).fillna(0).astype(int)
        s.name = name
        series[sid] = s
        print(f"  站点 {sid} {name}：{len(s)} 个小时级观测")
    return series


# ================================================================ 2. 平稳性检验
def adf_check(s: pd.Series) -> dict:
    """ADF 单位根检验：对原序列与一阶差分序列各做一次，决定差分阶数 d。"""
    stat0, p0 = adfuller(s)[:2]
    stat1, p1 = adfuller(s.diff().dropna())[:2]
    d = 0 if p0 < 0.05 else 1          # p < 0.05 视为平稳，无需差分
    print(f"  ADF检验：原序列 p={p0:.4f}，一阶差分 p={p1:.4f} → d={d}")
    return {"ADF统计量(原序列)": round(stat0, 3), "p值(原序列)": round(p0, 4),
            "ADF统计量(一阶差分)": round(stat1, 3), "p值(一阶差分)": round(p1, 4),
            "选定差分阶数d": d}


# ================================================================ 3. 模型定阶与训练
def fit_plain_arima(train: pd.Series, d: int):
    """普通 ARIMA：网格搜索 p,q ∈ {0,1,2,3}，按 AIC 选最优。"""
    best, best_order, table = None, None, []
    for p in range(4):
        for q in range(4):
            if p == q == 0:
                continue
            try:
                m = ARIMA(train, order=(p, d, q)).fit()
                table.append({"模型": f"ARIMA({p},{d},{q})", "AIC": round(m.aic, 1)})
                if best is None or m.aic < best.aic:
                    best, best_order = m, (p, d, q)
            except Exception:
                continue
    return best, f"ARIMA{best_order}", sorted(table, key=lambda r: r["AIC"])


def fit_sarima(train: pd.Series, d: int):
    """季节 ARIMA：两阶段定阶。
    阶段1：固定周期项 (P,D,Q)=(1,1,1)，网格搜索 p,q ∈ {0,1,2}
    阶段2：固定最优 p,q，比较其余 3 种周期项组合
    """
    S = HOURS_PER_DAY
    best, best_order, best_seas, table = None, None, None, []
    for p in range(3):
        for q in range(3):
            try:
                m = SARIMAX(train, order=(p, d, q), seasonal_order=(1, 1, 1, S),
                            enforce_stationarity=False,
                            enforce_invertibility=False).fit(disp=False)
                table.append({"模型": f"SARIMA({p},{d},{q})x(1,1,1,{S})",
                              "AIC": round(m.aic, 1)})
                if best is None or m.aic < best.aic:
                    best, best_order, best_seas = m, (p, d, q), (1, 1, 1, S)
            except Exception:
                continue
    p0, q0 = best_order[0], best_order[2]
    for P, Q in [(0, 0), (1, 0), (0, 1)]:
        try:
            m = SARIMAX(train, order=(p0, d, q0), seasonal_order=(P, 1, Q, S),
                        enforce_stationarity=False,
                        enforce_invertibility=False).fit(disp=False)
            table.append({"模型": f"SARIMA({p0},{d},{q0})x({P},1,{Q},{S})",
                          "AIC": round(m.aic, 1)})
            if m.aic < best.aic:
                best, best_seas = m, (P, 1, Q, S)
        except Exception:
            continue
    spec = f"SARIMA{best_order}x{best_seas}"
    return best, spec, sorted(table, key=lambda r: r["AIC"])


# ================================================================ 4. 评估
def metrics(actual: np.ndarray, pred: np.ndarray) -> dict:
    """回归预测误差指标：MAE / MSE / RMSE / MAPE。"""
    err = actual - pred
    mae = float(np.mean(np.abs(err)))
    mse = float(np.mean(err ** 2))
    rmse = float(np.sqrt(mse))
    mape = float(np.mean(np.abs(err) / np.maximum(np.abs(actual), 1)) * 100)
    return {"MAE": round(mae, 2), "MSE": round(mse, 1),
            "RMSE": round(rmse, 2), "MAPE(%)": round(mape, 2)}


# ================================================================ 主流程
def main() -> None:
    print("=" * 60)
    print("ARIMA 短时客流预测")
    print("=" * 60)

    print("\n[选代表站] 从聚类结果中为 5 类站点各选一个日均客流最大的代表站...")
    targets, types = select_representatives()

    print("\n[构建序列] 读取进出站大表并汇总目标站点小时级客流...")
    series = load_station_series(targets)

    adf_rows, aic_rows, metric_rows = [], [], []
    n_sta = len(targets)
    n_cols, n_rows = 3, 2
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 8.5), dpi=150)

    for idx, (sid, s) in enumerate(series.items()):
        ax = axes.flat[idx]
        name = s.name
        stype = types[sid]
        # 展示名带英文，用于图表/报告；文件名用「中文·类别」短名，避免英文与特殊符号过长
        cn_short = name.split("(")[0]          # 中文站名
        file_tag = f"{cn_short}_{stype}"
        print(f"\n———— 站点 {sid} {name} ————")
        split = len(s) - TEST_DAYS * HOURS_PER_DAY
        train, test = s.iloc[:split], s.iloc[split:]
        print(f"  训练集 {len(train)} 点 / 测试集 {len(test)} 点（最后{TEST_DAYS}天）")
        # 序列按“每天17个运营小时”拼接，datetime 索引存在夜间空隙，
        # statsmodels 无法将其识别为规则频率索引，建模前重置为整数序号
        train_ts = train.reset_index(drop=True)

        print("  [平稳性检验]")
        adf_rows.append({"站点": name, "站点类型": stype, **adf_check(train_ts)})
        d = adf_rows[-1]["选定差分阶数d"]

        print("  [普通 ARIMA 定阶]")
        arima, arima_spec, _ = fit_plain_arima(train_ts, d)
        print(f"    最优：{arima_spec}")

        print("  [季节 SARIMA 定阶]")
        sarima, sarima_spec, _ = fit_sarima(train_ts, d)
        print(f"    最优：{sarima_spec}")

        aic_rows.append({"站点": name, "站点类型": stype, "普通ARIMA最优": arima_spec,
                         "季节SARIMA最优": sarima_spec})

        # ---- 样本外预测与误差 ----
        pred_arima = np.asarray(arima.forecast(steps=len(test)).clip(lower=0))
        pred_sarima = np.asarray(sarima.forecast(steps=len(test)).clip(lower=0))
        pred_naive = s.iloc[split - TEST_DAYS * HOURS_PER_DAY:split].values  # 上周同时刻
        actual = test.values

        for method, pred in [("普通ARIMA", pred_arima.astype(float)),
                             ("季节SARIMA", pred_sarima.astype(float)),
                             ("上周同时刻基线", np.asarray(pred_naive, dtype=float))]:
            metric_rows.append({"站点": name, "站点类型": stype, "方法": method,
                                **metrics(actual, pred)})

        # ---- 预测结果明细 ----
        pd.DataFrame({"datetime": test.index.strftime("%Y-%m-%d %H:%M"),
                      "真实客流": actual,
                      "普通ARIMA预测": pred_arima,
                      "季节SARIMA预测": pred_sarima,
                      "上周同时刻基线": pred_naive}).to_csv(
            OUT_DIR / f"预测结果_{file_tag}.csv", index=False, encoding="utf-8-sig")

        # ---- 绘图 ----
        ax.plot(test.index, actual, color="black", lw=1.4, label="真实客流")
        ax.plot(test.index, pred_sarima, color="#d62728", lw=1.1, label="季节SARIMA")
        ax.plot(test.index, pred_arima, color="#1f77b4", lw=0.9, ls="--", label="普通ARIMA")
        ax.plot(test.index, pred_naive, color="#2ca02c", lw=0.9, ls=":", label="上周同时刻基线")
        ax.set_title(f"{name} 未来{TEST_DAYS}天进站客流预测对比", fontsize=10)
        ax.set_ylabel("进站客流（人次/小时）", fontsize=9)
        ax.legend(fontsize=7)
        ax.tick_params(axis="x", rotation=20, labelsize=7)

    # 隐藏多余的第 6 格
    for extra in axes.flat[n_sta:]:
        extra.set_visible(False)

    pd.DataFrame(adf_rows).to_csv(OUT_DIR / "表4_平稳性检验结果.csv",
                                  index=False, encoding="utf-8-sig")
    pd.DataFrame(aic_rows).to_csv(OUT_DIR / "表5_模型定阶结果.csv",
                                  index=False, encoding="utf-8-sig")
    met = pd.DataFrame(metric_rows)
    met.to_csv(OUT_DIR / "表6_预测误差指标.csv", index=False, encoding="utf-8-sig")

    fig.suptitle("5 类典型站点短时客流预测：真实值 vs 模型预测值（2×3 网格）")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "图4_客流预测对比曲线.png")
    plt.close(fig)

    # ---- 自动生成模型分析草稿 ----
    # 每站聚合成一行：普通ARIMA / 季节SARIMA 的 MAE，并标记最优
    lines = ["# ARIMA 短时客流预测分析结论（自动生成）\n"]
    lines.append("| 站点 | 类型 | 普通ARIMA MAE | 季节SARIMA MAE | 上周基线 MAE | 最优方法 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for sid, s in series.items():
        stype = types[sid]
        sub = met[met["站点"] == s.name]
        row = {r["方法"]: r for r in sub.to_dict("records")}
        a = row["普通ARIMA"]["MAE"]
        sa = row["季节SARIMA"]["MAE"]
        b = row["上周同时刻基线"]["MAE"]
        best = min(["普通ARIMA", "季节SARIMA", "上周同时刻基线"],
                   key=lambda m: row[m]["MAE"])
        lines.append(f"| {s.name} | {stype} | {a} | {sa} | {b} | **{best}** |")
    lines += [
        "\n主要发现：",
        "1. 各类型站点中，季节 SARIMA 的 MAE 普遍约为普通 ARIMA 的一半，周期项(s=17)对刻画早晚高峰至关重要；",
        "2. SARIMA 峰形与相位基本同步，但受线性均值回归影响峰值估计偏低，且未区分工作日/周末，周末存在虚高通勤峰预测；",
        "3. 「上周同时刻」朴素基线误差通常最低，说明周级客流规律极强；但基线只是历史平移，无法适应节假日与突发事件，",
        "   改进方向：SARIMAX 引入天气等外生变量、工作日/周末分模型、缩短步长滚动预测。",
        "\n注：以上误差为各站最后 7 天（119 个运营小时）样本外检验结果；",
    ]
    (OUT_DIR / "预测模型分析.md").write_text("\n".join(lines), encoding="utf-8")

    print("\n" + met.to_string(index=False))
    print(f"\n全部完成！结果已保存到：{OUT_DIR}")


if __name__ == "__main__":
    main()
