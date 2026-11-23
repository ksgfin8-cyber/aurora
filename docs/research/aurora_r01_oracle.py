"""Local formula oracle for AURORA-R01. Does not invoke Pine."""

import csv
import itertools
import math
from pathlib import Path
import statistics
import sys

FLOOR = 1e-10
CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/aurora-r01.csv")


def views(z_slope, z_chop, z_delta):
    trend = z_slope is not None and z_slope > 1 and z_chop < -1
    ranging = z_chop > 1
    volatile = z_delta is not None and z_delta > 1
    histogram = 1 if trend else 2 if volatile else 0
    panel = "TREND" if trend else "RANGE" if ranging else "VOLATILE" if volatile else "NEUTRAL"
    background = {"TREND": "green", "RANGE": "gray", "VOLATILE": "red", "NEUTRAL": "none"}[panel]
    return (trend, ranging, volatile), histogram, panel, background


def window(series, length):
    values = series[-length:]
    return values if len(values) == length and None not in values else None


def zscore(series, length):
    values = window(series, length)
    if values is None:
        return None
    return (values[-1] - statistics.mean(values)) / max(statistics.pstdev(values), FLOOR)


def ema(value, previous, length):
    weight = 2 / (length + 1)
    return value if previous is None else weight * value + (1 - weight) * previous


def market_bars(log_return, spread=0):
    close = 100.0
    yield close, close, close, close
    for index in range(1, 100):
        opening = close
        close *= math.exp(log_return(index))
        yield opening, max(opening, close) * (1 + spread), min(opening, close) * (1 - spread), close


def trace(bars, lengths=(50, 30, 20)):
    phi_length, sigma_length, slope_length = lengths
    if min(lengths) < 1:
        raise ValueError("Oracle requires positive lengths")
    returns, ranges, highs, lows, deltas, chops, slopes = ([] for _ in range(7))
    close_previous = return_ema = price_ema = vol_previous = None
    for index, (_, high, low, close) in enumerate(bars):
        ret = None if close_previous is None else math.log(close / close_previous)
        returns.append(ret)
        highs.append(high)
        lows.append(low)
        true_range = None if close_previous is None else max(
            high - low, abs(high - close_previous), abs(low - close_previous)
        )
        ranges.append(true_range)
        if ret is not None:
            return_ema = ema(ret, return_ema, phi_length)
        phi_window = window(returns, phi_length)
        phi = None
        if phi_window is not None:
            base = statistics.mean(abs(value) for value in phi_window)
            phi = min(1, max(0, 1 - abs(ret - return_ema) / max(base, FLOOR)))
        vol_window = window(returns, sigma_length)
        vol = statistics.pstdev(vol_window) if vol_window else None
        delta = abs(vol - vol_previous) if vol is not None and vol_previous is not None else None
        deltas.append(delta)
        z_delta = zscore(deltas, sigma_length)
        tr_window = window(ranges, sigma_length)
        price_range = max(highs[-sigma_length:]) - min(lows[-sigma_length:])
        tr_sum = sum(tr_window) if tr_window is not None else None
        chop_raw = None
        if tr_sum is not None and tr_sum > 0 and sigma_length > 1:
            chop_raw = 100 * math.log10(tr_sum / max(price_range, FLOOR)) / math.log10(sigma_length)
        chop = 50.0 if chop_raw is None else chop_raw
        chops.append(chop)
        z_chop = zscore(chops, sigma_length)
        psi = None if z_delta is None else 1 / (1 + math.exp(-0.5 * (z_delta + z_chop)))
        complement = None if psi is None else 1 - psi
        omega = None if phi is None or complement is None else phi * complement
        next_ema = ema(close, price_ema, slope_length)
        slope = None if price_ema is None else next_ema - price_ema
        slopes.append(slope)
        z_slope = zscore(slopes, sigma_length)
        bits, histogram, panel, background = views(
            z_slope, z_chop if z_chop is not None else 0, z_delta
        )
        yield dict(bar=index, close=close, ret=ret, ret_ema=return_ema, tr=true_range,
                   sum_tr=tr_sum, price_range=price_range, raw_chop=chop_raw, chop=chop,
                   fallback=chop_raw is None, vol=vol, delta=delta, z_delta=z_delta,
                   z_chop=z_chop, slope=slope, z_slope=z_slope, phi=phi, psi=psi,
                   complement=complement, omega=omega, trend=bits[0], ranging=bits[1],
                   volatile=bits[2], histogram=histogram, panel=panel, background=background)
        close_previous, price_ema, vol_previous = close, next_ema, vol


def close_enough(actual, expected):
    assert math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12), (actual, expected)


