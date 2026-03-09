HOT_FUND_RANK = {
    "161725": 100,
    "110022": 98,
    "005827": 95,
    "001632": 90,
    "003096": 88,
    "006113": 85,
}


def hot_rank(code: str) -> int:
    return HOT_FUND_RANK.get(code, 0)


def sort_codes_by_hotness(codes: list[str]) -> list[str]:
    return sorted(codes, key=lambda x: (-hot_rank(x), x))
