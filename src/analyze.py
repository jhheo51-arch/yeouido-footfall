"""여의도역(5, 9호선)과 여의나루역(5호선) 하차를 휴일, 요일, 달, 날씨, 시간대로 나눠 본다.

입력: data/clean (prepare.py 결과)
출력: data/out/*.csv(그림용 집계), results/summary.txt(콘솔과 같은 내용)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "data" / "out"
OUT.mkdir(parents=True, exist_ok=True)
(ROOT / "results").mkdir(exist_ok=True)


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)

    def flush(self):
        for st in self.streams:
            st.flush()


log = open(ROOT / "results" / "summary.txt", "w", encoding="utf-8")
sys.stdout = Tee(sys.__stdout__, log)
pd.set_option("display.width", 120)

# 평일에 걸린 공휴일(대체공휴일, 선거일, 임시공휴일 포함).
# 2026년 노동절(5/1)과 제헌절(7/17)은 인사혁신처 2026-04-29 보도자료로 공휴일 지정.
# 2026년 추석(9/24~26)은 일요일과 겹치지 않아 대체공휴일 없음(9/28은 평일).
HOLIDAYS = """
2024-01-01 2024-02-09 2024-02-12 2024-03-01 2024-04-10 2024-05-06 2024-05-15 2024-06-06
2024-08-15 2024-09-16 2024-09-17 2024-09-18 2024-10-01 2024-10-03 2024-10-09 2024-12-25
2025-01-01 2025-01-27 2025-01-28 2025-01-29 2025-01-30 2025-03-03 2025-05-05 2025-05-06
2025-06-03 2025-06-06 2025-08-15 2025-10-03 2025-10-06 2025-10-07 2025-10-08 2025-10-09
2025-12-25
2026-01-01 2026-02-16 2026-02-17 2026-02-18 2026-03-02 2026-05-01 2026-05-05 2026-05-25
2026-06-03 2026-07-17 2026-08-17 2026-09-24 2026-09-25
""".split()

sub = pd.read_csv(CLEAN / "subway_daily.csv", encoding="utf-8-sig", parse_dates=["date"])
daily = sub.groupby(["date", "station"]).alight.sum().unstack()
daily["holiday"] = (daily.index.weekday >= 5) | daily.index.strftime("%Y-%m-%d").isin(HOLIDAYS)

w = pd.read_csv(CLEAN / "weather_hourly.csv", encoding="utf-8-sig", parse_dates=["time"])
w["date"] = w.time.dt.normalize()
day_w = w[w.time.dt.hour.between(10, 20)].groupby("date").agg(
    rain_day=("precip_mm", "sum"), temp=("temp_c", "mean"), feels=("feels_like_c", "mean"))
daily = daily.join(day_w)
daily["wet"] = daily.rain_day >= 3  # 낮(10~20시) 강수 3mm 이상
daily["month"] = daily.index.to_period("M")

hol = daily[daily.holiday].copy()
for s in ["여의도", "여의나루"]:
    hol[f"{s}_idx"] = hol[s] / hol.groupby("month")[s].transform("median")

# 1) 평일 대비 휴일 수준
lvl = daily.groupby("holiday")[["여의도", "여의나루"]].mean().round(0)
print("== 하루 평균 하차 (평일 False / 휴일 True)\n", lvl)

# 2) 비 온 휴일과 맑은 휴일 (같은 달 휴일 중앙값 대비)
rain = hol.groupby("wet")[["여의도_idx", "여의나루_idx"]].agg(["median", "count"]).round(3)
print("\n== 같은 달 휴일 중앙값 대비 (낮 강수 3mm 이상 True)\n", rain)

# 3) 체감온도 구간별
hol["feels_band"] = pd.cut(hol.feels, [-30, 0, 10, 20, 27, 45],
                           labels=["0도 미만", "0~10도", "10~20도", "20~27도", "27도 이상"])
dry = hol[~hol.wet]
band = dry.groupby("feels_band", observed=True)[["여의도_idx", "여의나루_idx"]].agg(["median", "count"]).round(3)
print("\n== 비 안 온 휴일, 낮 체감온도 구간별\n", band)

# 4) 월별 휴일 하차 중앙값
monthly = hol.groupby(hol.index.month)[["여의도", "여의나루"]].median().round(0)
print("\n== 월별 휴일 하차 중앙값 (집회, 불꽃축제 이상치 때문에 평균 대신 중앙값)\n", monthly)

# 4-1) 토요일(5)과 일요일(6) 휴일 하차 중앙값, 연도별과 전체
wk = hol[hol.index.weekday >= 5]
sat_sun = wk.groupby(wk.index.weekday)[["여의도", "여의나루"]].median().round(0)
print("\n== 토(5) 일(6) 휴일 하차 중앙값\n",
      wk.groupby([wk.index.year, wk.index.weekday])[["여의도", "여의나루"]].median().round(0),
      "\n", sat_sun)

# 4-2) 연도별 평일과 휴일 하차 중앙값, 2026년 자료가 9월까지라 1~9월끼리 비교
ytd = daily[daily.index.month <= 9]
print("\n== 1~9월 연도별 하차 중앙값 (평일 False / 휴일 True)\n",
      ytd.groupby([ytd.index.year, "holiday"])[["여의도", "여의나루"]].median().round(0))

# 5) 상위 휴일
top = hol.sort_values("여의도", ascending=False).head(12)[["여의도", "여의나루", "rain_day", "feels"]]
print("\n== 여의도 하차 상위 휴일\n", top.round(1))

# 6) 5호선 여의도 시간대별 하차와 승차 (평일과 주말, 2024~2025 분기 평균)
h = pd.read_csv(CLEAN / "subway_hourly.csv", encoding="utf-8-sig")
prof = (h[h.direction == "하차"].groupby(["day_type", "hour"]).avg_per_day.mean().unstack(0).round(0))
print("\n== 5호선 여의도 시간대별 하차 하루 평균\n", prof.loc[7:22])
up = (h[h.direction == "승차"].groupby(["day_type", "hour"]).avg_per_day.mean().unstack(0).round(0))
print("\n== 5호선 여의도 시간대별 승차 하루 평균 (16~21시)\n", up.loc[16:21],
      "\n평일 17~19시 합계:", up.loc[17:19, "평일"].sum())

# 7) 일요일 행사 효과를 구분하려면 일요일이 몇 번 필요한가 (유의수준 5%, 검정력 80%)
sun = hol[hol.index.weekday == 6].copy()
for s in ["여의도", "여의나루"]:
    sun[f"{s}_log"] = np.log(sun[s] / sun.groupby("month")[s].transform("median"))
sd_own = sun["여의도_log"].std()
sd_ref = np.log(sun["여의도"] / sun["여의나루"]).pipe(lambda x: x - x.groupby(sun.month).transform("median")).std()
for name, sd in [("같은 달 일요일 기준", sd_own), ("여의나루 대비 비율 기준", sd_ref)]:
    need = {f"{int(e*100)}%": int(np.ceil(((1.96 + 0.84) * sd / np.log(1 + e)) ** 2)) for e in (0.05, 0.10)}
    print(f"\n== {name}: 표준편차 {sd:.3f}, 일요일 {len(sun)}개, 필요한 일요일 수 {need}")

# 그림용 집계
monthly.to_csv(OUT / "monthly_holiday_median.csv", encoding="utf-8-sig")
sat_sun.to_csv(OUT / "sat_sun_median.csv", encoding="utf-8-sig")
hol.groupby("wet")[["여의도_idx", "여의나루_idx"]].median().to_csv(OUT / "rain_index.csv", encoding="utf-8-sig")
up.to_csv(OUT / "hourly_board.csv", encoding="utf-8-sig")
daily.to_csv(OUT / "daily.csv", encoding="utf-8-sig")
sys.stdout = sys.__stdout__
log.close()
