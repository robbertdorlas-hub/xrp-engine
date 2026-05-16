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

st.subheader("🏆 Beste setups")

top = latest.head(3)
cols = st.columns(3)
medals = ["🥇", "🥈", "🥉"]

for i, (_, row) in enumerate(top.iterrows()):
    with cols[i]:
        st.metric(
            f"{medals[i]} {row['symbol']}",
            row["prediction"],
            f"Score {row['rank_score']}"
        )
        st.write(f"Breakout: **{row['breakout_probability']}%**")
        st.write(f"Fake risk: **{row['fake_breakout_risk']}%**")
        st.write(f"Trend 1h: **{row['trend_1h']}**")
        st.write(f"RSI 1h: **{round(row['rsi_1h'], 2)}**")

st.subheader("📊 Laatste scan")

columns = [
    "symbol",
    "prediction",
    "rank_score",
    "breakout_probability",
    "fake_breakout_risk",
    "score",
    "price_1h",
    "trend_15m",
    "trend_1h",
    "trend_4h",
    "rsi_15m",
    "rsi_1h",
    "rsi_4h",
    "volume_strength_15m",
    "volume_strength_1h",
    "volume_strength_4h",
]

available_columns = [col for col in columns if col in latest.columns]

st.dataframe(
    latest[available_columns],
    use_container_width=True
)

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
