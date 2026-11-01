"""내려받은 원자료에서 여의도역과 여의나루역, 날씨만 골라 data/clean 에 저장한다.

입력(data/raw 아래, 받는 방법은 README)
  subway_daily/*.csv   서울 열린데이터광장 OA-12914, 월별 파일
  subway_hourly/*.csv  서울 열린데이터광장 OA-12921, 연도별 파일
  weather/*.csv        Open-Meteo Historical API, 서울 종로 격자 시간별
기간: 2024-01-01 ~ 2026-09-30
"""
import glob
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)
START, END = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")
STATIONS = ["여의도", "여의나루"]


def read_kr_csv(path, **kw):
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=enc, **kw)
        except UnicodeDecodeError:
            continue
    raise ValueError(path)


def in_range(df, col):
    return df[(df[col] >= START) & (df[col] <= END)].copy()


# 1. 일별 승하차(5, 9호선 여의도와 5호선 여의나루)
frames = [read_kr_csv(f, index_col=False, dtype=str) for f in sorted(glob.glob(str(RAW / "subway_daily" / "*.csv")))]
d = pd.concat(frames, ignore_index=True).iloc[:, :5]
d.columns = ["date", "line", "station", "board", "alight"]
d = d[d.station.isin(STATIONS)]
d["date"] = pd.to_datetime(d["date"], format="%Y%m%d")
for c in ("board", "alight"):
    d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)
d = in_range(d, "date")
d.to_csv(CLEAN / "subway_daily.csv", index=False, encoding="utf-8-sig")
print("subway_daily:", len(d), "rows")

# 2. 시간대별 승하차(서울교통공사 5호선 여의도), 분기와 평일/주말별 하루 평균
frames = []
for f in sorted(glob.glob(str(RAW / "subway_hourly" / "*.csv"))):
    h = read_kr_csv(f, dtype=str)
    hours = list(h.columns[6:26])
    h = h.iloc[:, [1, 2, 3, 4, 5] + list(range(6, 26))]
    h.columns = ["date", "line", "station_no", "station", "direction"] + hours
    h = h[h.station == "여의도"]
    frames.append(h.melt(id_vars=["date", "line", "station_no", "station", "direction"],
                         var_name="hour_band", value_name="count"))
h = pd.concat(frames, ignore_index=True)
h["date"] = pd.to_datetime(h["date"])
h["count"] = pd.to_numeric(h["count"].str.replace(",", ""), errors="coerce").fillna(0)
h["hour"] = h["hour_band"].map(lambda s: 5 if "이전" in s else 24 if "이후" in s else int(re.match(r"(\d+)", s).group(1)))
h["day_type"] = h["date"].dt.dayofweek.map(lambda x: "주말" if x >= 5 else "평일")
h = in_range(h, "date")
h["quarter"] = h["date"].dt.year.astype(str) + "-Q" + h["date"].dt.quarter.astype(str)
days = h.groupby(["quarter", "day_type"])["date"].nunique().rename("n_days")
agg = (h.groupby(["quarter", "day_type", "line", "station", "direction", "hour"], as_index=False)["count"].sum()
        .join(days, on=["quarter", "day_type"]))
agg["avg_per_day"] = (agg["count"] / agg["n_days"]).round(1)
agg.to_csv(CLEAN / "subway_hourly.csv", index=False, encoding="utf-8-sig")
print("subway_hourly:", len(agg), "rows")

# 3. 날씨(시간별)
wf = sorted(glob.glob(str(RAW / "weather" / "*.csv")))[0]
w = pd.read_csv(wf, skiprows=3)
w = w.iloc[:, :4]
w.columns = ["time", "temp_c", "feels_like_c", "precip_mm"]
w["time"] = pd.to_datetime(w["time"])
w = in_range(w, "time")
w.to_csv(CLEAN / "weather_hourly.csv", index=False, encoding="utf-8-sig")
print("weather_hourly:", len(w), "rows")
