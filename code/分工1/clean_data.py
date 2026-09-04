# -*- coding: utf-8 -*-
"""
上海地铁刷卡数据清洗脚本（2017-05 ~ 2017-08）

清洗 raw_data/ 下五个 CSV，输出到 processed_data/：
  1. stationInfo.csv          -> station_info.csv
  2. workday_calendar.csv     -> workday_calendar.csv
  3. shanghai_weatherHourly.csv -> weather_hourly.csv
  4. metroData_InOutFlow.csv  -> std_10min_inout.csv
  5. metroData_ODFlow.csv     -> std_10min_od.csv  (12GB, 分块处理)

修复了原 pipeline 中的若干问题：
  - 列名前导空格（", " 分隔符导致）
  - startTime/endTime 被读成 int 丢失前导零，导致 datetime 拼接失败
  - station 列名误写成 stationID
  - workday_calendar / weather / stationInfo 未真正清洗
"""

import os
import numpy as np
import pandas as pd

RAW_PATH = r"C:\Users\yzcw_\Desktop\MetroFlow_project\raw_data"
OUT_PATH = r"C:\Users\yzcw_\Desktop\MetroFlow_project\processed_data"

TIME_START = pd.Timestamp("2017-05-01 00:00:00")
TIME_END = pd.Timestamp("2017-08-31 23:59:59")
MIN_HOUR, MAX_HOUR = 5, 23  # 地铁运营时段校验范围

os.makedirs(OUT_PATH, exist_ok=True)


def _fmt_time(s: pd.Series) -> pd.Series:
    """把 60000 这种整数或 '60000' 字符串统一成 'HH:MM:SS'。"""
    s = s.astype(str).str.zfill(6)
    return s.str[:2] + ":" + s.str[2:4] + ":" + s.str[4:]


def _make_datetime(date: pd.Series, start_time: pd.Series) -> pd.Series:
    """date(YYYYMMDD) + startTime(HHMMSS) -> Timestamp。"""
    return pd.to_datetime(
        date.astype(str) + start_time.astype(str).str.zfill(6),
        format="%Y%m%d%H%M%S",
    )


def clean_station_info():
    print("\n[1/5] 清洗 stationInfo.csv ...")
    df = pd.read_csv(os.path.join(RAW_PATH, "stationInfo.csv"))
    df.columns = df.columns.str.strip()
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")])

    df["stationID"] = df["stationID"].astype(np.int32)
    df["name"] = df["name"].astype(str).str.strip()
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")

    n_before = len(df)
    # 上海经纬度范围粗校验
    df = df[(df["lon"].between(120.8, 122.2)) & (df["lat"].between(30.5, 31.6))]
    df = df.drop_duplicates(subset=["stationID"]).reset_index(drop=True)

    out = os.path.join(OUT_PATH, "station_info.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  站点数: {n_before} -> {len(df)}（剔除 {n_before - len(df)} 条异常）")
    return df


def clean_workday_calendar():
    print("\n[2/5] 清洗 workday_calendar.csv ...")
    df = pd.read_csv(os.path.join(RAW_PATH, "workday_calendar.csv"))
    df.columns = df.columns.str.strip()

    df = df.rename(columns={"isWorday": "isWorkday"})
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    df["isWorkday"] = pd.to_numeric(df["isWorkday"], errors="coerce").astype("Int8")
    df["weekday"] = df["date"].dt.day_name()

    df = df[(df["isWorkday"].isin([0, 1]))]
    df = df[(df["date"] >= TIME_START) & (df["date"] <= TIME_END)]
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

    # 输出时把 date 还原成 YYYYMMDD 整数，便于与客流表 join
    df_out = df.copy()
    df_out["date"] = df_out["date"].dt.strftime("%Y%m%d").astype(np.int32)

    out = os.path.join(OUT_PATH, "workday_calendar.csv")
    df_out.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  工作日/非工作日记录: {len(df_out)} 条（{df['isWorkday'].sum()} 个工作日）")
    return df_out


