import streamlit as st

st.set_page_config(page_title="HR & Talent | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, AMBER, GREEN, CARD_BG,
    PLOTLY_LAYOUT,
)
from lib.data import (
    load_venues, load_headcount, load_succession_map, load_hiring,
    load_daily_ops, get_scope_venue_ids, filter_by_scope,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("HR & Talent", f"Scope: {scope_desc(scope)}")

headcount = filter_by_scope(load_headcount(), venue_ids)
succession = filter_by_scope(load_succession_map(), venue_ids)
hiring = filter_by_scope(load_hiring(), venue_ids)

if headcount.empty:
    empty_state()
    st.stop()

# ── Headcount summary ──────────────────────────────────────────

st.subheader("Headcount Summary")

latest_month = headcount["month"].max()
latest_hc = headcount[headcount["month"] == latest_month]
total_fte = latest_hc["headcount"].sum()
total_budgeted = latest_hc["budgeted_headcount"].sum()
fill_rate = total_fte / total_budgeted * 100 if total_budgeted else 0
open_roles = len(hiring[hiring["status"] == "Open"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total FTE", f"{total_fte:,.0f}")
c2.metric("Budgeted", f"{total_budgeted:,.0f}")
c3.metric("Fill Rate", f"{fill_rate:.1f}%")
c4.metric("Open Roles", str(open_roles))

st.divider()

# ── FTE by role category ───────────────────────────────────────

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("FTE by Role Category")
    role_hc = latest_hc.groupby("role_category").agg(
        actual=("headcount", "sum"),
        budgeted=("budgeted_headcount", "sum"),
    ).reset_index()

    fig_role = go.Figure()
    fig_role.add_trace(go.Bar(
        x=role_hc["role_category"], y=role_hc["actual"],
        name="Actual", marker_color=GOLD,
    ))
    fig_role.add_trace(go.Bar(
        x=role_hc["role_category"], y=role_hc["budgeted"],
        name="Budgeted", marker_color="#2A3950",
    ))
    fig_role.update_layout(**PLOTLY_LAYOUT, height=340, barmode="group")
    fig_role.update_layout(legend=dict(orientation="h", y=1.12))
    fig_role.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_role, use_container_width=True)

with col_r:
    st.subheader("Headcount Trend")
    monthly_hc = headcount.groupby("month")["headcount"].sum().reset_index()
    monthly_budget = headcount.groupby("month")["budgeted_headcount"].sum().reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly_hc["month"], y=monthly_hc["headcount"],
        mode="lines+markers", name="Actual",
        line=dict(color=GOLD, width=2),
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly_budget["month"], y=monthly_budget["budgeted_headcount"],
        mode="lines", name="Budgeted",
        line=dict(color="#9BA8B8", width=1.5, dash="dash"),
    ))
    fig_trend.update_layout(**PLOTLY_LAYOUT, height=340)
    fig_trend.update_layout(legend=dict(orientation="h", y=1.12))
    fig_trend.update_yaxes(gridcolor="#2A3950")
    fig_trend.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ── Open roles & critical flags ────────────────────────────────

st.subheader("Open Roles")
open_hiring = hiring[hiring["status"] == "Open"]

if open_hiring.empty:
    empty_state("No open roles in scope.")
