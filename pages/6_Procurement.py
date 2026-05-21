import streamlit as st

st.set_page_config(page_title="Procurement | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, AMBER, GREEN, CARD_BG,
    PLOTLY_LAYOUT,
)
from lib.data import (
    load_venues, load_vendors, load_venue_vendor_map, load_savings,
    get_scope_venue_ids, filter_by_scope,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Procurement", f"Scope: {scope_desc(scope)}")

vendors = load_vendors()
vvm = load_venue_vendor_map()
savings = load_savings()

# Filter vendor map to scoped venues
scoped_vvm = vvm[vvm["venue_id"].isin(venue_ids)]

if scoped_vvm.empty:
    empty_state()
    st.stop()

scoped_vendor_ids = set(scoped_vvm["vendor_id"])
scoped_vendors = vendors[vendors["vendor_id"].isin(scoped_vendor_ids)]

# ── Vendor health matrix ───────────────────────────────────────

st.subheader("Vendor Health Matrix")

if scoped_vendors.empty:
    empty_state("No vendor data.")
else:
    fig_scatter = px.scatter(
        scoped_vendors,
        x="on_time_delivery_pct", y="quality_score",
        color="risk_flag",
        color_discrete_map={"Low": GREEN, "Medium": AMBER, "High": RED},
        size=[12] * len(scoped_vendors),
        hover_name="vendor_name",
        hover_data=["category", "signature_flag"],
        labels={
            "on_time_delivery_pct": "On-Time Delivery %",
            "quality_score": "Quality Score",
            "risk_flag": "Risk",
        },
    )
    fig_scatter.update_layout(**PLOTLY_LAYOUT, height=400)
    fig_scatter.update_xaxes(gridcolor="#2A3950", tickformat=".0%")
    fig_scatter.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ── Signature vs commodity split ───────────────────────────────

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Signature vs Commodity")
    sig_counts = scoped_vendors["signature_flag"].value_counts().reset_index()
    sig_counts.columns = ["Type", "Count"]
    sig_counts["Type"] = sig_counts["Type"].map({"Yes": "Signature", "No": "Commodity"})
    fig_sig = px.pie(
        sig_counts, values="Count", names="Type",
        color_discrete_sequence=[GOLD, "#4A5568"], hole=0.45,
    )
    fig_sig.update_layout(**PLOTLY_LAYOUT, height=280)
    fig_sig.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_sig, use_container_width=True)

with col_r:
    st.subheader("Vendors by Category")
    cat_counts = scoped_vendors["category"].value_counts().head(8).reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig_cat = px.bar(
        cat_counts, x="Count", y="Category", orientation="h",
        color_discrete_sequence=[GOLD],
        labels={"Count": "Vendors", "Category": ""},
    )
    fig_cat.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False)
    fig_cat.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_cat, use_container_width=True)

st.divider()

# ── Blast-radius view ──────────────────────────────────────────

st.subheader("Blast Radius — Vendor Dependency")

vendor_options = sorted(scoped_vendors["vendor_name"].tolist())
if vendor_options:
    selected_vendor = st.selectbox("Select a vendor", vendor_options)
    sel_vendor_id = vendors[vendors["vendor_name"] == selected_vendor]["vendor_id"].iloc[0]

    dependent_venues = vvm[vvm["vendor_id"] == sel_vendor_id]["venue_id"].unique()
    dep_in_scope = [v for v in dependent_venues if v in venue_ids]

    dep_display = venues[venues["venue_id"].isin(dep_in_scope)][
        ["sub_brand", "city", "country", "vertical"]
    ].rename(columns={
        "sub_brand": "Venue", "city": "City", "country": "Country", "vertical": "Vertical",
    })

    vendor_info = vendors[vendors["vendor_id"] == sel_vendor_id].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Affected Venues", str(len(dep_in_scope)))
    c2.metric("Category", vendor_info["category"])
    c3.metric("OTD %", f"{vendor_info['on_time_delivery_pct']:.0%}")
    c4.metric("Quality", f"{vendor_info['quality_score']:.1f}/5")

    if not dep_display.empty:
        st.dataframe(dep_display, use_container_width=True, hide_index=True)
    else:
        empty_state("No scoped venues depend on this vendor.")

