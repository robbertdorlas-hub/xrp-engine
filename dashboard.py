import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Crypto AI Scanner", layout="wide")

st.title("🚀 Crypto AI Scanner")

log_file = "/data/xrp_prediction_log.csv"
chart_file = "/data/xrp_chart.png"

if not os.path.exists(log_file):
    st.warning("Nog geen logbestand gevonden")
    st.stop()

df = pd.read_csv(log_file)

latest = (
    df.sort_values("datetime")
    .groupby("symbol")
    .tail(1)
    .copy()
)

latest["rank_score"] = (
    latest["breakout_probability"]
    - latest["fake_breakout_risk"]
    + latest["score"] * 5
)

latest = latest.sort_values("rank_score", ascending=False)

def signal_badge(row):
    if row["breakout_probability"] >= 55 and row["fake_breakout_risk"] <= 50:
        return "🟢 KANS"
    if row["breakout_probability"] >= 30 and row["fake_breakout_risk"] <= 70:
        return "🟠 WATCHLIST"
    return "🔴 VERMIJDEN"

latest["signaal"] = latest.apply(signal_badge, axis=1)

columns = [
    "datetime",
    "symbol",
    "signaal",
    "prediction",
    "rank_score",
    "breakout_probability",
    "fake_breakout_risk",
    "score",
    "price_15m",
    "price_1h",
    "price_4h",
    "trend_15m",
    "trend_1h",
    "trend_4h",
    "rsi_15m",
    "rsi_1h",
    "rsi_4h",
    "volume_strength_15m",
    "volume_strength_1h",
    "volume_strength_4h",
    "fear_greed_value",
    "fear_greed_label",
    "market_mode",
]

available_columns = [col for col in columns if col in latest.columns]

st.subheader("🌍 Markt Intelligentie")

market_cols = st.columns(3)

fg_value = (
    latest["fear_greed_value"].dropna().iloc[-1]
    if "fear_greed_value" in latest.columns
    and latest["fear_greed_value"].notna().any()
    else "-"
)

fg_label = (
    latest["fear_greed_label"].dropna().iloc[-1]
    if "fear_greed_label" in latest.columns
    and latest["fear_greed_label"].notna().any()
    else "-"
)

market_mode = (
    latest["market_mode"].dropna().iloc[-1]
    if "market_mode" in latest.columns
    and latest["market_mode"].notna().any()
    else "-"
)

translated_label = {
    "Extreme Fear": "Extreme Angst",
    "Fear": "Angst",
    "Neutral": "Neutraal",
    "Greed": "Hebzucht",
    "Extreme Greed": "Extreme Hebzucht"
}

fg_label_nl = translated_label.get(fg_label, fg_label)
market_mode_nl = translated_label.get(market_mode, market_mode)

market_cols[0].metric("Fear & Greed Index", f"{fg_value}")
market_cols[1].metric("Markt Sentiment", f"{fg_label_nl}")
market_cols[2].metric("Marktmodus", f"{market_mode_nl}")

opportunities = latest[
    (latest["breakout_probability"] >= 55)
    & (latest["fake_breakout_risk"] <= 50)
]

watchlist = latest[
    (latest["breakout_probability"] >= 30)
    & (latest["fake_breakout_risk"] <= 70)
    & ~latest.index.isin(opportunities.index)
]

avoid = latest[
    ~latest.index.isin(opportunities.index)
    & ~latest.index.isin(watchlist.index)
]

st.subheader("🏆 Beste setups")

top = latest.head(3)
cols = st.columns(3)
medals = ["🥇", "🥈", "🥉"]

for i, (_, row) in enumerate(top.iterrows()):
    with cols[i]:
        st.markdown(f"### {medals[i]} {row['symbol']}")
        st.markdown(f"**{row['signaal']}**")
        st.metric("Voorspelling", row["prediction"], f"Score {row['rank_score']}")
        st.write(f"Breakout kans: **{row['breakout_probability']}%**")
        st.progress(int(row["breakout_probability"]))
        st.write(f"Fake breakout risk: **{row['fake_breakout_risk']}%**")
        st.progress(int(row["fake_breakout_risk"]))
        st.write(f"Trend 1h: **{row['trend_1h']}**")
        st.write(f"RSI 1h: **{round(row['rsi_1h'], 2)}**")

st.subheader("🟢 Kansen")
if len(opportunities) > 0:
    st.dataframe(opportunities[available_columns], use_container_width=True)
else:
    st.info("Geen sterke bullish kansen gevonden.")

st.subheader("🟠 Watchlist")
if len(watchlist) > 0:
    st.dataframe(watchlist[available_columns], use_container_width=True)
else:
    st.info("Geen watchlist setups.")

st.subheader("🔴 Vermijden")
if len(avoid) > 0:
    st.dataframe(avoid[available_columns], use_container_width=True)
else:
    st.success("Geen duidelijke avoid setups.")

st.subheader("📊 Laatste scan")
st.dataframe(latest[available_columns], use_container_width=True)

if os.path.exists(chart_file):
    st.subheader("📈 Beste setup grafiek")
    st.image(chart_file, use_container_width=True)

st.caption("Auto refresh elke 60 seconden")

st.markdown(
    """
    <script>
    setTimeout(function(){
       window.location.reload(1);
    }, 60000);
    </script>
    """,
    unsafe_allow_html=True
)