else:
    critical = open_hiring[
        (open_hiring["criticality"] == "Critical") | (open_hiring["blocks_opening"] == "Yes")
    ]
    if not critical.empty:
        st.markdown(
            f"<div style='background:{CARD_BG}; border-left:4px solid {RED}; "
            f"border-radius:6px; padding:12px 16px; margin-bottom:12px;'>"
            f"<strong style='color:{RED};'>⚠ {len(critical)} Critical / Opening-Blocking Role(s)</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

    display_cols = ["position_id", "venue_id", "role", "seniority", "criticality",
                    "days_open", "blocks_opening"]
    display = open_hiring[display_cols].copy()
    display = display.merge(venues[["venue_id", "sub_brand"]], on="venue_id", how="left")
    display = display.rename(columns={
        "position_id": "ID", "sub_brand": "Venue", "role": "Role",
        "seniority": "Seniority", "criticality": "Criticality",
        "days_open": "Days Open", "blocks_opening": "Blocks Opening",
    })
    display = display.drop(columns=["venue_id"])
    st.dataframe(display.sort_values("Days Open", ascending=False),
                 use_container_width=True, hide_index=True)

st.divider()

# ── Time-to-fill ───────────────────────────────────────────────

st.subheader("Time-to-Fill Analysis")
filled = hiring[hiring["status"] == "Filled"]

if filled.empty:
    empty_state("No filled roles to analyse.")
else:
    avg_ttf = filled["days_open"].mean()
    median_ttf = filled["days_open"].median()

    c1, c2 = st.columns(2)
    c1.metric("Avg Time-to-Fill", f"{avg_ttf:.0f} days")
    c2.metric("Median Time-to-Fill", f"{median_ttf:.0f} days")

    ttf_by_seniority = filled.groupby("seniority")["days_open"].mean().reset_index()
    fig_ttf = px.bar(
        ttf_by_seniority.sort_values("days_open"),
        x="days_open", y="seniority", orientation="h",
        color_discrete_sequence=[GOLD],
        labels={"days_open": "Avg Days", "seniority": ""},
    )
    fig_ttf.update_layout(**PLOTLY_LAYOUT, height=250, showlegend=False,
                          title="Avg Time-to-Fill by Seniority")
    fig_ttf.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_ttf, use_container_width=True)

st.divider()

# ── Succession map ─────────────────────────────────────────────

st.subheader("Succession Map")

if succession.empty:
    empty_state("No succession data in scope.")
else:
    succ_display = succession.merge(
        venues[["venue_id", "sub_brand"]], on="venue_id", how="left"
    )
    succ_display = succ_display[["sub_brand", "role", "incumbent_name",
                                  "successor_name", "readiness", "risk_level"]].rename(
        columns={
            "sub_brand": "Venue", "role": "Role", "incumbent_name": "Incumbent",
            "successor_name": "Successor", "readiness": "Readiness",
            "risk_level": "Risk",
        }
    )

    def _color_readiness(val):
        if val == "Ready Now":
            return f"color: {GREEN};"
        elif val == "1-2 Years":
            return f"color: {AMBER};"
        return f"color: {RED};"

    def _color_risk(val):
        if val == "Low":
            return f"color: {GREEN};"
        elif val == "Medium":
            return f"color: {AMBER};"
        return f"color: {RED};"

    style_fn = getattr(succ_display.style, "map", None) or succ_display.style.applymap
    styled = style_fn(
        _color_readiness, subset=["Readiness"]
    )
    style_fn2 = getattr(styled, "map", None) or styled.applymap
    styled = style_fn2(
        _color_risk, subset=["Risk"]
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ── Labour cost vs benchmark ───────────────────────────────────

st.subheader("Labour Cost vs Portfolio Benchmark")
daily_ops = load_daily_ops()

if not daily_ops.empty:
    portfolio_median = daily_ops["labor_cost_pct"].median()
    scoped_ops = filter_by_scope(daily_ops, venue_ids)

    if not scoped_ops.empty:
        venue_labor = scoped_ops.merge(
            venues[["venue_id", "sub_brand"]], on="venue_id", how="left"
        ).groupby("sub_brand")["labor_cost_pct"].mean().reset_index()

        df_labor = venue_labor.sort_values("labor_cost_pct").copy()
        df_labor["flag"] = df_labor["labor_cost_pct"].apply(
            lambda x: "Above" if x > portfolio_median + 0.03 else "Normal"
        )
        fig_labor = px.bar(
            df_labor, x="labor_cost_pct", y="sub_brand", orientation="h",
            color="flag",
            color_discrete_map={"Above": RED, "Normal": GOLD},
            labels={"labor_cost_pct": "Labour Cost %", "sub_brand": ""},
        )
        fig_labor.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
        fig_labor.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
        fig_labor.add_vline(x=portfolio_median, line_dash="dash", line_color="#9BA8B8",
                            annotation_text=f"Median {portfolio_median:.0%}")
        st.plotly_chart(fig_labor, use_container_width=True)
