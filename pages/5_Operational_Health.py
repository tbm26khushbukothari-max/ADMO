import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Operational Health | ADMO", page_icon="♦", layout="wide")

from lib.style import (
    metric_card_css, fmt_aed, GOLD, OFF_WHITE, RED, AMBER, GREEN, CARD_BG,
    PLOTLY_LAYOUT, SEVERITY_COLORS, BRAND_COLORS,
)
from lib.data_loader import (
    load_alerts, load_vendors, load_venue_vendor_map, load_venues,
    load_hiring, load_daily_ops,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
st.markdown(f"<h1 style='color:{GOLD};'>Operational Health</h1>", unsafe_allow_html=True)
st.caption("Alerts engine, vendor risk matrix, blast radius, hiring pipeline, and NPS trends")

alerts = load_alerts()
vendors = load_vendors()
vv_map = load_venue_vendor_map()
venues = load_venues()
hiring = load_hiring()
daily_ops = load_daily_ops()

# --- Alert Dashboard ---
st.subheader("Alert Dashboard")
open_alerts = alerts[alerts["status"].isin(["Open", "Investigating", "Escalated"])]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Active Alerts", str(open_alerts.shape[0]))
c2.metric("Red (Critical)", str((open_alerts["severity"] == "Red").sum()))
c3.metric("Amber (Warning)", str((open_alerts["severity"] == "Amber").sum()))
c4.metric("Green (Opportunity)", str((open_alerts["severity"] == "Green").sum()))

for _, a in open_alerts.sort_values("severity", key=lambda s: s.map({"Red": 0, "Amber": 1, "Green": 2})).iterrows():
    sev_color = SEVERITY_COLORS.get(a["severity"], OFF_WHITE)
    venue_name = venues.loc[venues["venue_id"] == a["venue_id"], "sub_brand"].values
    vname = venue_name[0] if len(venue_name) > 0 else a["venue_id"]
    st.markdown(
        f"<div style='background:{CARD_BG}; border-left:4px solid {sev_color}; "
        f"border-radius:6px; padding:12px 16px; margin-bottom:10px;'>"
        f"<strong style='color:{sev_color};'>{a['severity']}</strong> &nbsp;|&nbsp; "
        f"<strong style='color:{OFF_WHITE};'>{a['headline']}</strong><br/>"
        f"<span style='color:#9BA8B8; font-size:0.85rem;'>{vname} &mdash; {a['category']}</span><br/>"
        f"<span style='color:#6B7A8D; font-size:0.8rem;'>{a['description']}</span></div>",
        unsafe_allow_html=True,
    )

st.divider()

# --- Vendor Risk Matrix ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Vendor Risk Matrix")
    fig_vendor = px.scatter(
        vendors, x="on_time_delivery_pct", y="quality_score",
        color="risk_flag",
        color_discrete_map={"Low": GREEN, "Medium": AMBER, "High": RED},
        size=[12] * len(vendors),
        hover_name="vendor_name",
        hover_data=["category", "signature_flag"],
        labels={
            "on_time_delivery_pct": "On-Time Delivery %",
            "quality_score": "Quality Score",
            "risk_flag": "Risk",
        },
    )
    fig_vendor.update_layout(**PLOTLY_LAYOUT, height=400)
    fig_vendor.update_xaxes(gridcolor="#2A3950", range=[0.7, 1.02])
    fig_vendor.update_yaxes(gridcolor="#2A3950", range=[3.5, 5.2])
    fig_vendor.add_hline(y=4.0, line_dash="dash", line_color=AMBER, opacity=0.5)
    fig_vendor.add_vline(x=0.85, line_dash="dash", line_color=AMBER, opacity=0.5)
    st.plotly_chart(fig_vendor, use_container_width=True)

with col_right:
    st.subheader("Vendor Blast Radius — VEN-012")
    st.caption("Mykonos Local Producers Co. — signature produce vendor with declining quality")
    ven012_venues = vv_map[vv_map["vendor_id"] == "VEN-012"]["venue_id"].tolist()
    blast_venues = venues[venues["venue_id"].isin(ven012_venues)][["sub_brand", "city", "brand"]].copy()
    blast_venues.columns = ["Venue", "City", "Brand"]

    st.markdown(
        f"<div style='background:{RED}15; border:1px solid {RED}; border-radius:8px; "
        f"padding:16px; margin-bottom:12px;'>"
        f"<strong style='color:{RED};'>At Risk: {len(blast_venues)} venues depend on VEN-012</strong><br/>"
        f"<span style='color:{OFF_WHITE};'>Quality: 3.8/5.0 &bull; OTD: 78% &bull; "
        f"Action needed before May 2026 season</span></div>",
        unsafe_allow_html=True,
    )
    st.dataframe(blast_venues, use_container_width=True, hide_index=True)

    st.subheader("Signature vs Commodity Vendors")
    sig_count = (vendors["signature_flag"] == "Yes").sum()
    com_count = (vendors["signature_flag"] == "No").sum()
    fig_sig = px.pie(
        values=[sig_count, com_count], names=["Signature", "Commodity"],
        color_discrete_sequence=[GOLD, "#4A5568"], hole=0.5,
    )
    fig_sig.update_layout(**PLOTLY_LAYOUT, height=250)
    fig_sig.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_sig, use_container_width=True)

