import streamlit as st

st.set_page_config(page_title="Verticals | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, CARD_BG,
    PLOTLY_LAYOUT, VERTICAL_COLORS,
)
from lib.data import (
    load_monthly_summary, load_venues, load_daily_ops, load_brand_health,
    load_savings, get_scope_venue_ids, filter_by_scope, compute_growth_pct,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Verticals", f"Scope: {scope_desc(scope)}")

summary = load_monthly_summary()
health = load_brand_health()
savings = load_savings()
daily_ops = load_daily_ops()

verticals = sorted(venues["vertical"].dropna().unique())

# ── Vertical scorecards ─────────────────────────────────────────

st.subheader("Vertical Scorecards")
cols = st.columns(min(len(verticals), 5))

for i, vert in enumerate(verticals):
    vert_venues = set(venues[venues["vertical"] == vert]["venue_id"])
    vert_summary = summary[summary["venue_id"].isin(vert_venues)]
    rev = vert_summary["revenue_aed"].sum()
    covers = vert_summary["covers"].sum()
    growth = compute_growth_pct(summary, vert_venues)
    latest_health = health[health["brand"].isin(
        venues[venues["vertical"] == vert]["brand"].unique()
    )]
    if not latest_health.empty:
        h_score = latest_health.groupby("month")["health_score"].mean().iloc[-1]
    else:
        h_score = 0
    n_venues = len(vert_venues)

    with cols[i % len(cols)]:
        st.markdown(
            f"<div style='background:{CARD_BG}; border-top:3px solid "
            f"{VERTICAL_COLORS.get(vert, GOLD)}; border-radius:8px; padding:16px; "
            f"margin-bottom:12px;'>"
            f"<strong style='color:{VERTICAL_COLORS.get(vert, GOLD)};'>{vert}</strong><br/>"
            f"<span style='color:{OFF_WHITE};'>Revenue: {fmt_currency(rev, ccy)}</span><br/>"
            f"<span style='color:{OFF_WHITE};'>Covers: {covers:,.0f}</span><br/>"
            f"<span style='color:{OFF_WHITE};'>Growth: {growth:+.1f}%</span><br/>"
            f"<span style='color:{OFF_WHITE};'>Health: {h_score:.0f}/100</span><br/>"
            f"<span style='color:#9BA8B8;'>{n_venues} venues</span></div>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Vertical comparison ─────────────────────────────────────────

st.subheader("Vertical Comparison")
col_l, col_r = st.columns(2)

with col_l:
    vert_rev = summary.groupby("vertical")["revenue_aed"].sum().reset_index()
    if ccy == "USD":
        vert_rev["revenue_aed"] *= 1 / 3.67
    fig = px.bar(
        vert_rev.sort_values("revenue_aed", ascending=True),
        x="revenue_aed", y="vertical", orientation="h",
        color="vertical", color_discrete_map=VERTICAL_COLORS,
        labels={"revenue_aed": f"Revenue ({ccy})", "vertical": ""},
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False, title="Revenue")
    fig.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    ops = daily_ops.merge(venues[["venue_id", "vertical"]], on="venue_id", how="left")
    nps_by_vert = ops.groupby("vertical")["nps_score"].mean().reset_index()
    fig2 = px.bar(
        nps_by_vert.sort_values("nps_score", ascending=True),
        x="nps_score", y="vertical", orientation="h",
        color="vertical", color_discrete_map=VERTICAL_COLORS,
        labels={"nps_score": "Avg NPS", "vertical": ""},
    )
    fig2.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False, title="NPS")
    fig2.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Savings model per vertical ──────────────────────────────────

st.subheader("Savings by Vertical")

savings_rows = []
for _, s in savings.iterrows():
    if s["venue_ids"] == "all":
        for vert in verticals:
            savings_rows.append({"vertical": vert, "status": s["status"],
                                 "savings": s["annual_savings_aed"] / len(verticals)})
    else:
        sv_ids = str(s["venue_ids"]).split(";")
        matched_verts = venues[venues["venue_id"].isin(sv_ids)]["vertical"].unique()
        for vert in matched_verts:
            savings_rows.append({"vertical": vert, "status": s["status"],
                                 "savings": s["annual_savings_aed"] / max(1, len(matched_verts))})

if savings_rows:
    sdf = pd.DataFrame(savings_rows)
    sdf_agg = sdf.groupby(["vertical", "status"])["savings"].sum().reset_index()
    fig3 = px.bar(
        sdf_agg, x="vertical", y="savings", color="status",
        barmode="stack",
        color_discrete_map={"Captured": "#5A7D3C", "Pipeline": "#D89B3F", "Identified": "#9BA8B8"},
        labels={"savings": "Annual Savings (AED)", "vertical": "", "status": "Status"},
    )
    fig3.update_layout(**PLOTLY_LAYOUT, height=320)
    fig3.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig3, use_container_width=True)
