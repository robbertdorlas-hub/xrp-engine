import requests
import pandas as pd
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
from datetime import datetime
import os

SYMBOL = "XRPUSDT"
LOG_FILE = "xrp_prediction_log.csv"


def get_data(interval):
    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "limit": 150
    }

    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df


def detect_zones(df):
    recent = df.tail(80)

    support = recent["low"].min()
    resistance = recent["high"].max()

    zone_size = recent["close"].mean() * 0.003

    return {
        "support_low": support,
        "support_high": support + zone_size,
        "resistance_low": resistance - zone_size,
        "resistance_high": resistance
    }


def detect_candle(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(last["close"] - last["open"])
    candle_range = last["high"] - last["low"]

    if candle_range == 0:
        return "Geen patroon", 0

    upper_wick = last["high"] - max(last["open"], last["close"])
    lower_wick = min(last["open"], last["close"]) - last["low"]

    if body <= candle_range * 0.1:
        return "Doji", 0

    if lower_wick > body * 2 and upper_wick < body:
        return "Hammer", 1

    if upper_wick > body * 2 and lower_wick < body:
        return "Shooting Star", -1

    if (
        prev["close"] < prev["open"]
        and last["close"] > last["open"]
        and last["close"] > prev["open"]
    ):
        return "Bullish Engulfing", 2

    if (
        prev["close"] > prev["open"]
        and last["close"] < last["open"]
        and last["close"] < prev["open"]
    ):
        return "Bearish Engulfing", -2

    return "Geen duidelijk patroon", 0


def analyze_timeframe(df, name):
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()

    df["ema20"] = EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["ema50"] = EMAIndicator(
        close=df["close"],
        window=50
    ).ema_indicator()

    macd = MACD(close=df["close"])

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    bb = BollingerBands(
        close=df["close"],
        window=20
    )

    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()

    latest = df.iloc[-1]

    price = latest["close"]

    zones = detect_zones(df)

    if (
        price > latest["ema20"]
        and latest["ema20"] > latest["ema50"]
    ):
        trend = "Bullish"
        trend_score = 1

    elif (
        price < latest["ema20"]
        and latest["ema20"] < latest["ema50"]
    ):
        trend = "Bearish"
        trend_score = -1

    else:
        trend = "Neutraal"
        trend_score = 0

    if latest["macd"] > latest["macd_signal"]:
        macd_status = "Bullish"
        macd_score = 1

    else:
        macd_status = "Bearish"
        macd_score = -1

    candle, candle_score = detect_candle(df)

    zone_status = "Geen belangrijke zone"
    zone_score = 0

    if (
        zones["support_low"]
        <= price
        <= zones["support_high"]
    ):
        zone_status = "Prijs zit in support zone"
        zone_score = 1

    if (
        zones["resistance_low"]
        <= price
        <= zones["resistance_high"]
    ):
        zone_status = "Prijs zit in resistance zone"
        zone_score = -1

    volume_strength = (
        latest["volume"]
        / df["volume"].tail(20).mean()
    )

    volatility = (
        latest["bb_high"]
        - latest["bb_low"]
    )

    tf_score = (
        trend_score
        + macd_score
        + candle_score
        + zone_score
    )

    print(f"\n===== {name} =====")
    print(f"Prijs: ${price:.4f}")
    print(f"RSI: {latest['rsi']:.2f}")
    print(f"Trend: {trend}")
    print(f"MACD: {macd_status}")
    print(f"Candlestick: {candle}")
    print(f"Zone status: {zone_status}")
    print(f"Volume strength: {volume_strength:.2f}")
    print(f"Timeframe score: {tf_score}")

    return {
        "price": price,
        "rsi": latest["rsi"],
        "trend": trend,
        "macd": macd_status,
        "candle": candle,
        "zone_status": zone_status,
        "volume_strength": volume_strength,
        "volatility": volatility,
        "score": tf_score,
        "zones": zones,
        "df": df
    }


def breakout_engine(r15, r1h, r4h):
    score = 0

    for r in [r15, r1h, r4h]:

        if r["trend"] == "Bullish":
            score += 1

    if r15["macd"] == "Bullish":
        score += 1

    if r1h["macd"] == "Bullish":
        score += 1

    if r15["volume_strength"] > 1.2:
        score += 1

    if r1h["volume_strength"] > 1.2:
        score += 1

    if r15["rsi"] > 55:
        score += 1

    if r1h["rsi"] > 55:
        score += 1

    breakout = min(100, score * 10)

    rejection = 100 - breakout

    return breakout, rejection


def fake_breakout_detector(r15, r1h, r4h, breakout):
    fake_score = 0
    reasons = []

    if "resistance" in r15["zone_status"]:
        fake_score += 2
        reasons.append(
            "15m prijs zit in resistance zone"
        )

    if "resistance" in r1h["zone_status"]:
        fake_score += 2
        reasons.append(
            "1h prijs zit in resistance zone"
        )

    if r15["volume_strength"] < 0.8:
        fake_score += 2
        reasons.append("15m volume is zwak")

    if r1h["volume_strength"] < 0.8:
        fake_score += 2
        reasons.append("1h volume is zwak")

    if r4h["trend"] != "Bullish":
        fake_score += 1
        reasons.append(
            "4h trend is niet bullish"
        )

    if breakout < 50:
        fake_score += 2
        reasons.append(
            "Breakout probability is laag"
        )

    risk = min(100, fake_score * 10)

    if risk >= 70:
        warning = "Hoog fake breakout risico"

    elif risk >= 40:
        warning = "Gemiddeld fake breakout risico"

    else:
        warning = "Laag fake breakout risico"

    return risk, warning, reasons


df_15m = get_data("15m")
df_1h = get_data("1h")
df_4h = get_data("4h")

r15 = analyze_timeframe(df_15m, "15 MIN")
r1h = analyze_timeframe(df_1h, "1 UUR")
r4h = analyze_timeframe(df_4h, "4 UUR")

total_score = (
    r15["score"]
    + r1h["score"]
    + r4h["score"]
)

breakout_probability, rejection_probability = breakout_engine(
    r15,
    r1h,
    r4h
)

fake_risk, fake_warning, fake_reasons = fake_breakout_detector(
    r15,
    r1h,
    r4h,
    breakout_probability
)

print("\n===== BREAKOUT ENGINE =====")

print(
    f"Breakout probability: {breakout_probability}%"
)

print(
    f"Rejection probability: {rejection_probability}%"
)

print("\n===== FAKE BREAKOUT DETECTOR =====")

print(f"Fake breakout risk: {fake_risk}%")

print(f"Waarschuwing: {fake_warning}")

for reason in fake_reasons:
    print(f"- {reason}")

print("\n===== TOTALE ANALYSE =====")

print(f"Totale score: {total_score}")

if fake_risk >= 70:
    prediction = "Wachten - hoog fake breakout risico"

elif breakout_probability >= 70:
    prediction = "Hoge breakout kans"

elif breakout_probability >= 55:
    prediction = "Licht bullish"

elif rejection_probability >= 70:
    prediction = "Hoge rejection kans"

else:
    prediction = "Neutraal"

print(f"Voorspelling: {prediction}")

log_data = {
    "datetime": [datetime.now()],
    "prediction": [prediction],
    "score": [total_score],
    "breakout_probability": [breakout_probability],
    "rejection_probability": [rejection_probability],
    "fake_breakout_risk": [fake_risk],
    "price_15m": [r15["price"]],
    "price_1h": [r1h["price"]],
    "price_4h": [r4h["price"]]
}

log_df = pd.DataFrame(log_data)

if os.path.exists(LOG_FILE):

    old = pd.read_csv(LOG_FILE)

    for col in log_df.columns:
        if col not in old.columns:
            old[col] = None

    for col in old.columns:
        if col not in log_df.columns:
            log_df[col] = None

    log_df = log_df[old.columns]

    final_log = pd.concat(
        [old, log_df],
        ignore_index=True
    )

    final_log.to_csv(
        LOG_FILE,
        index=False
    )

else:
    log_df.to_csv(
        LOG_FILE,
        index=False
    )

print("\nAnalyse opgeslagen.")

df_chart = r1h["df"]

zones = r1h["zones"]

plt.figure(figsize=(14, 7))

plt.plot(
    df_chart["time"],
    df_chart["close"],
    label="XRP prijs"
)

plt.plot(
    df_chart["time"],
    df_chart["ema20"],
    label="EMA20"
)

plt.plot(
    df_chart["time"],
    df_chart["ema50"],
    label="EMA50"
)

plt.axhspan(
    zones["support_low"],
    zones["support_high"],
    alpha=0.2,
    label="Support zone"
)

plt.axhspan(
    zones["resistance_low"],
    zones["resistance_high"],
    alpha=0.2,
    label="Resistance zone"
)

plt.title(
    f"XRP | Breakout: {breakout_probability}% | Fake risk: {fake_risk}% | {prediction}"
)

plt.xlabel("Tijd")

plt.ylabel("Prijs")

plt.legend()

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig("xrp_chart.png")

plt.close()

print("Grafiek opgeslagen.")