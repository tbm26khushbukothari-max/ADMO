import streamlit as st

st.set_page_config(
    page_title="ADMO Lifestyle Dashboard",
    page_icon="♦",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state, alert_card,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, CARD_BG,
    PLOTLY_LAYOUT, VERTICAL_COLORS, SEVERITY_COLORS,
)
from lib.data import (
    load_monthly_summary, load_venues, load_alerts, load_guests,
    load_transactions, get_scope_venue_ids, filter_by_scope,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Executive Overview", f"Scope: {scope_desc(scope)}")

summary = filter_by_scope(load_monthly_summary(), venue_ids)
alerts = filter_by_scope(load_alerts(), venue_ids)

if summary.empty:
    empty_state()
    st.stop()

# ── Pulse KPIs ──────────────────────────────────────────────────

total_rev = summary["revenue_aed"].sum()
total_covers = summary["covers"].sum()
avg_check = total_rev / total_covers if total_covers else 0
active_venues = summary["venue_id"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Portfolio Revenue", fmt_currency(total_rev, ccy))
c2.metric("Total Covers", f"{total_covers:,.0f}")
c3.metric("Avg Check / Cover", fmt_currency(avg_check, ccy))
c4.metric("Active Venues", str(active_venues))

st.divider()

# ── Revenue trend line (by vertical) ───────────────────────────

col_chart, col_alerts = st.columns([2, 1])

with col_chart:
    st.subheader("Monthly Revenue by Vertical")
    monthly = summary.groupby(["month", "vertical"])["revenue_aed"].sum().reset_index()
    if ccy == "USD":
        monthly["revenue_aed"] *= 1 / 3.67
    fig = px.area(
        monthly, x="month", y="revenue_aed", color="vertical",
        color_discrete_map=VERTICAL_COLORS,
        labels={"revenue_aed": f"Revenue ({ccy})", "month": "", "vertical": "Vertical"},
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=380)
    fig.update_yaxes(gridcolor="#2A3950", gridwidth=0.5)
    fig.update_xaxes(gridcolor="#2A3950", gridwidth=0.5)
    st.plotly_chart(fig, use_container_width=True)

# ── Exception ticker ────────────────────────────────────────────

with col_alerts:
    st.subheader("Exception Alerts")
    open_alerts = alerts[alerts["status"].isin(["Open", "Investigating", "Escalated"])]
    if open_alerts.empty:
        empty_state("No active alerts in scope.")
    else:
        for _, a in open_alerts.sort_values(
            "severity", key=lambda s: s.map({"Red": 0, "Amber": 1, "Green": 2})
        ).iterrows():
            vname = venues.loc[venues["venue_id"] == a["venue_id"], "sub_brand"].values
            alert_card(
                a["severity"], a["headline"],
                venue_name=vname[0] if len(vname) else a["venue_id"],
                owner=a["owner"], status=a["status"],
            )

st.divider()

# ── Revenue by vertical (bar) + Region breakdown ───────────────

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Revenue by Vertical")
    vert_rev = summary.groupby("vertical")["revenue_aed"].sum().sort_values(ascending=True).reset_index()
    if ccy == "USD":
        vert_rev["revenue_aed"] *= 1 / 3.67
    fig2 = px.bar(
        vert_rev, x="revenue_aed", y="vertical", orientation="h",
        color="vertical", color_discrete_map=VERTICAL_COLORS,
        labels={"revenue_aed": f"Revenue ({ccy})", "vertical": ""},
    )
    fig2.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
    fig2.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig2, use_container_width=True)

with col_r:
    st.subheader("Revenue by Region")
    region_rev = summary.groupby("region")["revenue_aed"].sum().sort_values(ascending=False).reset_index()
    if ccy == "USD":
        region_rev["revenue_aed"] *= 1 / 3.67
    fig3 = px.bar(
        region_rev, x="region", y="revenue_aed",
        color_discrete_sequence=[GOLD],
        labels={"revenue_aed": f"Revenue ({ccy})", "region": ""},
    )
    fig3.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
    fig3.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Cross-brand headline ───────────────────────────────────────

guests = load_guests()
multi = guests[guests["brands_visited_count"] >= 2]
multi_pct_base = len(multi) / len(guests) * 100 if len(guests) else 0
multi_ltv = multi["lifetime_spend_aed"].sum()
total_ltv = guests["lifetime_spend_aed"].sum()
multi_pct_rev = multi_ltv / total_ltv * 100 if total_ltv else 0

st.markdown(
    f"<div style='background:{CARD_BG}; border:1px solid {GOLD}44; border-radius:10px; "
    f"padding:24px; text-align:center;'>"
    f"<span style='color:#9BA8B8; font-size:1rem;'>Cross-Brand Intelligence</span><br/>"
    f"<span style='color:{GOLD}; font-size:2rem; font-weight:bold;'>"
    f"{multi_pct_base:.0f}% of guests visit 2+ brands → {multi_pct_rev:.0f}% of revenue"
    f"</span></div>",
    unsafe_allow_html=True,
)
