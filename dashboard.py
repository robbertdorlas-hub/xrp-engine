import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(
    page_title="XRP Dashboard",
    layout="wide"
)

st.title("🚀 XRP Dashboard")

log_file = "/data/xrp_prediction_log.csv"
chart_file = "/data/xrp_chart.png"

if os.path.exists(log_file):
    df = pd.read_csv(log_file)

    st.subheader("Laatste voorspellingen")
    st.dataframe(df.tail(20), use_container_width=True)

    laatste = df.iloc[-1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Breakout kans", f"{laatste['breakout_probability']}%")

    with col2:
        st.metric("Fake breakout risk", f"{laatste['fake_breakout_risk']}%")

    with col3:
        st.metric("Voorspelling", laatste['prediction'])

else:
    st.warning("Nog geen logbestand gevonden")

if os.path.exists(chart_file):
    st.subheader("Laatste grafiek")
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
