import pandas as pd
import os

OUTPUT_PATH = r"C:\Users\yzcw_\Desktop\MetroFlow_project\processed_data"

df_inout = pd.read_csv(os.path.join(OUTPUT_PATH, "std_10min_inout.csv"))
df_inout["datetime"] = pd.to_datetime(df_inout["datetime"])

print("====进出站数据校验====")
print("时间范围：", df_inout["datetime"].min(), " ~ ", df_inout["datetime"].max())
print("最小inFlow：", df_inout["inFlow"].min())
print("最小outFlow：", df_inout["outFlow"].min())

df_od_sample = pd.read_csv(os.path.join(OUTPUT_PATH, "std_10min_od.csv"), nrows=2000)
print("\n====OD抽样校验====")
same_station_cnt = (df_od_sample["originStation"] == df_od_sample["destinationStation"]).sum()
print("抽样中起终点相同行数：", same_station_cnt)
print("抽样最小Flow：", df_od_sample["Flow"].min())