def clean_weather():
    print("\n[3/5] 清洗 shanghai_weatherHourly.csv ...")
    df = pd.read_csv(os.path.join(RAW_PATH, "shanghai_weatherHourly.csv"))
    df.columns = df.columns.str.strip()

    df["datetime"] = pd.to_datetime(df["date"], format="%Y%m%d %H:%M:%S", errors="coerce")
    df["date"] = df["datetime"].dt.strftime("%Y%m%d").astype(np.int32)
    df["hour"] = df["datetime"].dt.hour.astype(np.int8)

    for c in ["temperature_2m", "apparent_temperature", "rain", "wind_speed_10m"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    n_before = len(df)
    df = df.dropna(subset=["datetime"])
    # 雨量 / 风速不可能为负；气温做上海夏季合理区间校验
    df = df[df["rain"] >= 0]
    df = df[df["wind_speed_10m"] >= 0]
    df = df[df["temperature_2m"].between(-30, 50)]
    df = df[df["apparent_temperature"].between(-40, 60)]
    df = df.drop_duplicates(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)

    cols = ["date", "hour", "datetime",
            "temperature_2m", "apparent_temperature", "rain", "wind_speed_10m"]
    out = os.path.join(OUT_PATH, "weather_hourly.csv")
    df[cols].to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  天气记录: {n_before} -> {len(df)}（剔除 {n_before - len(df)} 条异常）")
    return df


# 客流表通用清洗逻辑（inout 与 od 共用）
FLOW_DTYPES = {
    "date": np.int32, "timeslot": np.int32, "startTime": str, "endTime": str,
}


def _clean_flow_chunk(chunk: pd.DataFrame, valid_stations: set) -> pd.DataFrame:
    """对单个 chunk 做：类型转换 + 时间/站点/流量校验。"""
    chunk["datetime"] = _make_datetime(chunk["date"], chunk["startTime"])
    chunk["startTime"] = _fmt_time(chunk["startTime"])
    chunk["endTime"] = _fmt_time(chunk["endTime"])
    chunk["date"] = chunk["date"].astype(np.int32)
    chunk["timeslot"] = chunk["timeslot"].astype(np.int32)

    hour = chunk["datetime"].dt.hour
    mask = (
        (chunk["datetime"] >= TIME_START)
        & (chunk["datetime"] <= TIME_END)
        & (hour >= MIN_HOUR) & (hour <= MAX_HOUR)
    )
    return chunk[mask]


def clean_inout_flow(valid_stations: set):
    print("\n[4/5] 清洗 metroData_InOutFlow.csv ...")
    dtype = dict(FLOW_DTYPES)
    dtype.update({
        "station": np.int32, "inFlow": np.int32, "outFlow": np.int32,
        "CinFlow": np.int32, "HBOinFlow": np.int32, "NHBinFlow": np.int32,
        "CoutFlow": np.int32, "HBOoutFlow": np.int32, "NHBoutFlow": np.int32,
    })
    df = pd.read_csv(
        os.path.join(RAW_PATH, "metroData_InOutFlow.csv"),
        skipinitialspace=True, dtype=dtype, low_memory=False,
    )
    n_before = len(df)

    df = _clean_flow_chunk(df, valid_stations)
    flow_cols = ["inFlow", "outFlow", "CinFlow", "HBOinFlow", "NHBinFlow",
                 "CoutFlow", "HBOoutFlow", "NHBoutFlow"]
    df = df[df["station"].isin(valid_stations)]
    df = df[(df[flow_cols] >= 0).all(axis=1)]
    df = df.rename(columns={"station": "stationID"})
    df = df.drop_duplicates(subset=["date", "timeslot", "stationID"])

    cols = ["datetime", "date", "timeslot", "startTime", "endTime", "stationID"] + flow_cols
    out = os.path.join(OUT_PATH, "std_10min_inout.csv")
    df[cols].to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  进出站记录: {n_before} -> {len(df)}（剔除 {n_before - len(df)} 条）")
    return df


def clean_od_flow(valid_stations: set):
    print("\n[5/5] 清洗 metroData_ODFlow.csv（12GB，分块处理）...")
    dtype = dict(FLOW_DTYPES)
    dtype.update({
        "originStation": np.int32, "destinationStation": np.int32,
        "Flow": np.int32, "CFlow": np.int32, "HBOFlow": np.int32, "NHBFlow": np.int32,
    })

    out_file = os.path.join(OUT_PATH, "std_10min_od.csv")
    flow_cols = ["Flow", "CFlow", "HBOFlow", "NHBFlow"]
    out_cols = ["datetime", "date", "timeslot", "startTime", "endTime",
                "originStation", "destinationStation"] + flow_cols

    reader = pd.read_csv(
        os.path.join(RAW_PATH, "metroData_ODFlow.csv"),
        skipinitialspace=True, dtype=dtype, chunksize=500_000, low_memory=False,
    )

    total, kept, first = 0, 0, True
    for i, chunk in enumerate(reader):
        n = len(chunk)
        total += n
        chunk = _clean_flow_chunk(chunk, valid_stations)
        chunk = chunk[chunk["originStation"].isin(valid_stations)
                      & chunk["destinationStation"].isin(valid_stations)]
        chunk = chunk[chunk["originStation"] != chunk["destinationStation"]]
        chunk = chunk[(chunk[flow_cols] >= 0).all(axis=1)]
        chunk = chunk.drop_duplicates(
            subset=["date", "timeslot", "originStation", "destinationStation"])
        kept += len(chunk)

        chunk[out_cols].to_csv(
            out_file, mode="w" if first else "a",
            header=first, index=False, encoding="utf-8-sig")
        first = False

        if (i + 1) % 50 == 0:
            print(f"  已处理 {i + 1} 块 / 累计 {total:,} 行 ...")

    print(f"  OD 记录: {total:,} -> {kept:,}（剔除 {total - kept:,} 条）")


def main():
    print("=" * 60)
    print("上海地铁刷卡数据清洗")
    print("=" * 60)

    df_station = clean_station_info()
    valid_stations = set(df_station["stationID"].tolist())

    clean_workday_calendar()
    clean_weather()
    clean_inout_flow(valid_stations)
    clean_od_flow(valid_stations)

    print("\n" + "=" * 60)
    print(f"全部完成，清洗结果已输出到：{OUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