st.divider()

# --- Hiring Pipeline ---
st.subheader("Hiring Pipeline")
open_roles = hiring[hiring["status"] == "Open"]
filled_roles = hiring[hiring["status"] == "Filled"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Open Positions", str(open_roles.shape[0]))
c2.metric("Filled (18 mo)", str(filled_roles.shape[0]))
c3.metric("Avg Days to Fill", f"{filled_roles['days_open'].mean():.0f}")
c4.metric("Blocking Openings", str((open_roles["blocks_opening"] == "Yes").sum()))

col_l, col_r = st.columns(2)

with col_l:
    st.markdown("**Open Roles by Criticality**")
    crit = open_roles["criticality"].value_counts().reset_index()
    crit.columns = ["Criticality", "Count"]
    fig_crit = px.bar(
        crit, x="Criticality", y="Count",
        color="Criticality",
        color_discrete_map={"Critical": RED, "High": AMBER, "Medium": GOLD, "Low": "#4A5568"},
    )
    fig_crit.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False)
    fig_crit.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_crit, use_container_width=True)

with col_r:
    st.markdown("**Critical & Blocking Roles**")
    critical = open_roles[
        (open_roles["criticality"].isin(["Critical", "High"])) | (open_roles["blocks_opening"] == "Yes")
    ].merge(venues[["venue_id", "sub_brand"]], on="venue_id", how="left")
    if critical.empty:
        st.info("No critical blocking roles.")
    else:
        display = critical[["sub_brand", "role", "criticality", "days_open", "blocks_opening"]].copy()
        display.columns = ["Venue", "Role", "Criticality", "Days Open", "Blocks Opening"]
        st.dataframe(
            display.sort_values("Days Open", ascending=False),
            use_container_width=True, hide_index=True,
        )

st.divider()

# --- NPS Trends ---
st.subheader("NPS Trends by Venue")
ops_with_venue = daily_ops.merge(venues[["venue_id", "sub_brand", "brand"]], on="venue_id", how="left")
ops_with_venue["month"] = ops_with_venue["date"].dt.to_period("M").dt.to_timestamp()

brand_filter = st.selectbox("Filter by Brand", ["All"] + sorted(venues["brand"].unique().tolist()))
if brand_filter != "All":
    ops_with_venue = ops_with_venue[ops_with_venue["brand"] == brand_filter]

monthly_nps = ops_with_venue.groupby(["month", "sub_brand"])["nps_score"].mean().reset_index()

fig_nps = px.line(
    monthly_nps, x="month", y="nps_score", color="sub_brand",
    labels={"nps_score": "NPS Score", "month": "", "sub_brand": "Venue"},
)
fig_nps.update_layout(**PLOTLY_LAYOUT, height=400)
fig_nps.update_yaxes(gridcolor="#2A3950")
fig_nps.update_xaxes(gridcolor="#2A3950")
fig_nps.add_hline(y=70, line_dash="dash", line_color=GOLD, opacity=0.5,
                   annotation_text="Target NPS: 70", annotation_font_color=GOLD)
st.plotly_chart(fig_nps, use_container_width=True)

st.divider()

# --- Cost Benchmarking ---
st.subheader("Cost Benchmarking — Labour Cost % by Venue")
labour = ops_with_venue.groupby("sub_brand")["labor_cost_pct"].mean().sort_values(ascending=False).reset_index()
benchmark = labour["labor_cost_pct"].median()

fig_labor = px.bar(
    labour, x="labor_cost_pct", y="sub_brand", orientation="h",
    color=labour["labor_cost_pct"].apply(lambda x: "Above Benchmark" if x > benchmark + 0.03 else "Normal"),
    color_discrete_map={"Above Benchmark": RED, "Normal": GOLD},
    labels={"labor_cost_pct": "Labour Cost %", "sub_brand": ""},
)
fig_labor.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=True)
fig_labor.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
fig_labor.add_vline(x=benchmark, line_dash="dash", line_color="#9BA8B8", opacity=0.7,
                     annotation_text=f"Median: {benchmark:.0%}", annotation_font_color="#9BA8B8")
st.plotly_chart(fig_labor, use_container_width=True)
