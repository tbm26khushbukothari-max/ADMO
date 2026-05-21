import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Group CEO | ADMO", page_icon="♦", layout="wide")

from lib.style import (
    metric_card_css, fmt_aed, fmt_usd, GOLD, OFF_WHITE, CARD_BG,
    PLOTLY_LAYOUT, BRAND_COLORS,
)
from lib.data_loader import (
    load_monthly_summary, load_venues, load_guests, load_transactions,
    load_plan_targets, load_events,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
st.markdown(f"<h1 style='color:{GOLD};'>Group CEO View</h1>", unsafe_allow_html=True)
st.caption("Portfolio-level performance, revenue vs plan, and the cross-brand intelligence story")

summary = load_monthly_summary()
venues = load_venues()
guests = load_guests()
targets = load_plan_targets()
events = load_events()

# --- Top-line KPIs ---
total_rev = summary["revenue_aed"].sum()
total_covers = summary["covers"].sum()
total_txn = summary["transactions"].sum()
avg_check = total_rev / total_covers if total_covers > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Portfolio Revenue", fmt_aed(total_rev))
c2.metric("USD Equivalent", fmt_usd(total_rev / 3.67))
c3.metric("Total Covers", f"{total_covers:,.0f}")
c4.metric("Avg Check / Cover", fmt_aed(avg_check))

st.divider()

# --- Revenue vs Plan ---
st.subheader("Monthly Revenue vs Plan")
monthly_actual = summary.groupby("month")["revenue_aed"].sum().reset_index()
monthly_plan = targets.groupby("month")["revenue_target_aed"].sum().reset_index()

merged = monthly_actual.merge(monthly_plan, on="month", how="outer").sort_values("month")

fig_plan = go.Figure()
fig_plan.add_trace(go.Scatter(
    x=merged["month"], y=merged["revenue_aed"],
    mode="lines+markers", name="Actual",
    line=dict(color=GOLD, width=2.5),
    marker=dict(size=6),
))
fig_plan.add_trace(go.Scatter(
    x=merged["month"], y=merged["revenue_target_aed"],
    mode="lines", name="Plan",
    line=dict(color="#9BA8B8", width=1.5, dash="dash"),
))
fig_plan.update_layout(**PLOTLY_LAYOUT, height=350, legend=dict(orientation="h", y=1.12))
fig_plan.update_yaxes(gridcolor="#2A3950", gridwidth=0.5)
fig_plan.update_xaxes(gridcolor="#2A3950", gridwidth=0.5)
st.plotly_chart(fig_plan, use_container_width=True)

st.divider()

# --- Revenue by Brand and Region ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Revenue by Brand")
    brand_rev = summary.groupby("brand")["revenue_aed"].sum().reset_index().sort_values("revenue_aed", ascending=False)
    fig_brand = px.bar(
        brand_rev, x="brand", y="revenue_aed",
        color="brand", color_discrete_map=BRAND_COLORS,
        labels={"revenue_aed": "Revenue (AED)", "brand": ""},
    )
    fig_brand.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
    fig_brand.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_brand, use_container_width=True)

with col_right:
    st.subheader("Revenue by Region")
    region_rev = summary.groupby("region")["revenue_aed"].sum().reset_index().sort_values("revenue_aed", ascending=False)
    fig_region = px.bar(
        region_rev, x="region", y="revenue_aed",
        color_discrete_sequence=[GOLD],
        labels={"revenue_aed": "Revenue (AED)", "region": ""},
    )
    fig_region.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
    fig_region.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_region, use_container_width=True)

st.divider()

# --- Cross-Brand Intelligence (the key story) ---
st.subheader("Cross-Brand Intelligence")
st.caption("Multi-brand guests represent a disproportionate share of revenue — the core value proposition of group-level data")

multi_brand = guests[guests["brands_visited_count"] >= 2]
single_brand = guests[guests["brands_visited_count"] == 1]

multi_pct_base = len(multi_brand) / len(guests) * 100
multi_ltv = multi_brand["lifetime_spend_aed"].sum()
single_ltv = single_brand["lifetime_spend_aed"].sum()
total_ltv = multi_ltv + single_ltv
multi_pct_rev = multi_ltv / total_ltv * 100 if total_ltv > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Multi-Brand Guests", f"{len(multi_brand):,}")
col2.metric("% of Guest Base", f"{multi_pct_base:.0f}%")
col3.metric("% of Lifetime Revenue", f"{multi_pct_rev:.0f}%")
col4.metric("Avg LTV (Multi)", fmt_aed(multi_brand["lifetime_spend_aed"].mean()))

col_l, col_r = st.columns(2)

with col_l:
    tier_dist = guests.groupby(["guest_tier", guests["brands_visited_count"].clip(upper=3).map(
        {1: "Single brand", 2: "2 brands", 3: "3+ brands"}
    )]).size().reset_index(name="count")
    tier_dist.columns = ["Tier", "Brand Reach", "Count"]
    fig_tier = px.bar(
        tier_dist, x="Tier", y="Count", color="Brand Reach",
        barmode="group",
        color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31"],
        category_orders={"Tier": ["Diamond", "Platinum", "Gold", "Standard"]},
    )
    fig_tier.update_layout(**PLOTLY_LAYOUT, height=300)
    fig_tier.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_tier, use_container_width=True)

with col_r:
    brand_reach = guests["brands_visited_count"].value_counts().sort_index().reset_index()
    brand_reach.columns = ["Brands Visited", "Guest Count"]
    fig_reach = px.pie(
        brand_reach, values="Guest Count", names="Brands Visited",
        color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C"],
        hole=0.45,
    )
    fig_reach.update_layout(**PLOTLY_LAYOUT, height=300)
    fig_reach.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_reach, use_container_width=True)

st.divider()

# --- Top Venues ---
st.subheader("Top 10 Venues by Revenue")
venue_rev = summary.groupby(["venue_id", "sub_brand", "brand"])["revenue_aed"].sum().reset_index()
top10 = venue_rev.nlargest(10, "revenue_aed")
fig_top = px.bar(
    top10.sort_values("revenue_aed"),
    x="revenue_aed", y="sub_brand", orientation="h",
    color="brand", color_discrete_map=BRAND_COLORS,
    labels={"revenue_aed": "Revenue (AED)", "sub_brand": ""},
)
fig_top.update_layout(**PLOTLY_LAYOUT, height=400)
fig_top.update_xaxes(gridcolor="#2A3950")
st.plotly_chart(fig_top, use_container_width=True)

# --- Events Revenue ---
st.subheader("Events & Private Dining Revenue")
events_monthly = events.copy()
events_monthly["month"] = events_monthly["event_date"].dt.to_period("M").dt.to_timestamp()
ev_summary = events_monthly.groupby(["month", "event_type"])["total_revenue_aed"].sum().reset_index()
fig_ev = px.bar(
    ev_summary, x="month", y="total_revenue_aed", color="event_type",
    color_discrete_sequence=[GOLD, "#C84B31", "#5A7D3C", "#D89B3F"],
    labels={"total_revenue_aed": "Revenue (AED)", "month": "", "event_type": "Type"},
)
fig_ev.update_layout(**PLOTLY_LAYOUT, height=300)
fig_ev.update_yaxes(gridcolor="#2A3950")
st.plotly_chart(fig_ev, use_container_width=True)
