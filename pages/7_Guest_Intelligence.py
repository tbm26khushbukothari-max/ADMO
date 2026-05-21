import streamlit as st

st.set_page_config(page_title="Guest Intelligence | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, AMBER, GREEN, CARD_BG,
    PLOTLY_LAYOUT, VERTICAL_COLORS,
)
from lib.data import (
    load_venues, load_guests, load_transactions,
    get_scope_venue_ids, filter_by_scope,
    compute_cross_brand_affinity, compute_ltv_uplift,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Guest Intelligence", f"Scope: {scope_desc(scope)}")

txn = load_transactions()
guests = load_guests()
scoped_txn = filter_by_scope(txn, venue_ids)

if scoped_txn.empty:
    empty_state()
    st.stop()

# Identify guests in scope
guest_ids_in_scope = set(scoped_txn["guest_id"].dropna().unique())
scoped_guests = guests[guests["guest_id"].isin(guest_ids_in_scope)]

if scoped_guests.empty:
    empty_state("No guest data for selected scope.")
    st.stop()

# ── Cross-brand affinity matrix ────────────────────────────────

st.subheader("Cross-Brand Affinity Matrix")

affinity = compute_cross_brand_affinity(txn, guests)
if affinity.empty:
    empty_state("Not enough multi-brand guests for affinity analysis.")
else:
    # Normalise to percentages (row-wise)
    affinity_pct = affinity.div(affinity.values.diagonal(), axis=0) * 100

    fig_hm = go.Figure(data=go.Heatmap(
        z=affinity_pct.values,
        x=affinity_pct.columns.tolist(),
        y=affinity_pct.index.tolist(),
        colorscale=[[0, "#0F1A2E"], [0.5, "#D89B3F"], [1, "#C9A961"]],
        text=affinity_pct.round(0).astype(int).astype(str).values,
        texttemplate="%{text}%",
        textfont=dict(color=OFF_WHITE),
        hovertemplate="From %{y} → %{x}: %{z:.0f}%<extra></extra>",
    ))
    fig_hm.update_layout(
        **PLOTLY_LAYOUT, height=400,
        title="Guest Overlap % (row brand → column brand)",
        xaxis=dict(side="bottom"),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

st.divider()

# ── LTV uplift ─────────────────────────────────────────────────

st.subheader("LTV Uplift — Multi-Brand vs Single-Brand")

multi_avg, single_avg, ratio = compute_ltv_uplift(scoped_guests)

c1, c2, c3 = st.columns(3)
c1.metric("Multi-Brand Avg LTV", fmt_currency(multi_avg, ccy))
c2.metric("Single-Brand Avg LTV", fmt_currency(single_avg, ccy))
c3.metric("Uplift Ratio", f"{ratio:.1f}x" if ratio else "—")

fig_ltv = go.Figure()
fig_ltv.add_trace(go.Bar(
    x=["Single-Brand", "Multi-Brand"],
    y=[single_avg, multi_avg],
    marker_color=["#4A5568", GOLD],
    text=[fmt_currency(single_avg, ccy), fmt_currency(multi_avg, ccy)],
    textposition="outside",
    textfont=dict(color=OFF_WHITE),
))
fig_ltv.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False,
                       yaxis_title=f"Avg Lifetime Spend ({ccy})")
fig_ltv.update_yaxes(gridcolor="#2A3950")
st.plotly_chart(fig_ltv, use_container_width=True)

st.divider()

# ── Consent breakdown ──────────────────────────────────────────

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Consent Breakdown")
    if "consent_status" in scoped_guests.columns:
        consent_dist = scoped_guests["consent_status"].value_counts().reset_index()
        consent_dist.columns = ["Status", "Count"]
        fig_consent = px.pie(
            consent_dist, values="Count", names="Status",
            color_discrete_map={"Full": GREEN, "Partial": AMBER, "None": RED},
            hole=0.45,
        )
        fig_consent.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_consent.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_consent, use_container_width=True)
    else:
        empty_state("No consent data available.")

