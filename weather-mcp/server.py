import json
import os
from datetime import date
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_FILE = Path(os.environ.get("WEATHER_DATA_FILE", Path(__file__).parent / "weather_data.json"))

mcp = FastMCP("weather")


def _load() -> dict:
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def _find_city(city: str) -> dict:
    cities = _load()["cities"]
    q = city.strip().lower()
    for key, info in cities.items():
        if q == key or q.removesuffix("市") == info["name"]:
            return info
    available = ", ".join(f"{k}({v['name']})" for k, v in cities.items())
    raise ValueError(f"找不到城市 '{city}'，可用城市：{available}")


def _parse_date(s: str, field: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise ValueError(f"{field} 格式錯誤：'{s}'，請使用 YYYY-MM-DD")


@mcp.tool()
def get_current_weather(city: str) -> dict:
    """查詢城市目前天氣。city 可用中文（台北）或英文（taipei）。"""
    info = _find_city(city)
    return {"city": info["name"], **info["current"]}


@mcp.tool()
def get_weather_forecast(city: str, days: int = 3) -> dict:
    """查詢城市未來 N 天（1-7）的天氣預報，從目前觀測日的隔天起算。"""
    if not 1 <= days <= 7:
        raise ValueError("days 必須介於 1 到 7")
    info = _find_city(city)
    today = info["current"]["date"]
    future = [d for d in info["daily"] if d["date"] > today][:days]
    return {"city": info["name"], "from": today, "forecast": future}


@mcp.tool()
def get_weather_by_range(city: str, start_date: str, end_date: str) -> dict:
    """查詢城市在指定日期區間（含頭尾，格式 YYYY-MM-DD）的每日天氣。"""
    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")
    if start > end:
        raise ValueError("start_date 不可晚於 end_date")
    info = _find_city(city)
    records = [d for d in info["daily"] if start <= date.fromisoformat(d["date"]) <= end]
    if not records:
        first, last = info["daily"][0]["date"], info["daily"][-1]["date"]
        raise ValueError(f"區間內沒有資料，可查詢範圍：{first} ~ {last}")
    return {"city": info["name"], "start_date": start_date, "end_date": end_date, "days": records}


if __name__ == "__main__":
    mcp.run()
