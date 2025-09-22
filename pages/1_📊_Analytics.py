import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import func, extract
from ma_tracker.db import get_session
from ma_tracker.models import Deal

st.set_page_config(page_title="M&A Analytics", layout="wide")
st.title("📊 M&A Deal Analytics")

session = get_session()

# Load all deals into a DataFrame
try:
    rows = session.query(
        Deal.announcement_date,
        Deal.acquirer_name,
        Deal.target_name,
        Deal.sector,
        Deal.geography,
        Deal.ev_to_ebitda,
        Deal.enterprise_value,
    ).all()
finally:
    session.close()

if not rows:
    st.info("No deals available. Add or import deals first.")
    st.stop()

df = pd.DataFrame(rows, columns=[
    "announcement_date",
    "acquirer_name",
    "target_name",
    "sector",
    "geography",
    "ev_to_ebitda",
    "enterprise_value",
])

# --- Chart 1: deal volume by month ---
st.subheader("📈 Deal volume over time")

df["month"] = pd.to_datetime(df["announcement_date"]).dt.to_period("M")
vol = df.groupby("month").size()

fig, ax = plt.subplots()
vol.plot(kind="bar", ax=ax)
ax.set_ylabel("Number of deals")
ax.set_xlabel("Month")
st.pyplot(fig)

# --- Chart 2: average EV/EBITDA by sector ---
st.subheader("🏭 Average EV/EBITDA by sector")

sector_ev = df.dropna(subset=["ev_to_ebitda"]).groupby("sector")["ev_to_ebitda"].mean().sort_values()

if not sector_ev.empty:
    fig2, ax2 = plt.subplots()
    sector_ev.plot(kind="barh", ax=ax2)
    ax2.set_xlabel("Average EV/EBITDA")
    st.pyplot(fig2)
else:
    st.info("No EV/EBITDA data available to plot.")
