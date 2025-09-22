# 💼 M&A Deal Tracker

A Streamlit app for tracking M&A (Mergers & Acquisitions) deals.  
Built with Python, SQLAlchemy, and Streamlit.

---

## ✨ Features
- **Database**: SQLite via SQLAlchemy with a `Deal` model.
- **Streamlit UI**:
  - Initialize database with one click
  - Manual form to add deals
  - Recent deals preview
  - Bulk CSV upload
  - Import press releases from RSS feeds
- **Analytics Page**:
  - Deal volume over time (monthly)
  - Average EV/EBITDA by sector

---

## 📂 Project structure
ma-deal-tracker/
├─ ma_tracker/ # app package (DB, models, scraping)
├─ pages/ # multipage Streamlit analytics
├─ data/ # local SQLite database
├─ streamlit_app.py # main Streamlit entrypoint
├─ requirements.txt # dependencies
└─ .gitignore