with col_r:
    st.subheader("Guest Tier Distribution")
    tier_dist = scoped_guests["guest_tier"].value_counts().reset_index()
    tier_dist.columns = ["Tier", "Count"]
    fig_tier = px.pie(
        tier_dist, values="Count", names="Tier",
        color_discrete_map={"Diamond": GOLD, "Platinum": "#9BA8B8",
                            "Gold": "#D89B3F", "Standard": "#4A5568"},
        hole=0.45,
    )
    fig_tier.update_layout(**PLOTLY_LAYOUT, height=280)
    fig_tier.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_tier, use_container_width=True)

st.divider()

# ── Guest journey Sankey ───────────────────────────────────────

st.subheader("Guest Journey — First Brand → Current Brand(s)")

multi_guests = scoped_guests[scoped_guests["brands_visited_count"] >= 2]
if multi_guests.empty or "first_seen_brand" not in multi_guests.columns:
    empty_state("Not enough multi-brand guests for journey analysis.")
else:
    # Map first brand to vertical
    brand_to_vert = venues[["brand", "vertical"]].drop_duplicates().set_index("brand")["vertical"].to_dict()

    # Get the most recent brand each multi-guest visited (from transactions)
    latest_txn = scoped_txn[scoped_txn["guest_id"].isin(multi_guests["guest_id"])].sort_values(
        "transaction_date"
    ).drop_duplicates("guest_id", keep="last")
    latest_txn = latest_txn.merge(venues[["venue_id", "vertical"]], on="venue_id", how="left")

    journey = multi_guests[["guest_id", "first_seen_brand"]].merge(
        latest_txn[["guest_id", "vertical"]], on="guest_id", how="inner"
    )
    journey["source"] = journey["first_seen_brand"].map(brand_to_vert).fillna(journey["first_seen_brand"])
    journey["target"] = journey["vertical"]

    # Build Sankey data
    flow = journey.groupby(["source", "target"]).size().reset_index(name="count")
    flow = flow[flow["count"] >= 2]  # filter noise

    if flow.empty:
        empty_state("Not enough journey data to display.")
    else:
        all_labels = sorted(set(flow["source"].tolist() + flow["target"].tolist()))
        label_to_idx = {l: i for i, l in enumerate(all_labels)}

        # Source nodes on left, target nodes on right
        src_labels = sorted(flow["source"].unique())
        tgt_labels = sorted(flow["target"].unique())

        # Assign colors
        node_colors = [VERTICAL_COLORS.get(l, GOLD) for l in all_labels]

        fig_sankey = go.Figure(go.Sankey(
            node=dict(
                label=all_labels,
                color=node_colors,
                pad=20, thickness=20,
                line=dict(color="#2A3950", width=1),
            ),
            link=dict(
                source=[label_to_idx[s] for s in flow["source"]],
                target=[label_to_idx[t] for t in flow["target"]],
                value=flow["count"].tolist(),
                color="rgba(201, 169, 97, 0.3)",
            ),
        ))
        fig_sankey.update_layout(**PLOTLY_LAYOUT, height=400,
                                  title="First Seen Brand → Latest Visit Vertical")
        st.plotly_chart(fig_sankey, use_container_width=True)

st.divider()

# ── Top guests table ───────────────────────────────────────────

st.subheader("Top 25 Guests by Lifetime Value")

top_guests = scoped_guests.nlargest(25, "lifetime_spend_aed")[
    ["guest_id", "guest_tier", "nationality", "lifetime_spend_aed",
     "brands_visited_count", "total_visits", "last_visit_date"]
].copy()
top_guests.columns = ["Guest ID", "Tier", "Nationality", "Lifetime Spend (AED)",
                       "Brands Visited", "Total Visits", "Last Visit"]
top_guests["Lifetime Spend (AED)"] = top_guests["Lifetime Spend (AED)"].apply(
    lambda x: f"{x:,.0f}"
)
st.dataframe(top_guests, use_container_width=True, hide_index=True)
