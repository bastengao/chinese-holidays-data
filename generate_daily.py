#!/usr/bin/env python3
"""
根据 data/<year>.json 的放假数据，为每年每一天生成 data/<year>/mm-dd.json 文件。

type 枚举:
  - holiday  : 法定节假日（含调休多出的假期）
  - workday  : 调休补班日 / 普通工作日 / 普通周末

name:
  - 法定节假日或调休补班日 → 对应节日名称
  - 普通工作日 / 普通周末  → null
"""

import json
import os
from datetime import date, timedelta
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"


def date_range(start_str: str, end_str: str | None = None):
    """生成从 start 到 end（含）的所有日期。"""
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str) if end_str else start
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def load_special_days(year: int) -> dict[date, dict]:
    """
    读取 data/<year>.json，返回 {date: {"type": ..., "name": ...}} 的映射。
    源数据 type:
      - "holiday"    → 法定节假日
      - "workingday" → 调休补班（正常本是休息日，需要上班）
    """
    json_path = DATA_DIR / f"{year}.json"
    if not json_path.exists():
        return {}

    with json_path.open(encoding="utf-8") as f:
        entries = json.load(f)

    special: dict[date, dict] = {}
    for entry in entries:
        name = entry["name"]
        src_type = entry["type"]          # "holiday" | "workingday"
        r = entry["range"]
        start_str = r[0]
        end_str = r[1] if len(r) == 2 else None

        for d in date_range(start_str, end_str):
            if src_type == "holiday":
                special[d] = {"type": "holiday", "name": name}
            else:
                # workingday：调休补班，输出 type=workday，但保留名称
                special[d] = {"type": "workday", "name": name}

    return special


def day_type(d: date, special: dict[date, dict]) -> dict:
    """
    返回某天的完整信息。
    优先级：特殊日历表 > 周末/工作日默认推断
    """
    if d in special:
        return {
            "date": d.isoformat(),
            "type": special[d]["type"],
            "name": special[d]["name"],
        }

    # 默认：周一~五 → workday，周六~日 → holiday（普通周末也算休息）
    # 但 name 均为 null（非节假日、非调休）
    is_weekend = d.weekday() >= 5  # 5=Saturday, 6=Sunday
    return {
        "date": d.isoformat(),
        "type": "holiday" if is_weekend else "workday",
        "name": None,
    }


def generate_year(year: int):
    special = load_special_days(year)
    if not special and not (DATA_DIR / f"{year}.json").exists():
        print(f"[skip] data/{year}.json 不存在，跳过 {year}")
        return

    year_dir = DATA_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)

    start = date(year, 1, 1)
    end = date(year, 12, 31)
    current = start
    count = 0
    while current <= end:
        info = day_type(current, special)
        filename = year_dir / current.strftime("%m-%d.json")
        with filename.open("w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, separators=(",", ":"))
        current += timedelta(days=1)
        count += 1

    print(f"[done] {year}: 生成 {count} 个文件 → {year_dir}/")


def main():
    # 收集所有有源数据的年份
    years = sorted(
        int(p.stem)
        for p in DATA_DIR.glob("*.json")
        if p.stem.isdigit()
    )

    if not years:
        print("未找到任何年份数据文件（data/<year>.json）")
        return

    print(f"发现年份: {years}")
    for year in years:
        generate_year(year)


if __name__ == "__main__":
    main()
