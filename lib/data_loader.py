from pathlib import Path
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_data(show_spinner=False)
def load_venues():
    df = pd.read_csv(DATA_DIR / "venue_master.csv")
    df["open_date"] = pd.to_datetime(df["open_date"])
    return df


@st.cache_data(show_spinner=False)
def load_guests():
    df = pd.read_csv(DATA_DIR / "guest_master.csv")
    df["first_seen_date"] = pd.to_datetime(df["first_seen_date"])
    df["last_visit_date"] = pd.to_datetime(df["last_visit_date"])
    return df


@st.cache_data(show_spinner=False)
def load_transactions():
    df = pd.read_csv(DATA_DIR / "transactions.csv")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    return df


@st.cache_data(show_spinner=False)
def load_daily_ops():
    df = pd.read_csv(DATA_DIR / "daily_ops_metrics.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(show_spinner=False)
def load_vendors():
    return pd.read_csv(DATA_DIR / "vendor_master.csv")


@st.cache_data(show_spinner=False)
def load_venue_vendor_map():
    return pd.read_csv(DATA_DIR / "venue_vendor_map.csv")


@st.cache_data(show_spinner=False)
def load_events():
    df = pd.read_csv(DATA_DIR / "events_bookings.csv")
    df["event_date"] = pd.to_datetime(df["event_date"])
    return df


@st.cache_data(show_spinner=False)
def load_hiring():
    df = pd.read_csv(DATA_DIR / "hiring_pipeline.csv")
    df["open_date"] = pd.to_datetime(df["open_date"])
    return df


@st.cache_data(show_spinner=False)
def load_plan_targets():
    df = pd.read_csv(DATA_DIR / "plan_targets.csv")
    df["month"] = pd.to_datetime(df["month"])
    return df


@st.cache_data(show_spinner=False)
def load_reservations():
    df = pd.read_csv(DATA_DIR / "reservations_today.csv")
    df["reservation_date"] = pd.to_datetime(df["reservation_date"])
    return df


@st.cache_data(show_spinner=False)
def load_vip_flags():
    return pd.read_csv(DATA_DIR / "vip_flags.csv")


@st.cache_data(show_spinner=False)
def load_alerts():
    df = pd.read_csv(DATA_DIR / "alerts_feed.csv")
    df["raised_at"] = pd.to_datetime(df["raised_at"])
    return df


@st.cache_data(show_spinner=False)
def load_interactions():
    df = pd.read_csv(DATA_DIR / "guest_interactions.csv")
    df["interaction_date"] = pd.to_datetime(df["interaction_date"])
    return df


@st.cache_data(show_spinner=False)
def load_dishes():
    return pd.read_csv(DATA_DIR / "dish_master.csv")


@st.cache_data(show_spinner=False)
def load_fx_rates():
    return pd.read_csv(DATA_DIR / "fx_rates.csv")


@st.cache_data(show_spinner=False)
def load_brand_exposure():
    df = pd.read_csv(DATA_DIR / "brand_exposure_calendar.csv")
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    return df


@st.cache_data(show_spinner=False)
def load_monthly_summary():
    txn = load_transactions()
    txn["month"] = txn["transaction_date"].dt.to_period("M").dt.to_timestamp()
    summary = (
        txn.groupby(["month", "venue_id"])
        .agg(
            revenue_aed=("total_revenue_aed", "sum"),
            food_revenue_aed=("food_revenue_aed", "sum"),
            beverage_revenue_aed=("beverage_revenue_aed", "sum"),
            covers=("cover_count", "sum"),
            transactions=("transaction_id", "count"),
            avg_check=("avg_check_per_cover_aed", "mean"),
            avg_satisfaction=("guest_satisfaction_score", "mean"),
        )
        .reset_index()
    )
    venues = load_venues()[["venue_id", "brand", "sub_brand", "city", "region"]]
    return summary.merge(venues, on="venue_id", how="left")
