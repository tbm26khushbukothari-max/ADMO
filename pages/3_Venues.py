import streamlit as st

st.set_page_config(page_title="Venues | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state, alert_card,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, CARD_BG,
    PLOTLY_LAYOUT, SEVERITY_COLORS,
)
from lib.data import (
    load_venues, load_daily_ops, load_monthly_summary, load_transactions,
    load_dishes, load_alerts, get_scope_venue_ids, filter_by_scope,
    compute_anomaly_flags, compute_slot_splits,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Venues", f"Scope: {scope_desc(scope)}")

if not venue_ids:
    empty_state()
    st.stop()

venue_list = sorted(venues[venues["venue_id"].isin(venue_ids)]["sub_brand"].tolist())
selected_venue_name = st.selectbox("Select venue for drill-down", venue_list)
sel_row = venues[venues["sub_brand"] == selected_venue_name]
if sel_row.empty:
    empty_state()
    st.stop()

sel_vid = sel_row.iloc[0]["venue_id"]
daily_ops = load_daily_ops()
summary = load_monthly_summary()
txn = load_transactions()
dishes = load_dishes()
alerts = load_alerts()

venue_ops = daily_ops[daily_ops["venue_id"] == sel_vid].sort_values("date")
venue_summary = summary[summary["venue_id"] == sel_vid]
venue_txn = txn[txn["venue_id"] == sel_vid]
venue_dishes = dishes[dishes["venue_id"] == sel_vid]
venue_alerts = alerts[alerts["venue_id"] == sel_vid]

# ── Venue scorecard ─────────────────────────────────────────────

if venue_ops.empty:
    empty_state("No operational data for this venue.")
    st.stop()

rev = venue_summary["revenue_aed"].sum()
covers = venue_summary["covers"].sum()
avg_occ = venue_ops["occupancy_pct"].mean()
avg_nps = venue_ops["nps_score"].mean()
avg_check = rev / covers if covers else 0
avg_food_cost = venue_ops["food_cost_pct"].mean()
avg_labor_cost = venue_ops["labor_cost_pct"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", fmt_currency(rev, ccy))
c2.metric("Covers", f"{covers:,.0f}")
c3.metric("Avg Occupancy", f"{avg_occ:.0%}")
c4.metric("Avg NPS", f"{avg_nps:.0f}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Avg Check", fmt_currency(avg_check, ccy))
c6.metric("Food Cost %", f"{avg_food_cost:.1%}")
c7.metric("Labour Cost %", f"{avg_labor_cost:.1%}")
c8.metric("Capacity", str(sel_row.iloc[0]["seat_capacity"]))

st.divider()

# ── 90-day revenue trend with anomaly flags ─────────────────────

st.subheader("90-Day Revenue Trend")
recent_ops = venue_ops.tail(90)
anomalies = compute_anomaly_flags(daily_ops, sel_vid)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=recent_ops["date"], y=recent_ops["revenue_total_aed"],
    mode="lines", name="Daily Revenue",
    line=dict(color=GOLD, width=1.5),
))
if not anomalies.empty:
    anomalies_90 = anomalies[anomalies["date"].isin(recent_ops["date"])]
    if not anomalies_90.empty:
        fig.add_trace(go.Scatter(
            x=anomalies_90["date"], y=anomalies_90["revenue_total_aed"],
            mode="markers", name="Anomaly",
            marker=dict(color=RED, size=8, symbol="circle"),
        ))
fig.update_layout(**PLOTLY_LAYOUT, height=320, legend=dict(orientation="h", y=1.12))
fig.update_yaxes(gridcolor="#2A3950")
fig.update_xaxes(gridcolor="#2A3950")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Service-slot mix + F&B split ────────────────────────────────

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Service Slot Mix")
    slots = compute_slot_splits(txn, {sel_vid})
    if not slots.empty:
        fig_slot = px.pie(
            values=slots.values, names=slots.index,
            color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C"],
            hole=0.4,
        )
        fig_slot.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_slot.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_slot, use_container_width=True)

with col_r:
    st.subheader("Food vs Beverage Split")
    food_rev = venue_summary["food_revenue_aed"].sum()
    bev_rev = venue_summary["beverage_revenue_aed"].sum()
    fig_fb = px.pie(
        values=[food_rev, bev_rev], names=["Food", "Beverage"],
        color_discrete_sequence=[GOLD, "#5A7D3C"], hole=0.4,
    )
    fig_fb.update_layout(**PLOTLY_LAYOUT, height=280)
    fig_fb.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_fb, use_container_width=True)

st.divider()

# ── Dish-level revenue ──────────────────────────────────────────

st.subheader("Dish Menu")
if venue_dishes.empty:
    empty_state("No dish data.")
else:
    dish_display = venue_dishes[["dish_name", "price_aed", "food_cost_pct", "margin_aed", "signature_flag", "category"]].copy()
    dish_display.columns = ["Dish", "Price (AED)", "Food Cost %", "Margin (AED)", "Signature", "Category"]
    dish_display["Food Cost %"] = (dish_display["Food Cost %"] * 100).round(1).astype(str) + "%"
    st.dataframe(dish_display.sort_values("Margin (AED)", ascending=False),
                 use_container_width=True, hide_index=True)

st.divider()

# ── Venue alerts ────────────────────────────────────────────────

st.subheader("Venue Alerts")
open_v_alerts = venue_alerts[venue_alerts["status"].isin(["Open", "Investigating", "Escalated"])]
if open_v_alerts.empty:
    empty_state("No active alerts for this venue.")
else:
    for _, a in open_v_alerts.iterrows():
        alert_card(a["severity"], a["headline"], description=a["description"],
                   owner=a["owner"], status=a["status"])
