"""대시보드(docs/index.html)가 읽는 집계 파일 docs/data.js 를 만든다.

역별 일별 하차 합계와 5호선 여의도 시간대별 하루 평균만 담는다. 원자료 행은 넣지 않는다.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "out"
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

d = pd.read_csv(OUT / "daily.csv", encoding="utf-8-sig", parse_dates=["date"])
daily = [[r.date.strftime("%Y-%m-%d"), int(r.여의도), int(r.여의나루), int(r.holiday),
          round(float(r.rain_day), 1), round(float(r.feels), 1)] for r in d.itertuples()]

h = pd.read_csv(ROOT / "data" / "clean" / "subway_hourly.csv", encoding="utf-8-sig")
h = h[h.hour.between(5, 24)]
hourly = {}
for (direction, day_type), g in h.groupby(["direction", "day_type"]):
    s = g.groupby("hour").avg_per_day.mean().round(0)
    hourly[f"{direction}_{day_type}"] = [int(v) for v in s.reindex(range(5, 25), fill_value=0)]

data = {"columns": ["date", "yeouido", "yeouinaru", "holiday", "rain_10_20", "feels_10_20"],
        "daily": daily, "hourly": hourly, "hours": list(range(5, 25)),
        "outliers": {"2024-12-07": "국회 앞 집회", "2024-12-14": "국회 앞 집회",
                     "2024-10-05": "서울세계불꽃축제", "2025-09-27": "서울세계불꽃축제",
                     "2026-09-05": "서울세계불꽃축제"}}
(DOCS / "data.js").write_text("window.FOOTFALL = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                              encoding="utf-8")
print("docs/data.js", len(daily), "days")