st.divider()

# ── Consolidation opportunity ──────────────────────────────────

st.subheader("Consolidation Opportunities")

pipeline_savings = savings[savings["status"].isin(["Identified", "Pipeline"])]
if pipeline_savings.empty:
    empty_state("No pipeline / identified savings.")
else:
    display_sav = pipeline_savings[[
        "savings_id", "category", "description", "annual_savings_aed", "status"
    ]].rename(columns={
        "savings_id": "ID", "category": "Category", "description": "Description",
        "annual_savings_aed": "Annual Savings (AED)", "status": "Status",
    })
    st.dataframe(display_sav.sort_values("Annual Savings (AED)", ascending=False),
                 use_container_width=True, hide_index=True)

    total_pipeline = pipeline_savings["annual_savings_aed"].sum()
    st.markdown(
        f"<div style='background:{CARD_BG}; border:1px solid {GOLD}44; border-radius:8px; "
        f"padding:16px; text-align:center; margin-top:8px;'>"
        f"<span style='color:#9BA8B8;'>Total Pipeline + Identified</span><br/>"
        f"<span style='color:{GOLD}; font-size:1.5rem; font-weight:bold;'>"
        f"{fmt_currency(total_pipeline, ccy)}</span></div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Concentration risk ─────────────────────────────────────────

st.subheader("Concentration Risk — Vendors per Venue")

vendor_per_venue = scoped_vvm.groupby("venue_id")["vendor_id"].nunique().reset_index()
vendor_per_venue.columns = ["venue_id", "vendor_count"]
vendor_per_venue = vendor_per_venue.merge(
    venues[["venue_id", "sub_brand"]], on="venue_id", how="left"
)

sig_vendor_ids = set(vendors[vendors["signature_flag"] == "Yes"]["vendor_id"])
sig_per_venue = scoped_vvm[scoped_vvm["vendor_id"].isin(sig_vendor_ids)].groupby(
    "venue_id"
)["vendor_id"].nunique().reset_index()
sig_per_venue.columns = ["venue_id", "sig_vendor_count"]
vendor_per_venue = vendor_per_venue.merge(sig_per_venue, on="venue_id", how="left")
vendor_per_venue["sig_vendor_count"] = vendor_per_venue["sig_vendor_count"].fillna(0).astype(int)

fig_conc = go.Figure()
fig_conc.add_trace(go.Bar(
    x=vendor_per_venue.sort_values("vendor_count")["sub_brand"],
    y=vendor_per_venue.sort_values("vendor_count")["vendor_count"],
    name="Total Vendors", marker_color=GOLD,
))
fig_conc.add_trace(go.Bar(
    x=vendor_per_venue.sort_values("vendor_count")["sub_brand"],
    y=vendor_per_venue.sort_values("vendor_count")["sig_vendor_count"],
    name="Signature Vendors", marker_color="#5A7D3C",
))
fig_conc.update_layout(**PLOTLY_LAYOUT, height=380, barmode="group",
                        legend=dict(orientation="h", y=1.1))
fig_conc.update_yaxes(gridcolor="#2A3950", title_text="Vendor Count")
fig_conc.update_xaxes(gridcolor="#2A3950")
st.plotly_chart(fig_conc, use_container_width=True)

low_sig = vendor_per_venue[vendor_per_venue["sig_vendor_count"] < 3]
if not low_sig.empty:
    st.markdown(
        f"<div style='background:{CARD_BG}; border-left:4px solid {AMBER}; "
        f"border-radius:6px; padding:12px 16px;'>"
        f"<strong style='color:{AMBER};'>⚠ {len(low_sig)} venue(s) have fewer than 3 signature vendors</strong>"
        f"<br/><span style='color:#9BA8B8;'>"
        + ", ".join(low_sig["sub_brand"].tolist())
        + "</span></div>",
        unsafe_allow_html=True,
    )
