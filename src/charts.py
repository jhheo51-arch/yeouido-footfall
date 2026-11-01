"""analyze.py 집계로 요약 그림 한 장(assets/summary.png)을 만든다."""
from pathlib import Path

import matplotlib
import matplotlib.ticker
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")
plt.rcParams.update({"font.family": "Malgun Gothic", "axes.unicode_minus": False,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#9a9c9f", "axes.titleweight": "bold", "axes.titlesize": 13})

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "out"
GREEN, ORANGE, INK, GREY = "#1e9d8b", "#ca7700", "#1e1e1e", "#c9cacc"
read = lambda name: pd.read_csv(OUT / name, encoding="utf-8-sig", index_col=0)

fig, ax = plt.subplots(2, 2, figsize=(12, 8.4), dpi=150)
fig.suptitle("여의도역과 여의나루역 승하차로 본 방문 시점 (2024-01 ~ 2026-09)", fontsize=15, fontweight="bold", color=INK)

# 1) 평일 시간대별 승차(5호선 여의도)
up = read("hourly_board.csv").loc[7:22, "평일"]
colors = [GREEN if 17 <= h <= 19 else GREY for h in up.index]
a = ax[0, 0]
a.bar(up.index, up.values, color=colors)
a.set_title("평일 시간대별 승차, 5호선 여의도")
a.set_xlabel("시")
a.set_ylabel("하루 평균 승차(명)")
a.text(18, up.loc[18] * 1.04, f"17~19시 {up.loc[17:19].sum():,.0f}명", ha="center", color=GREEN, fontweight="bold")
a.set_ylim(0, up.max() * 1.18)

# 2) 토요일과 일요일 하차 중앙값
ss = read("sat_sun_median.csv")
a = ax[0, 1]
x = range(2)
a.bar([i - 0.2 for i in x], ss["여의도"], width=0.4, color=GREEN, label="여의도")
a.bar([i + 0.2 for i in x], ss["여의나루"], width=0.4, color=ORANGE, label="여의나루")
a.set_xticks(list(x), ["토요일", "일요일"])
for i, (yd, yn) in enumerate(zip(ss["여의도"], ss["여의나루"])):
    a.text(i - 0.2, yd + 400, f"{yd:,.0f}", ha="center", fontsize=10)
    a.text(i + 0.2, yn + 400, f"{yn:,.0f}", ha="center", fontsize=10)
a.set_title("토요일과 일요일 하차 중앙값")
a.set_ylabel("하루 하차(명)")
a.legend(frameon=False)

# 3) 월별 휴일 하차 중앙값
m = read("monthly_holiday_median.csv")
a = ax[1, 0]
a.plot(m.index, m["여의도"], color=GREEN, marker="o", label="여의도")
a.plot(m.index, m["여의나루"], color=ORANGE, marker="o", label="여의나루")
a.set_xticks(range(1, 13), [f"{i}월" for i in range(1, 13)])
a.set_title("월별 휴일 하차 중앙값")
a.set_ylabel("하루 하차(명)")
a.text(4.3, m.loc[4, "여의나루"], f"여의나루 4월은 1월의 {m.loc[4, '여의나루'] / m.loc[1, '여의나루']:.1f}배",
       color=ORANGE, va="center", fontweight="bold")
a.legend(frameon=False, loc="upper left")

# 4) 비 온 휴일
r = read("rain_index.csv")
a = ax[1, 1]
labels = ["여의도", "여의나루"]
vals = [r.loc[True, "여의도_idx"], r.loc[True, "여의나루_idx"]]
a.bar(labels, vals, color=[GREEN, ORANGE], width=0.5)
a.axhline(1, color=INK, lw=0.8, ls="--")
a.text(1.32, 1.01, "같은 달 휴일 중앙값 = 1", fontsize=9, color=INK, ha="right", va="bottom")
for i, v in enumerate(vals):
    a.text(i, v + 0.02, f"{v:.2f}배", ha="center", fontweight="bold")
a.set_ylim(0, 1.25)
a.set_title("낮 강수 3mm 이상인 휴일(42일)의 하차")

for a in (ax[0, 0], ax[0, 1], ax[1, 0]):
    a.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))

fig.text(0.01, 0.005, "자료: 서울 열린데이터광장 OA-12914, OA-12921(시간대별, 2024~2025), Open-Meteo. 휴일 = 토, 일, 공휴일. "
         "중앙값은 집회와 불꽃축제 같은 이상치를 줄이려고 씀.", fontsize=8.5, color="#5e6062")
fig.tight_layout(rect=(0, 0.02, 1, 0.96))
(ROOT / "assets").mkdir(exist_ok=True)
fig.savefig(ROOT / "assets" / "summary.png")
print("assets/summary.png")