def run():
    expected = {
        (0, 0, 0): (0, "NEUTRAL", "none"),
        (0, 0, 1): (2, "VOLATILE", "red"),
        (0, 1, 0): (0, "RANGE", "gray"),
        (0, 1, 1): (2, "RANGE", "gray"),
        (1, 0, 0): (1, "TREND", "green"),
        (1, 0, 1): (1, "TREND", "green"),
    }
    grid = set()
    for values in itertools.product((-2, -1, 0, 1, 2), repeat=3):
        bits, *outputs = views(*values)
        assert tuple(outputs) == expected[bits]
        grid.add(bits)
    assert grid == set(expected)

    fixtures = {
        "flat": list(market_bars(lambda _: 0)),
        "tiny": list(market_bars(lambda i: (-1) ** i * 1e-12)),
        "up": list(market_bars(lambda _: 0.002)),
        "down": list(market_bars(lambda _: -0.002)),
        "osc": list(market_bars(lambda i: (-1) ** i * 0.01, 0.001)),
        "jump": list(market_bars(lambda i: (-1) ** i * (0.001 if i < 70 else 0.03), 0.001)),
    }
    runs = {name: list(trace(bars)) for name, bars in fixtures.items()}
    runs["range_vol"] = list(trace(market_bars(lambda i: 0.001 if i < 70 else (-1) ** i * 0.001)))
    runs["sigma1"] = list(trace(fixtures["osc"], (50, 1, 20)))
    runs["short"] = list(trace(fixtures["jump"][:29]))
    for lengths in ((0, 30, 20), (50, -1, 20), (50, 30, 0)):
        try:
            list(trace(fixtures["up"][:1], lengths))
        except ValueError:
            print("rejected by oracle", lengths)
        else:
            raise AssertionError(lengths)

    def first(rows, key):
        return next((row["bar"] for row in rows if row[key] is not None), None)

    keys = ("ret", "tr", "sum_tr", "vol", "delta", "raw_chop", "z_chop",
            "z_slope", "z_delta", "phi", "psi", "omega")
    with CSV_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, ["case", *runs["flat"][0]])
        writer.writeheader()
        for name, rows in runs.items():
            writer.writerows(dict(case=name, **row) for row in rows)
            print(name, "first", [first(rows, key) for key in keys],
                  "fallback", sum(row["fallback"] for row in rows))
            states = {}
            for row in rows:
                bits = tuple(int(row[key]) for key in ("trend", "ranging", "volatile"))
                states.setdefault(bits, row["bar"])
                if row["omega"] is not None:
                    assert 0 <= row["omega"] <= min(row["phi"], row["complement"]) <= 1
            print("  states", states)
            for index in (60, 69, 70, 99):
                if index < len(rows):
                    row = rows[index]
                    print(" ", index, *(None if row[key] is None else round(row[key], 9)
                                        for key in ("phi", "psi", "complement", "omega")))

    for name, bar, expected_bits in (
        ("osc", 30, (0, 1, 0)),
        ("range_vol", 71, (0, 1, 1)),
        ("jump", 70, (1, 0, 1)),
    ):
        row = runs[name][bar]
        assert tuple(row[key] for key in ("trend", "ranging", "volatile")) == expected_bits
        print("OHLC witness", name, bar, *(round(row[key], 6)
                                          for key in ("z_slope", "z_chop", "z_delta")
                                          if row[key] is not None))

    def order(left, right):
        if abs(left - right) <= 1e-7:
            return 0
        return 1 if left > right else -1

    comparisons = {}
    for left, right in itertools.combinations(fixtures, 2):
        for a, b in zip(runs[left], runs[right]):
            if a["omega"] is not None and b["omega"] is not None:
                orders = tuple(order(a[key], b[key]) for key in ("phi", "complement", "omega"))
                comparisons[orders] = comparisons.get(orders, 0) + 1
    print("Rank comparisons (phi, complement, omega)", sorted(comparisons.items()))
    assert sum(comparisons.values()) == 600
    for key, value in {"phi": 1, "psi": 0.5, "omega": 0.5}.items():
        for row in runs["flat"][60:]:
            close_enough(row[key], value)
    assert all(row["fallback"] for row in runs["flat"] + runs["sigma1"])
    assert all(row["omega"] is None for row in runs["short"])
    assert [first(runs["flat"], key) for key in ("phi", "psi", "omega")] == [50, 60, 60]
    assert [first(runs["sigma1"], key) for key in ("phi", "psi", "omega")] == [50, 2, 50]
    for a, b, expected_products in (
        ((0.8, 0.25), (0.8, 0.75), (0.60, 0.20)),
        ((0.9, 0.8), (0.5, 0.2), (0.18, 0.40)),
        ((0.9, 0.5), (0.5, 0.2), (0.45, 0.40)),
    ):
        for (phi, psi), product in zip((a, b), expected_products):
            close_enough(phi * (1 - psi), product)
    print("Assertions passed. Trace:", CSV_PATH)


if __name__ == "__main__":
    run()
