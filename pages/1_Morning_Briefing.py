import streamlit as st
import pandas as pd

st.set_page_config(page_title="Morning Briefing | ADMO", page_icon="♦", layout="wide")

from lib.style import (
    metric_card_css, fmt_aed, GOLD, OFF_WHITE, RED, AMBER, GREEN, CARD_BG,
    PLOTLY_LAYOUT, SEVERITY_COLORS,
)
from lib.data_loader import (
    load_alerts, load_reservations, load_vip_flags, load_daily_ops,
    load_venues, load_brand_exposure, load_guests,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
st.markdown(f"<h1 style='color:{GOLD};'>Morning Briefing</h1>", unsafe_allow_html=True)
st.caption("Daily snapshot for the Group CEO — alerts, reservations, VIP arrivals, and yesterday's performance")

alerts = load_alerts()
reservations = load_reservations()
vip_flags = load_vip_flags()
daily_ops = load_daily_ops()
venues = load_venues()
exposure = load_brand_exposure()
guests = load_guests()

demo_today = pd.Timestamp("2026-05-01")

# --- Alerts ---
st.subheader("Exception Alerts")
open_alerts = alerts[alerts["status"].isin(["Open", "Investigating", "Escalated"])]
for _, a in open_alerts.sort_values("severity", key=lambda s: s.map({"Red": 0, "Amber": 1, "Green": 2})).iterrows():
    sev_color = SEVERITY_COLORS.get(a["severity"], OFF_WHITE)
    venue_name = venues.loc[venues["venue_id"] == a["venue_id"], "sub_brand"].values
    vname = venue_name[0] if len(venue_name) > 0 else a["venue_id"]
    st.markdown(
        f"<div style='background:{CARD_BG}; border-left:4px solid {sev_color}; "
        f"border-radius:6px; padding:12px 16px; margin-bottom:10px;'>"
        f"<strong style='color:{sev_color};'>{a['severity']}</strong> &nbsp;|&nbsp; "
        f"<strong style='color:{OFF_WHITE};'>{a['headline']}</strong><br/>"
        f"<span style='color:#9BA8B8; font-size:0.85rem;'>{vname} &mdash; {a['description']}</span><br/>"
        f"<span style='color:#9BA8B8; font-size:0.8rem;'>Owner: {a['owner']} &nbsp;|&nbsp; "
        f"Status: {a['status']}</span></div>",
        unsafe_allow_html=True,
    )

st.divider()

# --- Today's Reservations ---
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Reservations — Next 7 Days")
    upcoming = reservations[
        (reservations["reservation_date"] >= demo_today)
        & (reservations["reservation_date"] <= demo_today + pd.Timedelta(days=7))
    ]
    daily_res = (
        upcoming.merge(venues[["venue_id", "sub_brand"]], on="venue_id", how="left")
        .groupby(["reservation_date", "sub_brand"])
        .agg(bookings=("reservation_id", "count"), covers=("party_size", "sum"))
        .reset_index()
    )
    day_totals = upcoming.groupby("reservation_date").agg(
        bookings=("reservation_id", "count"), covers=("party_size", "sum")
    ).reset_index()

    import plotly.express as px

    if not day_totals.empty:
        fig = px.bar(
            day_totals, x="reservation_date", y="covers",
            labels={"reservation_date": "", "covers": "Expected Covers"},
            color_discrete_sequence=[GOLD],
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=280)
        fig.update_xaxes(gridcolor="#2A3950")
        fig.update_yaxes(gridcolor="#2A3950")
        st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Bookings (7d)", f"{upcoming.shape[0]:,}")
    c2.metric("Expected Covers", f"{upcoming['party_size'].sum():,}")
    c3.metric("Waitlisted", f"{(upcoming['status'] == 'Waitlist').sum()}")

with col_right:
    st.subheader("VIP Arrivals — Next 7 Days")
    vip_guest_ids = set(vip_flags["guest_id"])
    vip_reservations = upcoming[upcoming["guest_id"].isin(vip_guest_ids)]
    vip_detail = vip_reservations.merge(
        vip_flags[["guest_id", "category", "sensitivity_level"]], on="guest_id", how="left"
    ).merge(venues[["venue_id", "sub_brand"]], on="venue_id", how="left")

    if vip_detail.empty:
        st.info("No VIP reservations in the next 7 days.")
    else:
        for _, v in vip_detail.iterrows():
            sens_color = RED if v["sensitivity_level"] == "Maximum" else AMBER
            st.markdown(
                f"<div style='background:{CARD_BG}; border-left:4px solid {sens_color}; "
                f"border-radius:6px; padding:10px 14px; margin-bottom:8px;'>"
                f"<strong style='color:{GOLD};'>{v['guest_id']}</strong> &mdash; "
                f"<span style='color:{OFF_WHITE};'>{v['category']}</span><br/>"
                f"<span style='color:#9BA8B8; font-size:0.85rem;'>"
                f"{v['sub_brand']} &bull; {v['reservation_date'].strftime('%b %d')} &bull; "
                f"Party of {v['party_size']}</span></div>",
                unsafe_allow_html=True,
            )

st.divider()

# --- Yesterday's Performance ---
st.subheader("Yesterday's Performance Snapshot")
yesterday = demo_today - pd.Timedelta(days=1)
yest_ops = daily_ops[daily_ops["date"] == yesterday].merge(
    venues[["venue_id", "sub_brand", "brand"]], on="venue_id", how="left"
)

if yest_ops.empty:
    st.info("No operational data for yesterday.")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", fmt_aed(yest_ops["revenue_total_aed"].sum()))
    c2.metric("Total Covers", f"{yest_ops['covers_total'].sum():,}")
    c3.metric("Avg NPS", f"{yest_ops['nps_score'].mean():.0f}")
    c4.metric("Active Venues", f"{yest_ops['venue_id'].nunique()}")

    top5 = yest_ops.nlargest(5, "revenue_total_aed")[["sub_brand", "revenue_total_aed", "covers_total", "nps_score"]]
    top5.columns = ["Venue", "Revenue (AED)", "Covers", "NPS"]
    top5["Revenue (AED)"] = top5["Revenue (AED)"].apply(lambda x: fmt_aed(x))
    st.markdown("**Top 5 Venues by Revenue**")
    st.dataframe(top5, use_container_width=True, hide_index=True)

st.divider()

# --- Upcoming Brand Exposure ---
st.subheader("Upcoming Brand Exposure Events")
upcoming_exp = exposure[exposure["end_date"] >= demo_today].sort_values("start_date")
if upcoming_exp.empty:
    st.info("No upcoming exposure events.")
else:
    exp_display = upcoming_exp.merge(venues[["venue_id", "sub_brand"]], on="venue_id", how="left")
    for _, e in exp_display.iterrows():
        level_color = RED if e["exposure_level"] == "Maximum" else (AMBER if e["exposure_level"] == "High" else GREEN)
        st.markdown(
            f"<div style='background:{CARD_BG}; border-left:4px solid {level_color}; "
            f"border-radius:6px; padding:10px 14px; margin-bottom:8px;'>"
            f"<strong style='color:{GOLD};'>{e['name']}</strong><br/>"
            f"<span style='color:{OFF_WHITE};'>{e['sub_brand']} &bull; "
            f"{e['start_date'].strftime('%b %d')} – {e['end_date'].strftime('%b %d, %Y')}</span><br/>"
            f"<span style='color:#9BA8B8; font-size:0.85rem;'>{e['notes']}</span></div>",
            unsafe_allow_html=True,
        )
