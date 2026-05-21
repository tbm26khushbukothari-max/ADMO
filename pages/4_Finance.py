import streamlit as st

st.set_page_config(page_title="Finance | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, AMBER, GREEN, CARD_BG,
    PLOTLY_LAYOUT,
)
from lib.data import (
    load_monthly_summary, load_venues, load_daily_ops, load_events,
    load_savings, get_scope_venue_ids, filter_by_scope,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Finance", f"Scope: {scope_desc(scope)}")

summary = filter_by_scope(load_monthly_summary(), venue_ids)
daily_ops = filter_by_scope(load_daily_ops(), venue_ids)
events = filter_by_scope(load_events(), venue_ids)
savings = load_savings()

if summary.empty:
    empty_state()
    st.stop()

# ── P&L summary ─────────────────────────────────────────────────

st.subheader("P&L Summary")
total_rev = summary["revenue_aed"].sum()
food_rev = summary["food_revenue_aed"].sum()
bev_rev = summary["beverage_revenue_aed"].sum()

avg_food_cost_pct = daily_ops["food_cost_pct"].mean() if not daily_ops.empty else 0
avg_labor_cost_pct = daily_ops["labor_cost_pct"].mean() if not daily_ops.empty else 0
food_cost = total_rev * avg_food_cost_pct
labor_cost = total_rev * avg_labor_cost_pct
gross_margin = total_rev - food_cost - labor_cost
events_rev = events["total_revenue_aed"].sum() if not events.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", fmt_currency(total_rev, ccy))
c2.metric("Food Cost", fmt_currency(food_cost, ccy))
c3.metric("Labour Cost", fmt_currency(labor_cost, ccy))
c4.metric("Gross Margin", fmt_currency(gross_margin, ccy))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Food Revenue", fmt_currency(food_rev, ccy))
c6.metric("Beverage Revenue", fmt_currency(bev_rev, ccy))
c7.metric("Events Revenue", fmt_currency(events_rev, ccy))
c8.metric("Gross Margin %", f"{gross_margin / total_rev * 100:.1f}%" if total_rev else "—")

st.divider()

# ── Cost structure vs benchmark ─────────────────────────────────

st.subheader("Cost Structure vs Portfolio Benchmark")

if not daily_ops.empty:
    all_ops = load_daily_ops()
    portfolio_food_median = all_ops["food_cost_pct"].median()
    portfolio_labor_median = all_ops["labor_cost_pct"].median()

    venue_costs = daily_ops.merge(
        venues[["venue_id", "sub_brand"]], on="venue_id", how="left"
    ).groupby("sub_brand").agg(
        food_cost=("food_cost_pct", "mean"),
        labor_cost=("labor_cost_pct", "mean"),
    ).reset_index()

    col_l, col_r = st.columns(2)

    with col_l:
        fig_food = px.bar(
            venue_costs.sort_values("food_cost"),
            x="food_cost", y="sub_brand", orientation="h",
            color=venue_costs.sort_values("food_cost")["food_cost"].apply(
                lambda x: "Above" if x > portfolio_food_median + 0.03 else "Normal"
            ),
            color_discrete_map={"Above": RED, "Normal": GOLD},
            labels={"food_cost": "Food Cost %", "sub_brand": ""},
        )
        fig_food.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False, title="Food Cost %")
        fig_food.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
        fig_food.add_vline(x=portfolio_food_median, line_dash="dash", line_color="#9BA8B8",
                           annotation_text=f"Median {portfolio_food_median:.0%}")
        st.plotly_chart(fig_food, use_container_width=True)

    with col_r:
        fig_labor = px.bar(
            venue_costs.sort_values("labor_cost"),
            x="labor_cost", y="sub_brand", orientation="h",
            color=venue_costs.sort_values("labor_cost")["labor_cost"].apply(
                lambda x: "Above" if x > portfolio_labor_median + 0.03 else "Normal"
            ),
            color_discrete_map={"Above": RED, "Normal": GOLD},
            labels={"labor_cost": "Labour Cost %", "sub_brand": ""},
        )
        fig_labor.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False, title="Labour Cost %")
        fig_labor.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
        fig_labor.add_vline(x=portfolio_labor_median, line_dash="dash", line_color="#9BA8B8",
                            annotation_text=f"Median {portfolio_labor_median:.0%}")
        st.plotly_chart(fig_labor, use_container_width=True)

st.divider()

# ── Savings tracker ─────────────────────────────────────────────

st.subheader("Savings Tracker")

captured = savings[savings["status"] == "Captured"]["annual_savings_aed"].sum()
pipeline = savings[savings["status"] == "Pipeline"]["annual_savings_aed"].sum()
identified = savings[savings["status"] == "Identified"]["annual_savings_aed"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Captured", fmt_currency(captured, ccy))
c2.metric("Pipeline", fmt_currency(pipeline, ccy))
c3.metric("Identified", fmt_currency(identified, ccy))

status_summary = savings.groupby("status")["annual_savings_aed"].sum().reset_index()
fig_sav = px.bar(
    status_summary, x="status", y="annual_savings_aed",
    color="status",
    color_discrete_map={"Captured": GREEN, "Pipeline": AMBER, "Identified": "#9BA8B8"},
    labels={"annual_savings_aed": "Annual Savings (AED)", "status": ""},
)
fig_sav.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False)
fig_sav.update_yaxes(gridcolor="#2A3950")
st.plotly_chart(fig_sav, use_container_width=True)

st.dataframe(
    savings[["savings_id", "category", "description", "annual_savings_aed", "status"]].rename(
        columns={"savings_id": "ID", "category": "Category", "description": "Description",
                 "annual_savings_aed": "Annual Savings (AED)", "status": "Status"}
    ),
    use_container_width=True, hide_index=True,
)

st.divider()

# ── Currency exposure ───────────────────────────────────────────

st.subheader("Currency Exposure")
scoped_venues = venues[venues["venue_id"].isin(venue_ids)]
ccy_rev = summary.merge(
    scoped_venues[["venue_id", "local_currency"]], on="venue_id", how="left"
).groupby("local_currency")["revenue_aed"].sum().reset_index()

if not ccy_rev.empty:
    fig_ccy = px.pie(
        ccy_rev, values="revenue_aed", names="local_currency",
        color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C", "#9BA8B8",
                                 "#7B8FA1", "#4A5568", "#E8D5B7", "#A67C52", "#6B4226", "#3D2914"],
        hole=0.45,
    )
    fig_ccy.update_layout(**PLOTLY_LAYOUT, height=300)
    fig_ccy.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_ccy, use_container_width=True)
