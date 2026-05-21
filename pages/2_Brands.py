import streamlit as st

st.set_page_config(page_title="Brands | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, CARD_BG,
    PLOTLY_LAYOUT, VERTICAL_COLORS, BRAND_COLORS,
)
from lib.data import (
    load_monthly_summary, load_venues, load_guests, load_transactions,
    load_brand_health, get_scope_venue_ids, filter_by_scope, compute_growth_pct,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Brands", f"Scope: {scope_desc(scope)}")

summary = filter_by_scope(load_monthly_summary(), venue_ids)
guests = load_guests()
health = load_brand_health()

if summary.empty:
    empty_state()
    st.stop()

brands_in_scope = sorted(summary["concept_brand"].dropna().unique())

# ── Brand scorecards ────────────────────────────────────────────

st.subheader("Brand Scorecards")
n_cols = min(len(brands_in_scope), 4)
for row_start in range(0, len(brands_in_scope), n_cols):
    cols = st.columns(n_cols)
    for j, brand in enumerate(brands_in_scope[row_start:row_start + n_cols]):
        brand_vids = set(venues[venues["concept_brand"] == brand]["venue_id"])
        bdata = summary[summary["venue_id"].isin(brand_vids)]
        rev = bdata["revenue_aed"].sum()
        covers = bdata["covers"].sum()
        avg_chk = rev / covers if covers else 0
        growth = compute_growth_pct(load_monthly_summary(), brand_vids)

        with cols[j]:
            vert = venues[venues["concept_brand"] == brand]["vertical"].iloc[0] if len(
                venues[venues["concept_brand"] == brand]) else ""
            color = VERTICAL_COLORS.get(vert, GOLD)
            st.markdown(
                f"<div style='background:{CARD_BG}; border-top:3px solid {color}; "
                f"border-radius:8px; padding:16px; margin-bottom:12px;'>"
                f"<strong style='color:{color};'>{brand}</strong><br/>"
                f"<span style='color:{OFF_WHITE};'>Revenue: {fmt_currency(rev, ccy)}</span><br/>"
                f"<span style='color:{OFF_WHITE};'>Covers: {covers:,.0f}</span><br/>"
                f"<span style='color:{OFF_WHITE};'>Avg Check: {fmt_currency(avg_chk, ccy)}</span><br/>"
                f"<span style='color:{OFF_WHITE};'>Growth: {growth:+.1f}%</span></div>",
                unsafe_allow_html=True,
            )

st.divider()

# ── Brand health composite ──────────────────────────────────────

st.subheader("Brand Health Composite (0–100)")

brand_to_original = venues[["concept_brand", "brand"]].drop_duplicates()
original_brands_in_scope = brand_to_original[
    brand_to_original["concept_brand"].isin(brands_in_scope)
]["brand"].unique()

health_scoped = health[health["brand"].isin(original_brands_in_scope)]
if health_scoped.empty:
    empty_state("No health data for scope.")
else:
    latest_month = health_scoped["month"].max()
    latest = health_scoped[health_scoped["month"] == latest_month]

    cols = st.columns(min(len(latest), 5))
    for i, (_, row) in enumerate(latest.iterrows()):
        with cols[i % len(cols)]:
            color = "#5A7D3C" if row["health_score"] >= 75 else ("#D89B3F" if row["health_score"] >= 60 else "#C84B31")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=row["health_score"],
                gauge=dict(
                    axis=dict(range=[0, 100], tickcolor=OFF_WHITE),
                    bar=dict(color=color),
                    bgcolor="#1A2940",
                    bordercolor="#2A3950",
                ),
                title=dict(text=row["brand"], font=dict(color=GOLD, size=14)),
                number=dict(font=dict(color=OFF_WHITE)),
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font=dict(color=OFF_WHITE),
                height=200, margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                f"Rev: {row['revenue_score']:.0f} | Guest: {row['guest_score']:.0f} | "
                f"Ops: {row['ops_score']:.0f} | Talent: {row['talent_score']:.0f}"
            )

    st.divider()
    st.subheader("Health Score Trend")
    fig_trend = px.line(
        health_scoped, x="month", y="health_score", color="brand",
        color_discrete_map=BRAND_COLORS if len(original_brands_in_scope) <= 5 else {},
        labels={"health_score": "Health Score", "month": "", "brand": "Brand"},
    )
    fig_trend.update_layout(**PLOTLY_LAYOUT, height=300)
    fig_trend.update_yaxes(gridcolor="#2A3950")
    fig_trend.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ── Venue list ──────────────────────────────────────────────────

st.subheader("Venues in Scope")
venue_display = venues[venues["venue_id"].isin(venue_ids)][
    ["sub_brand", "vertical", "concept_brand", "city", "country", "venue_type", "seat_capacity"]
].copy()
venue_display.columns = ["Venue", "Vertical", "Brand", "City", "Country", "Type", "Capacity"]
st.dataframe(venue_display.sort_values("Venue"),
             use_container_width=True, hide_index=True)

st.divider()

# ── Guest mix ───────────────────────────────────────────────────

st.subheader("Guest Tier Mix")
txn = filter_by_scope(load_transactions(), venue_ids)
guest_ids_in_scope = set(txn["guest_id"].dropna().unique())
scoped_guests = guests[guests["guest_id"].isin(guest_ids_in_scope)]

if scoped_guests.empty:
    empty_state("No guest data.")
else:
    tier_dist = scoped_guests["guest_tier"].value_counts().reset_index()
    tier_dist.columns = ["Tier", "Count"]
    fig_tier = px.pie(
        tier_dist, values="Count", names="Tier",
        color_discrete_map={"Diamond": GOLD, "Platinum": "#9BA8B8", "Gold": "#D89B3F", "Standard": "#4A5568"},
        hole=0.45,
    )
    fig_tier.update_layout(**PLOTLY_LAYOUT, height=300)
    fig_tier.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_tier, use_container_width=True)

st.divider()

# ── Founder / operating context ─────────────────────────────────

BRAND_NOTES = {
    "Nammos H&R": "Founded in Mykonos (2003). Now the world's highest-grossing beach club. Expansion: London (2025), Maldives (2026).",
    "Em Sherif": "Founded in Beirut (2011) by Mireille Hayek. Signature: 30-course set menu. Expansion across GCC + London.",
    "CÉ LA VI": "Rooftop dining originating from Singapore's Marina Bay Sands (2010). Pan-Asian concept across 5 cities.",
    "AlphaMind": "Multi-concept portfolio: CLAP (Japanese), Babylon (Lebanese nightlife), Sucre (fire cooking), Bar Du Port (Riviera), Iris (lounge).",
    "New Ventures": "Emerging concepts: Nalu (lifestyle, Abu Dhabi) and Son of a Fish (Greek casual, Dubai Harbour). Both opened 2024-25.",
}

st.subheader("Operating Context")
for vert in sorted(set(venues[venues["venue_id"].isin(venue_ids)]["vertical"])):
    note = BRAND_NOTES.get(vert, "")
    if note:
        st.markdown(
            f"<div style='background:{CARD_BG}; border-left:3px solid "
            f"{VERTICAL_COLORS.get(vert, GOLD)}; border-radius:6px; padding:12px 16px; "
            f"margin-bottom:8px;'>"
            f"<strong style='color:{VERTICAL_COLORS.get(vert, GOLD)};'>{vert}</strong><br/>"
            f"<span style='color:{OFF_WHITE};'>{note}</span></div>",
            unsafe_allow_html=True,
        )
