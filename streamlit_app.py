import streamlit as st
from datetime import date as dt_date
from decimal import Decimal, InvalidOperation
import pandas as pd
from sqlalchemy import func
from ma_tracker.scrape.rss import fetch_rss
from ma_tracker.db import Base, engine, get_session
from ma_tracker.models import Deal, DealStatus
from datetime import datetime

st.set_page_config(page_title="M&A Deal Tracker", layout="wide")
st.title("💼 M&A Deal Tracker")

# --- DB init ---
if st.button("Initialize Database"):
    Base.metadata.create_all(bind=engine)
    st.success("✅ Database initialized!")

# --- DB status ---
with st.expander("Database status", expanded=True):
    session = get_session()
    try:
        n_deals = session.query(func.count(Deal.id)).scalar() or 0
    finally:
        session.close()
    st.write(f"📦 Deals stored: **{n_deals}**")

st.divider()

# --- Add Deal (manual form) ---
st.subheader("➕ Add a deal (manual)")

with st.form("add_deal_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        announcement_date = st.date_input("Announcement date", value=None, format="YYYY-MM-DD")
        sector = st.text_input("Sector", placeholder="Software")
        geography = st.text_input("Geography", placeholder="North America")
    with c2:
        acquirer_name = st.text_input("Acquirer name", placeholder="Acquirer Inc.")
        enterprise_value = st.text_input("Enterprise value (USD)", placeholder="e.g. 1500000000")
        ebitda = st.text_input("EBITDA (USD)", placeholder="e.g. 150000000")
    with c3:
        target_name = st.text_input("Target name", placeholder="Target Ltd.")
        deal_value_usd = st.text_input("Headline deal value (USD)", placeholder="optional")
        source_url = st.text_input("Source URL (press release)", placeholder="https://...")
    
    status = st.selectbox(
        "Status",
        options=[DealStatus.ANNOUNCED.value, DealStatus.CLOSED.value, DealStatus.TERMINATED.value],
        index=0,
    )
    notes = st.text_area("Notes", placeholder="Key details, structure, etc.", height=80)

    submitted = st.form_submit_button("Save deal")

if submitted:
    def to_decimal_or_none(x: str):
        x = (x or "").strip().replace(",", "")
        if not x:
            return None
        try:
            return Decimal(x)
        except (InvalidOperation, ValueError):
            return None

    session = get_session()
    try:
        d = Deal(
            announcement_date=announcement_date if isinstance(announcement_date, dt_date) else None,
            acquirer_name=acquirer_name.strip(),
            target_name=target_name.strip(),
            deal_value_usd=to_decimal_or_none(deal_value_usd),
            currency="USD",
            enterprise_value=to_decimal_or_none(enterprise_value),
            ebitda=to_decimal_or_none(ebitda),
            sector=sector.strip() or None,
            geography=geography.strip() or None,
            status=DealStatus(status),
            source_url=source_url.strip() or None,
            notes=notes.strip() or None,
        )

        if d.enterprise_value and d.ebitda and d.ebitda != 0:
            d.ev_to_ebitda = float(d.enterprise_value / d.ebitda)

        errors = []
        if not d.acquirer_name:
            errors.append("Acquirer name is required.")
        if not d.target_name:
            errors.append("Target name is required.")
        if errors:
            st.error(" ; ".join(errors))
        else:
            session.add(d)
            session.commit()
            st.success("✅ Deal saved.")
    except Exception as e:
        session.rollback()
        st.error(f"Failed to save deal: {e}")
    finally:
        session.close()

# --- Recent deals preview ---
st.subheader("📄 Recent deals")
session = get_session()
try:
    rows = (
        session.query(
            Deal.id,
            Deal.announcement_date,
            Deal.acquirer_name,
            Deal.target_name,
            Deal.sector,
            Deal.geography,
            Deal.ev_to_ebitda,
        )
        .order_by(Deal.announcement_date.desc().nullslast(), Deal.id.desc())
        .limit(10)
        .all()
    )
finally:
    session.close()

if rows:
    st.dataframe(
        [{"ID": r.id,
          "Date": r.announcement_date,
          "Acquirer": r.acquirer_name,
          "Target": r.target_name,
          "Sector": r.sector,
          "Geo": r.geography,
          "EV/EBITDA": float(r.ev_to_ebitda) if r.ev_to_ebitda is not None else None}
         for r in rows],
        use_container_width=True
    )
else:
    st.info("No deals yet — add one above.")

st.divider()

# --- Bulk upload CSV ---
st.subheader("📂 Bulk upload (CSV)")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        st.write("CSV Preview:")
        st.dataframe(df.head(), use_container_width=True)

        if st.button("Import into DB"):
            required_cols = {"acquirer_name", "target_name"}
            missing = required_cols - set(df.columns)
            if missing:
                st.error(f"CSV missing required columns: {missing}")
            else:
                session = get_session()
                count_added = 0
                try:
                    for _, row in df.iterrows():
                        d = Deal(
                            announcement_date=pd.to_datetime(row.get("announcement_date")).date()
                            if pd.notnull(row.get("announcement_date")) else None,
                            acquirer_name=str(row.get("acquirer_name", "")).strip(),
                            target_name=str(row.get("target_name", "")).strip(),
                            deal_value_usd=row.get("deal_value_usd"),
                            currency=row.get("currency") if pd.notnull(row.get("currency")) else "USD",
                            enterprise_value=row.get("enterprise_value"),
                            ebitda=row.get("ebitda"),
                            sector=row.get("sector") if pd.notnull(row.get("sector")) else None,
                            geography=row.get("geography") if pd.notnull(row.get("geography")) else None,
                            status=DealStatus(row.get("status")) if pd.notnull(row.get("status")) else DealStatus.ANNOUNCED,
                            source_url=row.get("source_url") if pd.notnull(row.get("source_url")) else None,
                            notes=row.get("notes") if pd.notnull(row.get("notes")) else None,
                        )
                        if d.enterprise_value and d.ebitda and d.ebitda != 0:
                            d.ev_to_ebitda = float(d.enterprise_value / d.ebitda)
                        if d.acquirer_name and d.target_name:
                            session.add(d)
                            count_added += 1
                    session.commit()
                    st.success(f"✅ Imported {count_added} deals from CSV")
                except Exception as e:
                    session.rollback()
                    st.error(f"Failed import: {e}")
                finally:
                    session.close()
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
st.divider()
st.subheader("📰 Import from RSS / press release feed (preview)")

with st.form("rss_fetch_form"):
    rss_url = st.text_input(
        "RSS/Atom feed URL",
        placeholder="https://example.com/press-releases/rss.xml"
    )
    limit = st.number_input("Max items", min_value=1, max_value=200, value=25, step=1)
    fetch_clicked = st.form_submit_button("Fetch feed")

if fetch_clicked:
    if not rss_url.strip():
        st.warning("Please provide a feed URL.")
    else:
        try:
            items = fetch_rss(rss_url.strip(), limit=int(limit))
            if not items:
                st.info("No items found in that feed.")
            else:
                st.success(f"Fetched {len(items)} items.")
                preview = [
                    {
                        "published": i["published"],
                        "title": i["title"],
                        "link": i["link"],
                        "summary": i["summary"][:200] + ("..." if len(i["summary"]) > 200 else "")
                    }
                    for i in items
                ]
                st.dataframe(preview, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to fetch/parse feed: {e}")
