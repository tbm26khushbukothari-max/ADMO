import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Brand Operations | ADMO", page_icon="♦", layout="wide")

from lib.style import (
    metric_card_css, fmt_aed, GOLD, OFF_WHITE, CARD_BG,
    PLOTLY_LAYOUT, BRAND_COLORS,
)
from lib.data_loader import (
    load_monthly_summary, load_venues, load_daily_ops, load_plan_targets, load_dishes,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
st.markdown(f"<h1 style='color:{GOLD};'>Brand Operations</h1>", unsafe_allow_html=True)
st.caption("Per-brand drill-down — revenue, occupancy, cost structure, and signature dishes")

summary = load_monthly_summary()
venues = load_venues()
daily_ops = load_daily_ops()
targets = load_plan_targets()
dishes = load_dishes()

# --- Brand Selector ---
brands = sorted(summary["brand"].dropna().unique())
selected_brand = st.selectbox("Select Brand", brands, index=0)

brand_venues = venues[venues["brand"] == selected_brand]
brand_data = summary[summary["brand"] == selected_brand]
brand_venue_ids = set(brand_venues["venue_id"])
brand_ops = daily_ops[daily_ops["venue_id"].isin(brand_venue_ids)].merge(
    venues[["venue_id", "sub_brand"]], on="venue_id", how="left"
)

# --- Brand KPIs ---
brand_rev = brand_data["revenue_aed"].sum()
brand_covers = brand_data["covers"].sum()
brand_txn = brand_data["transactions"].sum()
avg_check = brand_rev / brand_covers if brand_covers > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Brand Revenue", fmt_aed(brand_rev))
c2.metric("Total Covers", f"{brand_covers:,.0f}")
c3.metric("Venues", str(brand_venues.shape[0]))
c4.metric("Avg Check / Cover", fmt_aed(avg_check))

st.divider()

# --- Monthly Revenue Trend vs Plan ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Monthly Revenue Trend")
    monthly = brand_data.groupby("month")["revenue_aed"].sum().reset_index()
    brand_targets = targets[targets["venue_id"].isin(brand_venue_ids)]
    monthly_plan = brand_targets.groupby("month")["revenue_target_aed"].sum().reset_index()
    merged = monthly.merge(monthly_plan, on="month", how="outer").sort_values("month")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged["month"], y=merged["revenue_aed"],
        mode="lines+markers", name="Actual",
        line=dict(color=BRAND_COLORS.get(selected_brand, GOLD), width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=merged["month"], y=merged["revenue_target_aed"],
        mode="lines", name="Plan",
        line=dict(color="#9BA8B8", width=1.5, dash="dash"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=320, legend=dict(orientation="h", y=1.12))
    fig.update_yaxes(gridcolor="#2A3950")
    fig.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Venue Revenue Comparison")
    venue_rev = brand_data.groupby("sub_brand")["revenue_aed"].sum().sort_values(ascending=True).reset_index()
    fig_v = px.bar(
        venue_rev, x="revenue_aed", y="sub_brand", orientation="h",
        color_discrete_sequence=[BRAND_COLORS.get(selected_brand, GOLD)],
        labels={"revenue_aed": "Revenue (AED)", "sub_brand": ""},
    )
    fig_v.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
    fig_v.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_v, use_container_width=True)

st.divider()

# --- Occupancy & Cost Structure ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Average Occupancy by Venue")
    if not brand_ops.empty:
        occ = brand_ops.groupby("sub_brand")["occupancy_pct"].mean().sort_values(ascending=True).reset_index()
        fig_occ = px.bar(
            occ, x="occupancy_pct", y="sub_brand", orientation="h",
            color_discrete_sequence=[BRAND_COLORS.get(selected_brand, GOLD)],
            labels={"occupancy_pct": "Avg Occupancy %", "sub_brand": ""},
        )
        fig_occ.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
        fig_occ.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
        st.plotly_chart(fig_occ, use_container_width=True)

with col2:
    st.subheader("Cost Structure (Food vs Labour)")
    if not brand_ops.empty:
        cost = brand_ops.groupby("sub_brand").agg(
            food_cost=("food_cost_pct", "mean"),
            labor_cost=("labor_cost_pct", "mean"),
        ).reset_index()
        cost_melted = cost.melt(id_vars="sub_brand", var_name="Cost Type", value_name="Percentage")
        cost_melted["Cost Type"] = cost_melted["Cost Type"].map({"food_cost": "Food Cost %", "labor_cost": "Labour Cost %"})
        fig_cost = px.bar(
            cost_melted, x="Percentage", y="sub_brand", color="Cost Type",
            orientation="h", barmode="group",
            color_discrete_sequence=["#C84B31", "#D89B3F"],
            labels={"sub_brand": ""},
        )
        fig_cost.update_layout(**PLOTLY_LAYOUT, height=320)
        fig_cost.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
        st.plotly_chart(fig_cost, use_container_width=True)

st.divider()

# --- Food vs Beverage Revenue Split ---
st.subheader("Food vs Beverage Split")
fb_split = brand_data.groupby("sub_brand").agg(
    food=("food_revenue_aed", "sum"),
    beverage=("beverage_revenue_aed", "sum"),
).reset_index()
fb_melted = fb_split.melt(id_vars="sub_brand", var_name="Category", value_name="Revenue")
fb_melted["Category"] = fb_melted["Category"].map({"food": "Food", "beverage": "Beverage"})
fig_fb = px.bar(
    fb_melted, x="sub_brand", y="Revenue", color="Category",
    barmode="stack",
    color_discrete_sequence=[GOLD, "#5A7D3C"],
    labels={"sub_brand": "", "Revenue": "Revenue (AED)"},
)
fig_fb.update_layout(**PLOTLY_LAYOUT, height=320)
fig_fb.update_yaxes(gridcolor="#2A3950")
st.plotly_chart(fig_fb, use_container_width=True)

st.divider()

# --- Signature Dishes ---
st.subheader("Signature Dishes")
brand_dishes = dishes[dishes["venue_id"].isin(brand_venue_ids)]
sig_dishes = brand_dishes[brand_dishes["signature_flag"] == "Yes"].merge(
    venues[["venue_id", "sub_brand"]], on="venue_id", how="left"
)
if sig_dishes.empty:
    st.info("No signature dishes found for this brand.")
else:
    display_cols = ["sub_brand", "dish_name", "price_aed", "food_cost_pct", "margin_aed", "category"]
    sig_display = sig_dishes[display_cols].copy()
    sig_display.columns = ["Venue", "Dish", "Price (AED)", "Food Cost %", "Margin (AED)", "Category"]
    sig_display["Food Cost %"] = (sig_display["Food Cost %"] * 100).round(1).astype(str) + "%"
    st.dataframe(sig_display.sort_values("Margin (AED)", ascending=False), use_container_width=True, hide_index=True)
