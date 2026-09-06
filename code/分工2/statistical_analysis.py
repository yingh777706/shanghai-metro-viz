# -*- coding: utf-8 -*-
"""
分工2 · 客流时空特征统计分析（业务分析）
================================================================
功能：
  基于分工1 输出的标准化数据集，完成全维度描述性统计，提炼客流时空分布规律：
    1. 全局描述性统计：总客运量、日均客运量、单站客流极值
    2. 时间维度：工作日/周末差异、早晚高峰识别、周内波动、月度变化
    3. 空间维度：站点客流排名、线路客流强度（换乘站按线均摊）、城区/郊区差异
    4. 出行指标：基于 18G OD 表 + od_travel_time.csv，分块计算平均出行距离/时长/换乘次数

运行方式：
  python statistical_analysis.py            # 完整运行（含 18G OD 表，较慢）
  python statistical_analysis.py --skip-od  # 跳过 OD，快速跑通前四部分
  数据文件位于 data/ 或 processed_data/ 或 docs/processed_data/ 任一目录即可。

依赖：pandas numpy matplotlib（见根目录 requirements.txt）
"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")                 # 无界面环境绘图，直接保存图片
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- 路径配置
# 统一的数据文件定位与项目根目录（见 code/common.py）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # 使 code/ 子目录脚本可 import common
from common import PROJECT_ROOT, find_data
from station_name_cn import NAME_CN      # 站点中文名映射（本目录同目录）

DATA_INOUT = find_data("std_10min_inout.csv")
DATA_OD = find_data("std_10min_od.csv")
DATA_STATION = find_data("station_info.csv")
DATA_CAL = find_data("workday_calendar.csv")
DATA_LINE = find_data("station_line_map.csv")      # 站点→线路映射（分工1）
DATA_AREA = find_data("station_area_class.csv")    # 城区/郊区分类（分工1）
DATA_TIME = find_data("od_travel_time.csv")        # OD 出行时长（分工1）

OUT_DIR = PROJECT_ROOT / "分工2_统计分析"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
sys.stdout.reconfigure(encoding="utf-8")

CHUNK = 500_000                       # 分块读取行数
SKIP_OD = "--skip-od" in sys.argv     # 是否跳过 18G OD 表（快速测试用）

# 星期英文 -> 中文（用于周内波动排序）
WEEKDAY_CN = {
    "Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
    "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日",
}
WEEKDAY_ORDER = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


# ================================================================ 数据读取
def load_small(path: Path) -> pd.DataFrame:
    """读取小体积 CSV（站点信息 / 工作日日历），统一处理 BOM。"""
    return pd.read_csv(path, encoding="utf-8-sig")


def load_hourly_flow() -> pd.DataFrame:
    """分块读取进出站表，聚合为『站点 × 日期 × 小时』粒度。

    原表约 379 万行（302 站 × 123 天 × 108 个10分钟时段），分块 groupby
    后压缩为约 67 万行，避免内存不足。返回列：date, stationID, hour, inFlow, outFlow。
    """
    cols = ["date", "startTime", "stationID", "inFlow", "outFlow"]
    dtypes = {"date": "int64", "stationID": "int16",
              "inFlow": "int32", "outFlow": "int32"}
    parts = []
    reader = pd.read_csv(DATA_INOUT, usecols=cols, dtype=dtypes,
                         encoding="utf-8-sig", chunksize=CHUNK)
    for chunk in reader:
        chunk["hour"] = chunk["startTime"].str.slice(0, 2).astype(int)
        g = (chunk.groupby(["date", "stationID", "hour"], sort=False)
                  [["inFlow", "outFlow"]].sum())
        parts.append(g.reset_index())
    df = pd.concat(parts, ignore_index=True)
    # 再聚合一次：防止同一 (date, stationID, hour) 被分块边界拆开
    return (df.groupby(["date", "stationID", "hour"], sort=False)
              [["inFlow", "outFlow"]].sum().reset_index())


# ================================================================ 1. 全局描述性统计
def global_stats(flow: pd.DataFrame) -> dict:
    """总客运量、日均客运量、单站客流极值。客运量以『进站量』口径统计。"""
    daily = flow.groupby("date")[["inFlow", "outFlow"]].sum()
    total_in = int(daily["inFlow"].sum())
    total_out = int(daily["outFlow"].sum())
    n_days = int(len(daily))

    # 单站总客流（进站+出站），用于极值
    station = flow.groupby("stationID")[["inFlow", "outFlow"]].sum()
    station["total"] = station["inFlow"] + station["outFlow"]
    station = station.merge(load_small(DATA_STATION)[["stationID", "name"]],
                            on="stationID", how="left")
    top = station.nlargest(10, "total")
    bottom = station.nsmallest(5, "total")

    print(f"  总进站量 = {total_in:,}  总出站量 = {total_out:,}  天数 = {n_days}")
    print(f"  日均进站量 = {total_in / n_days:,.0f}")

    # 保存全局指标汇总表
    summary = pd.DataFrame({
        "指标": ["总进站量", "总出站量", "统计天数", "日均进站量"],
        "数值": [total_in, total_out, n_days, round(total_in / n_days, 0)],
    })
    summary.to_csv(OUT_DIR / "表1_全局指标.csv", index=False, encoding="utf-8-sig")

    return {
        "总进站量": total_in, "总出站量": total_out, "统计天数": n_days,
        "日均进站量": round(total_in / n_days, 0),
        "客流最大站点": top.iloc[0]["name"], "客流最小站点": bottom.iloc[0]["name"],
    }


# ================================================================ 2. 时间维度
def time_stats(flow: pd.DataFrame) -> dict:
    """工作日/周末差异、早晚高峰、周内波动、月度变化。"""
    cal = load_small(DATA_CAL)[["date", "isWorkday", "weekday"]]
    flow = flow.merge(cal, on="date", how="left")
    flow["weekday_cn"] = flow["weekday"].map(WEEKDAY_CN)
    flow["month"] = (flow["date"] // 100) % 100          # 20170501 -> 5

    # (a) 工作日 / 周末日均进站量
    wd = flow.groupby("isWorkday")["inFlow"].sum()
    n_wd = int((cal["isWorkday"] == 1).sum())            # 工作日天数
    n_we = int((cal["isWorkday"] == 0).sum())            # 周末天数
    avg_workday = wd.get(1, 0) / n_wd if n_wd else 0
    avg_weekend = wd.get(0, 0) / n_we if n_we else 0

    wd_we = pd.DataFrame({
        "类型": ["工作日", "周末"],
        "天数": [n_wd, n_we],
        "日均进站量": [round(avg_workday, 0), round(avg_weekend, 0)],
    })
    wd_we.to_csv(OUT_DIR / "表3_工作日周末对比.csv", index=False, encoding="utf-8-sig")

    # (b) 分时进站量，识别早晚高峰
    hourly = flow.groupby("hour")["inFlow"].sum().reset_index()
    hourly.to_csv(OUT_DIR / "表4_分时客流.csv", index=False, encoding="utf-8-sig")
    morning = hourly[hourly["hour"].between(6, 10)]
    evening = hourly[hourly["hour"].between(16, 20)]
    peak_am = int(morning.loc[morning["inFlow"].idxmax(), "hour"])
    peak_pm = int(evening.loc[evening["inFlow"].idxmax(), "hour"])

    # (c) 周内波动（各星期日均进站量 = 该星期总进站量 / 该星期出现天数）
    week = flow.groupby("weekday_cn")["inFlow"].sum().reset_index()
    week_days = (flow.groupby("weekday_cn")["date"].nunique()
                    .reset_index().rename(columns={"date": "天数"}))
    week = week.merge(week_days, on="weekday_cn", how="left")
    week["日均进站量"] = (week["inFlow"] / week["天数"]).round(0)
    week["weekday_cn"] = pd.Categorical(week["weekday_cn"], categories=WEEKDAY_ORDER, ordered=True)
    week = week.sort_values("weekday_cn")
    week.to_csv(OUT_DIR / "表5_周内波动.csv", index=False, encoding="utf-8-sig")

    # (d) 月度变化
    month = flow.groupby("month")["inFlow"].sum().reset_index()
    month.columns = ["月份", "总进站量"]
    month.to_csv(OUT_DIR / "表6_月度变化.csv", index=False, encoding="utf-8-sig")

    print(f"  工作日日均进站 = {avg_workday:,.0f}  周末日均进站 = {avg_weekend:,.0f}"
          f"  早高峰 {peak_am} 时  晚高峰 {peak_pm} 时")

    return {
        "工作日日均进站": round(avg_workday, 0), "周末日均进站": round(avg_weekend, 0),
        "早高峰时段": f"{peak_am}:00", "晚高峰时段": f"{peak_pm}:00",
        "月度最高": int(month["总进站量"].max()), "月度最低": int(month["总进站量"].min()),
    }


# ================================================================ 3. 空间维度
def station_rank(flow: pd.DataFrame) -> dict:
    """站点客流排名（进站量口径），含站点名映射。"""
    station = flow.groupby("stationID")["inFlow"].sum().reset_index()
    station.columns = ["stationID", "总进站量"]
    station = station.merge(load_small(DATA_STATION)[["stationID", "name"]],
                            on="stationID", how="left")
    station["中文名"] = station["stationID"].map(NAME_CN)
    station = station.sort_values("总进站量", ascending=False).reset_index(drop=True)
    station.to_csv(OUT_DIR / "表2_站点客流排名.csv", index=False, encoding="utf-8-sig")
    top = station.head(10)
    print("  进站量前 3：", ", ".join(f"{r['name']}({r['总进站量']:,})" for _, r in top.head(3).iterrows()))
    return {"客流最大站点": top.iloc[0]["name"], "客流最小站点": station.iloc[-1]["name"]}


# ================================================================ 3b. 线路客流强度
def line_strength(flow: pd.DataFrame) -> dict:
    """各线路客流强度（进站量口径），换乘站进站量按经过线路数均摊。

    依据分工1 的 station_line_map.csv（stationID → line，换乘站一行一条）。
    返回 {'最繁忙线路': ...} 供结论引用。
    """
    n_days = int(flow["date"].nunique())
    line_map = load_small(DATA_LINE)          # stationID, name, line, is_transfer

    st = (flow.groupby("stationID")["inFlow"].sum()
             .reset_index().rename(columns={"inFlow": "总进站量"}))
    m = st.merge(line_map[["stationID", "line"]], on="stationID", how="left")

    # 换乘站分摊：该站进站量均分到它经过的每条线路，避免重复计入
    n_lines = m.groupby("stationID")["line"].transform("count")
    m["分摊进站量"] = m["总进站量"] / n_lines

    line = (m.groupby("line", as_index=False)
             .agg(站点数=("stationID", "nunique"),
                  总进站量=("总进站量", "sum"),
                  分摊进站量=("分摊进站量", "sum")))
    line = line.dropna(subset=["line"]).reset_index(drop=True)
    line["line"] = line["line"].astype(int)
    line["分摊进站量"] = line["分摊进站量"].round(0).astype("int64")
    line["日均进站量(分摊)"] = (line["分摊进站量"] / n_days).round(0).astype("int64")
    line["单站日均进站量"] = (line["分摊进站量"] / line["站点数"] / n_days).round(0).astype("int64")
    line = line.sort_values("分摊进站量", ascending=False).reset_index(drop=True)
    line.to_csv(OUT_DIR / "表7_线路客流强度.csv", index=False, encoding="utf-8-sig")

    top = line.iloc[0]
    print(f"  线路客流强度：Line {int(top['line'])} 最繁忙（分摊进站 {int(top['分摊进站量']):,}，"
          f"单站日均 {int(top['单站日均进站量']):,}）")
    return {"最繁忙线路": f"Line {int(top['line'])}",
            "最繁忙线路单站日均": int(top["单站日均进站量"])}


# ================================================================ 3c. 城区/郊区差异
def area_diff(flow: pd.DataFrame) -> dict:
    """核心城区 / 城区过渡 / 郊区 的客流规模与「工作日/周末」时间模式对比。

    依据分工1 的 station_area_class.csv 的 core_suburb 三分类。
    返回 {'单站日均最高区': ..., '工作日周末比_核心城区': ...} 供结论引用。
    """
    n_days = int(flow["date"].nunique())
    cal = load_small(DATA_CAL)[["date", "isWorkday"]]
    area = load_small(DATA_AREA)[["stationID", "core_suburb", "ring"]]

    st = (flow.groupby("stationID")["inFlow"].sum()
             .reset_index().rename(columns={"inFlow": "总进站量"}))
    m = st.merge(area, on="stationID", how="left")

    # (a) 规模对比：单站日均进站量
    g = (m.groupby("core_suburb", as_index=False)
          .agg(站点数=("stationID", "nunique"), 总进站量=("总进站量", "sum")))
    g["单站日均进站量"] = (g["总进站量"] / g["站点数"] / n_days).round(0).astype("int64")
    g = g.sort_values("单站日均进站量", ascending=False).reset_index(drop=True)
    g.to_csv(OUT_DIR / "表8_城区郊区对比.csv", index=False, encoding="utf-8-sig")

    # (b) 工作日/周末单站日均对比（验证「中心城区通勤主导、郊区低频」）
    n_wd = int((cal["isWorkday"] == 1).sum())
    n_we = int((cal["isWorkday"] == 0).sum())
    wd = (flow.merge(cal, on="date", how="left")
             .groupby(["stationID", "isWorkday"], as_index=False)["inFlow"].sum()
             .merge(area, on="stationID", how="left"))
    p = (wd.groupby(["core_suburb", "isWorkday"], as_index=False)["inFlow"].sum()
           .pivot(index="core_suburb", columns="isWorkday", values="inFlow"))
    p = p.rename(columns={0: "周末总进站", 1: "工作日总进站"})
    n_station = m.groupby("core_suburb")["stationID"].nunique()
    p["工作日单站日均"] = (p["工作日总进站"] / n_station / n_wd).round(0).astype("int64")
    p["周末单站日均"] = (p["周末总进站"] / n_station / n_we).round(0).astype("int64")
    p["工作日/周末比值"] = (p["工作日单站日均"] / p["周末单站日均"]).round(2)
    p = p.reset_index()
    p.to_csv(OUT_DIR / "表8b_城区郊区工作日周末.csv", index=False, encoding="utf-8-sig")

    core_row = g.iloc[0]
    print(f"  城区差异：{core_row['core_suburb']} 单站日均 {int(core_row['单站日均进站量']):,} 最高")
    return {"单站日均最高区": core_row["core_suburb"],
            "核心城区工作日周末比": round(float(p.loc[p["core_suburb"] == "核心城区", "工作日/周末比值"].iloc[0]), 2),
            "郊区工作日周末比": round(float(p.loc[p["core_suburb"] == "郊区", "工作日/周末比值"].iloc[0]), 2)}


# ================================================================ 4. 平均出行距离（分块，重）
def haversine_km(lat1, lon1, lat2, lon2):
    """球面距离（haversine），单位公里，向量化实现。"""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(a))


def od_metrics() -> dict:
    """分块读取 18G OD 表，聚合为 OD 对 → 总流量，算加权平均出行距离与时长。

    平均出行距离 = Σ(Flow_od × dist_od) / Σ(Flow_od)，dist_od 为起终点站
    经纬度球面距离。平均出行时长 = Σ(Flow_od × est_time_min) / Σ(Flow_od)，
    est_time_min 来自分工1 的 od_travel_time.csv。先按 OD 对聚合（最多约
    302×302 对），再算指标，避免对 2.67 亿行逐行做球面距离运算。
    """
    station = load_small(DATA_STATION)[["stationID", "lon", "lat"]]
    coord = {int(r.stationID): (float(r.lat), float(r.lon)) for _, r in station.iterrows()}

    cols = ["originStation", "destinationStation", "Flow"]
    dtypes = {"originStation": "int16", "destinationStation": "int16", "Flow": "int32"}
    parts = []
    print("  正在分块读取 OD 表（18G，约 2.67 亿行）……")
    reader = pd.read_csv(DATA_OD, usecols=cols, dtype=dtypes,
                         encoding="utf-8-sig", chunksize=CHUNK)
    for i, chunk in enumerate(reader, 1):
        g = chunk.groupby(["originStation", "destinationStation"], sort=False)["Flow"].sum()
        parts.append(g.reset_index())
        if i % 100 == 0:
            print(f"    已处理 {i * CHUNK:,} 行")
    od = pd.concat(parts, ignore_index=True)
    od = od.groupby(["originStation", "destinationStation"], sort=False)["Flow"].sum().reset_index()
    total_flow = int(od["Flow"].sum())

    # (a) 加权平均出行距离（需经纬度齐全的站点对）
    ok = od["originStation"].isin(coord) & od["destinationStation"].isin(coord)
    d = od[ok]
    lat1 = d["originStation"].map(lambda s: coord[s][0]).to_numpy()
    lon1 = d["originStation"].map(lambda s: coord[s][1]).to_numpy()
    lat2 = d["destinationStation"].map(lambda s: coord[s][0]).to_numpy()
    lon2 = d["destinationStation"].map(lambda s: coord[s][1]).to_numpy()
    dist = haversine_km(lat1, lon1, lat2, lon2)
    avg_dist = float(np.average(dist, weights=d["Flow"].to_numpy()))

    # (b) 加权平均出行时长 / 换乘次数（合并分工1 od_travel_time.csv）
    time = load_small(DATA_TIME)[["originStation", "destinationStation", "est_time_min", "n_transfers"]]
    od = od.merge(time, on=["originStation", "destinationStation"], how="left")
    has_t = od["est_time_min"].notna()
    covered = float(od.loc[has_t, "Flow"].sum() / total_flow)
    avg_time = float(np.average(od.loc[has_t, "est_time_min"].to_numpy(),
                                weights=od.loc[has_t, "Flow"].to_numpy()))
    avg_transfers = float(np.average(od.loc[has_t, "n_transfers"].to_numpy(),
                                     weights=od.loc[has_t, "Flow"].to_numpy()))

    print(f"  加权平均出行距离 = {avg_dist:.2f} km（总 OD 流量 {total_flow:,}）")
    print(f"  加权平均出行时长 = {avg_time:.2f} 分钟（覆盖 {covered:.1%} 流量）")
    print(f"  加权平均换乘次数 = {avg_transfers:.2f} 次")

    pd.DataFrame({
        "指标": ["加权平均出行距离(km)", "加权平均出行时长(min)", "加权平均换乘次数", "时长覆盖流量占比"],
        "数值": [round(avg_dist, 2), round(avg_time, 2), round(avg_transfers, 2), round(covered, 4)],
    }).to_csv(OUT_DIR / "表9_出行指标.csv", index=False, encoding="utf-8-sig")

    return {
        "平均出行距离_km": round(avg_dist, 2),
        "平均出行时长_min": round(avg_time, 2),
        "平均换乘次数": round(avg_transfers, 2),
    }


# ================================================================ 汇总输出
def write_conclusion(results: dict) -> None:
    """把各维度结果汇总成一份统计结论 Markdown。"""
    lines = [
        "# 客流时空特征统计分析结论（分工2）",
        "",
        "## 1. 全局描述性统计",
        f"- 总进站量（客运量）：{results['总进站量']:,} 人次",
        f"- 总出站量：{results['总出站量']:,} 人次",
        f"- 统计天数：{results['统计天数']} 天（2017-05-01 ~ 2017-08-31）",
        f"- 日均进站量：{results['日均进站量']:,.0f} 人次",
        "",
        "## 2. 时间维度",
        f"- 工作日日均进站：{results['工作日日均进站']:,.0f} 人次",
        f"- 周末日均进站：{results['周末日均进站']:,.0f} 人次",
        f"- 早高峰时段：{results['早高峰时段']}，晚高峰时段：{results['晚高峰时段']}",
        "",
        "## 3. 空间维度",
        f"- 进站量最大站点：{results['客流最大站点']}",
        f"- 进站量最小站点：{results['客流最小站点']}",
        f"- 最繁忙线路：{results['最繁忙线路']}（单站日均进站 {results['最繁忙线路单站日均']:,} 人次，详见 表7）",
        f"- 单站日均进站最高的区域：{results['单站日均最高区']}（详见 表8/表8b）",
        "",
        "## 4. 出行距离与时耗",
        f"- 加权平均出行距离（站点间球面直线距离）：{results['平均出行距离_km']} km",
        f"- 加权平均出行时长（按 OD 流量加权）：{results['平均出行时长_min']} 分钟",
        f"- 加权平均换乘次数：{results['平均换乘次数']} 次",
        "- 注：出行距离为起终点站经纬度的球面直线距离（非沿轨道实际路径）；出行时长/换乘来自分工1 `od_travel_time.csv`",
        "",
        "## 5. 业务归因解读",
        "- **周五全周最高、周日最低**：周五叠加「工作日通勤」与「下班后晚间休闲/离沪出行」双重需求，日均进站 681 万人次居全周之首；周日（431 万）缺少刚性通勤、以休闲出行为主，为全周谷底。",
        "- **月度先降后升、8 月达峰**：6 月为低谷（1.70 亿人次），受梅雨季出行意愿下降与学期末出行减少影响；7 月起进入暑期，旅游、返乡、休闲出行叠加，客流逐月攀升，8 月（1.94 亿人次）达样本期峰值。",
        "- **人民广场（People's Square）断层第一**：全期进站约 1800 万人次，约为次席徐家汇（1194 万）的 1.5 倍，源于 1/2/8 号线三线换乘 + 市政府/南京东路商圈 + 旅游核心区位的多重叠加。",
        "- **通勤主导结构**：工作日日均 651 万较周末 451 万高约 44%，且早高峰（8:00）显著强于晚高峰（17:00），印证「早晚高峰通勤」是全网客流主体。",
        f"- **线路强度分化**：{results['最繁忙线路']} 为全网最繁忙线路，主城区干线与郊区末端支线（如 5/16 号线）单站客流强度落差明显（详见 表7）。",
        f"- **城区/郊区梯度**：{results['单站日均最高区']}单站日均进站最高；核心城区「工作日/周末」比值约 {results['核心城区工作日周末比']}、郊区约 {results['郊区工作日周末比']}，印证中心城区通勤主导、郊区低频长距离出行的结构。",
        "",
        "## 6. 数据补齐说明（分工1 已交付）",
        "- 平均出行时长：由 `od_travel_time.csv`（`est_time_min` 字段）补齐",
        "- 线路客流强度：由 `station_line_map.csv` 补齐",
        "- 核心城区 vs 郊区差异：由 `station_area_class.csv`（`core_suburb`/`ring` 字段）补齐",
        "- 另收到 `weather_hourly.csv`（逐小时天气），可支撑后续「天气对客流影响」分析",
    ]
    (OUT_DIR / "统计分析结论.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n结果已输出到 {OUT_DIR}")


# ================================================================ 主流程
def main() -> None:
    print("=" * 60)
    print("分工2 · 客流时空特征统计分析")
    print(f"数据目录：{DATA_INOUT.parent}")
    print("=" * 60)

    print("\n[1/5] 读取进出站客流表并聚合……")
    flow = load_hourly_flow()
    print(f"  聚合后 {len(flow):,} 行")

    print("\n[2/5] 全局描述性统计……")
    g = global_stats(flow)

    print("\n[3/5] 时间维度分析……")
    t = time_stats(flow)

    print("\n[4/5] 空间维度 · 站点排名 / 线路强度 / 城区郊区……")
    s = station_rank(flow)
    l = line_strength(flow)
    a = area_diff(flow)

    results = {**g, **t, **s, **l, **a}

    if not SKIP_OD:
        print("\n[5/5] 出行距离与时耗（分块处理 18G OD 表）……")
        results.update(od_metrics())
    else:
        results["平均出行距离_km"] = "（--skip-od 跳过）"
        results["平均出行时长_min"] = "（--skip-od 跳过）"
        results["平均换乘次数"] = "（--skip-od 跳过）"
        print("\n[5/5] 已跳过出行距离与时耗计算（--skip-od）")

    write_conclusion(results)
    print("\n完成。")


if __name__ == "__main__":
    main()
