import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Guest Intelligence | ADMO", page_icon="♦", layout="wide")

from lib.style import (
    metric_card_css, fmt_aed, GOLD, OFF_WHITE, CARD_BG, RED, AMBER,
    PLOTLY_LAYOUT,
)
from lib.data_loader import (
    load_guests, load_vip_flags, load_interactions, load_venues,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
st.markdown(f"<h1 style='color:{GOLD};'>Guest Intelligence</h1>", unsafe_allow_html=True)
st.caption("Guest analytics, cross-brand behavior, Butler's Notebook, and VIP overlay")

guests = load_guests()
vip_flags = load_vip_flags()
interactions = load_interactions()
venues = load_venues()

# --- Top-line Guest KPIs ---
total_guests = len(guests)
multi_brand = guests[guests["brands_visited_count"] >= 2]
avg_ltv = guests["lifetime_spend_aed"].mean()
diamond_count = (guests["guest_tier"] == "Diamond").sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Guests", f"{total_guests:,}")
c2.metric("Multi-Brand Guests", f"{len(multi_brand):,}")
c3.metric("Avg LTV (AED)", fmt_aed(avg_ltv))
c4.metric("Diamond Tier", f"{diamond_count:,}")

st.divider()

# --- Tier Distribution & LTV ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Guest Tier Distribution")
    tier_order = ["Diamond", "Platinum", "Gold", "Standard"]
    tier_counts = guests["guest_tier"].value_counts().reindex(tier_order).reset_index()
    tier_counts.columns = ["Tier", "Count"]
    fig_tier = px.bar(
        tier_counts, x="Tier", y="Count",
        color="Tier",
        color_discrete_map={
            "Diamond": GOLD, "Platinum": "#9BA8B8",
            "Gold": "#D89B3F", "Standard": "#4A5568",
        },
        category_orders={"Tier": tier_order},
    )
    fig_tier.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
    fig_tier.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_tier, use_container_width=True)

with col_right:
    st.subheader("Average LTV by Tier")
    tier_ltv = guests.groupby("guest_tier")["lifetime_spend_aed"].mean().reindex(tier_order).reset_index()
    tier_ltv.columns = ["Tier", "Avg LTV"]
    fig_ltv = px.bar(
        tier_ltv, x="Tier", y="Avg LTV",
        color="Tier",
        color_discrete_map={
            "Diamond": GOLD, "Platinum": "#9BA8B8",
            "Gold": "#D89B3F", "Standard": "#4A5568",
        },
        category_orders={"Tier": tier_order},
    )
    fig_ltv.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
    fig_ltv.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_ltv, use_container_width=True)

st.divider()

# --- Nationality & Acquisition ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Guest Nationality (Top 10)")
    nat_counts = guests["nationality"].value_counts().head(10).reset_index()
    nat_counts.columns = ["Nationality", "Count"]
    fig_nat = px.bar(
        nat_counts.sort_values("Count"),
        x="Count", y="Nationality", orientation="h",
        color_discrete_sequence=[GOLD],
    )
    fig_nat.update_layout(**PLOTLY_LAYOUT, height=340, showlegend=False)
    fig_nat.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_nat, use_container_width=True)

with col2:
    st.subheader("Acquisition Channel")
    acq = guests["acquisition_channel"].value_counts().reset_index()
    acq.columns = ["Channel", "Count"]
    fig_acq = px.pie(
        acq, values="Count", names="Channel",
        color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C", "#9BA8B8"],
        hole=0.45,
    )
    fig_acq.update_layout(**PLOTLY_LAYOUT, height=340)
    fig_acq.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_acq, use_container_width=True)

st.divider()

# --- Consent Status ---
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Data Consent Status")
    consent = guests["consent_status"].value_counts().reset_index()
    consent.columns = ["Status", "Count"]
    fig_consent = px.pie(
        consent, values="Count", names="Status",
        color_discrete_map={"Full": "#5A7D3C", "Partial": "#D89B3F", "None": "#C84B31"},
        hole=0.45,
    )
    fig_consent.update_layout(**PLOTLY_LAYOUT, height=300)
    fig_consent.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_consent, use_container_width=True)

with col_r:
    st.subheader("First Seen Brand Distribution")
    first_brand = guests["first_seen_brand"].value_counts().reset_index()
    first_brand.columns = ["Brand", "Count"]
    from lib.style import BRAND_COLORS
    fig_fb = px.pie(
        first_brand, values="Count", names="Brand",
        color="Brand", color_discrete_map=BRAND_COLORS,
        hole=0.45,
    )
    fig_fb.update_layout(**PLOTLY_LAYOUT, height=300)
    fig_fb.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
    st.plotly_chart(fig_fb, use_container_width=True)

st.divider()

# --- Butler's Notebook (Guest Interactions) ---
st.subheader("Butler's Notebook — Recent Interactions")

int_with_venues = interactions.merge(venues[["venue_id", "sub_brand"]], on="venue_id", how="left")
int_types = ["All"] + sorted(interactions["interaction_type"].unique().tolist())
selected_type = st.selectbox("Filter by Type", int_types)

filtered = int_with_venues if selected_type == "All" else int_with_venues[int_with_venues["interaction_type"] == selected_type]
recent = filtered.nlargest(20, "interaction_date")

for _, row in recent.iterrows():
    type_color = {
        "Complaint resolved": AMBER, "Complaint unresolved": RED,
        "Compliment": "#5A7D3C", "Preference noted": GOLD,
        "Family note": "#9BA8B8", "Occasion": "#D89B3F",
    }.get(row["interaction_type"], OFF_WHITE)

    st.markdown(
        f"<div style='background:{CARD_BG}; border-left:4px solid {type_color}; "
        f"border-radius:6px; padding:10px 14px; margin-bottom:8px;'>"
        f"<strong style='color:{type_color};'>{row['interaction_type']}</strong> &nbsp;|&nbsp; "
        f"<span style='color:{GOLD};'>{row['guest_id']}</span> &nbsp;|&nbsp; "
        f"<span style='color:{OFF_WHITE};'>{row['sub_brand']}</span><br/>"
        f"<span style='color:#9BA8B8; font-size:0.85rem;'>{row['note']}</span><br/>"
        f"<span style='color:#6B7A8D; font-size:0.8rem;'>"
        f"{row['interaction_date'].strftime('%b %d, %Y')} &bull; Captured by: {row['captured_by']}</span></div>",
        unsafe_allow_html=True,
    )

st.divider()

# --- VIP Overlay ---
st.subheader("Group VIP Registry")
vip_detail = vip_flags.merge(
    guests[["guest_id", "guest_tier", "nationality", "lifetime_spend_aed", "total_visits"]],
    on="guest_id", how="left",
)
display = vip_detail[["guest_id", "category", "sensitivity_level", "guest_tier", "nationality", "lifetime_spend_aed", "total_visits"]].copy()
display.columns = ["Guest ID", "VIP Category", "Sensitivity", "Tier", "Nationality", "LTV (AED)", "Visits"]
display["LTV (AED)"] = display["LTV (AED)"].apply(lambda x: fmt_aed(x))
st.dataframe(display.sort_values("Visits", ascending=False), use_container_width=True, hide_index=True)
