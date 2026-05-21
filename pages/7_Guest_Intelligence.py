import streamlit as st

st.set_page_config(page_title="Guest Intelligence | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state, section_header,
    kpi_card, download_df, insight_card, persona_banner, stat_callout,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, RED, AMBER, GREEN, CARD_BG,
    BORDER, MUTED, DIM,
    PLOTLY_LAYOUT, VERTICAL_COLORS,
)
from lib.data import (
    load_venues, load_guests, load_transactions,
    get_scope_venue_ids, filter_by_scope,
    compute_cross_brand_affinity, compute_ltv_uplift, compute_repeat_guest_rate,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Guest Intelligence", f"Scope: {scope_desc(scope)}")

persona_banner(
    "Guest Intelligence",
    "CMO, VP Guest Experience, CRM Director, Loyalty Manager",
    ["Who are our guests?", "Are they coming back?", "What's the cross-brand overlap?",
     "Where do VIPs come from?", "What's the LTV of multi-brand guests?",
     "Do we have consent to market?"],
)

txn = load_transactions()
guests = load_guests()
scoped_txn = filter_by_scope(txn, venue_ids)

if scoped_txn.empty:
    empty_state()
    st.stop()

guest_ids_in_scope = set(scoped_txn["guest_id"].dropna().unique())
scoped_guests = guests[guests["guest_id"].isin(guest_ids_in_scope)]

if scoped_guests.empty:
    empty_state("No guest data for selected scope.")
    st.stop()

# ── Guest Summary KPIs ─────────────────────────────────────────

section_header("Guest Base Overview", "Key metrics for the guest population in scope")

total_guests = len(scoped_guests)
diamond_count = len(scoped_guests[scoped_guests["guest_tier"] == "Diamond"])
diamond_pct = diamond_count / total_guests * 100 if total_guests else 0
avg_ltv = scoped_guests["lifetime_spend_aed"].mean()
median_ltv = scoped_guests["lifetime_spend_aed"].median()
avg_visits = scoped_guests["total_visits"].mean()
multi_brand = scoped_guests[scoped_guests["brands_visited_count"] >= 2]
multi_brand_pct = len(multi_brand) / total_guests * 100 if total_guests else 0
repeat_rate = compute_repeat_guest_rate(txn, venue_ids)

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    kpi_card("Total Guests", f"{total_guests:,}", icon="👥", border_color=GOLD)
with c2:
    kpi_card("Diamond Guests", f"{diamond_count:,}",
             delta=f"{diamond_pct:.1f}% of base", icon="💎")
with c3:
    kpi_card("Avg LTV", fmt_currency(avg_ltv, ccy), icon="💰")
with c4:
    kpi_card("Repeat Rate", f"{repeat_rate:.1f}%", icon="🔄",
             border_color=GREEN if repeat_rate > 30 else (AMBER if repeat_rate > 15 else RED))
with c5:
    kpi_card("Multi-Brand", f"{multi_brand_pct:.1f}%",
             delta=f"{len(multi_brand):,} guests", icon="🔗",
             border_color=GOLD if multi_brand_pct > 25 else MUTED)
with c6:
    kpi_card("Avg Visits", f"{avg_visits:.1f}", icon="📊")

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

# ── Tabbed sections ────────────────────────────────────────────

tab_profile, tab_affinity, tab_ltv, tab_journey, tab_vip = st.tabs([
    "👤 Guest Profile", "🔗 Cross-Brand Affinity", "💰 LTV Analysis",
    "🗺 Guest Journey", "🏆 Top Guests"
])

# ── Tab 1: Guest Profile ──────────────────────────────────────

with tab_profile:
    col_l, col_r = st.columns(2)

    with col_l:
        section_header("Guest Tier Distribution", "Quality of the guest base")
        tier_dist = scoped_guests["guest_tier"].value_counts().reset_index()
        tier_dist.columns = ["Tier", "Count"]
        fig_tier = px.pie(
            tier_dist, values="Count", names="Tier",
            color_discrete_map={"Diamond": GOLD, "Platinum": "#9BA8B8",
                                "Gold": "#D89B3F", "Standard": "#4A5568"},
            hole=0.45,
        )
        fig_tier.update_layout(**PLOTLY_LAYOUT, height=320)
        fig_tier.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_tier, use_container_width=True)

    with col_r:
        section_header("Top 10 Nationalities", "Where are guests from?")
        nat_dist = scoped_guests["nationality"].value_counts().head(10).reset_index()
        nat_dist.columns = ["Nationality", "Count"]
        fig_nat = px.bar(
            nat_dist, x="Count", y="Nationality", orientation="h",
            color_discrete_sequence=[GOLD],
            labels={"Count": "Guests", "Nationality": ""},
        )
        fig_nat.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
        fig_nat.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_nat, use_container_width=True)

    st.divider()

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        section_header("Acquisition Channels", "How are we finding guests?")
        if "acquisition_channel" in scoped_guests.columns:
            acq_dist = scoped_guests["acquisition_channel"].value_counts().reset_index()
            acq_dist.columns = ["Channel", "Count"]
            fig_acq = px.pie(
                acq_dist, values="Count", names="Channel",
                color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C", "#9BA8B8",
                                         "#7B8FA1", "#4A5568"],
                hole=0.45,
            )
            fig_acq.update_layout(**PLOTLY_LAYOUT, height=280)
            fig_acq.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
            st.plotly_chart(fig_acq, use_container_width=True)

    with col_r2:
        section_header("Consent Breakdown", "Can we market to them?")
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

            # Consent insights
            full_consent = len(scoped_guests[scoped_guests["consent_status"] == "Full"])
            none_consent = len(scoped_guests[scoped_guests["consent_status"] == "None"])
            full_pct = full_consent / total_guests * 100 if total_guests else 0
            none_pct = none_consent / total_guests * 100 if total_guests else 0

            if none_pct > 30:
                insight_card("⚠", "Consent Gap",
                             f"{none_pct:.0f}% of guests have no marketing consent. "
                             f"CRM activation is limited for {none_consent:,} guests.",
                             RED)
            elif full_pct > 60:
                insight_card("✅", "Strong Consent Base",
                             f"{full_pct:.0f}% of guests have full consent — "
                             f"ready for personalised campaigns.", GREEN)
        else:
            empty_state("No consent data available.")

    # Visit frequency distribution
    st.divider()
    section_header("Visit Frequency", "How often do guests return?")
    visit_bins = pd.cut(scoped_guests["total_visits"], bins=[0, 1, 3, 10, 50, 1000],
                        labels=["1 visit", "2-3 visits", "4-10 visits", "11-50 visits", "50+ visits"])
    visit_dist = visit_bins.value_counts().sort_index().reset_index()
    visit_dist.columns = ["Frequency", "Count"]
    fig_freq = px.bar(visit_dist, x="Frequency", y="Count",
                      color_discrete_sequence=[GOLD])
    fig_freq.update_layout(**PLOTLY_LAYOUT, height=260, showlegend=False,
                            title="Guest Visit Frequency Distribution")
    fig_freq.update_yaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_freq, use_container_width=True)

    # Dietary flags
    if "dietary_flags" in scoped_guests.columns:
        st.divider()
        section_header("Dietary Preferences", "Key dietary needs across the guest base")
        dietary = scoped_guests["dietary_flags"].dropna()
        dietary = dietary[dietary != ""]
        if len(dietary) > 0:
            diet_counts = dietary.value_counts().head(8).reset_index()
            diet_counts.columns = ["Dietary Flag", "Count"]
            fig_diet = px.bar(diet_counts, x="Count", y="Dietary Flag", orientation="h",
                              color_discrete_sequence=[GOLD])
            fig_diet.update_layout(**PLOTLY_LAYOUT, height=220, showlegend=False)
            fig_diet.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_diet, use_container_width=True)

# ── Tab 2: Cross-Brand Affinity ──────────────────────────────

with tab_affinity:
    section_header("Cross-Brand Affinity Matrix",
                    "Guest overlap between verticals — where do multi-brand guests flow?")

    affinity = compute_cross_brand_affinity(txn, guests)
    if affinity.empty:
        empty_state("Not enough multi-brand guests for affinity analysis.")
    else:
        diag = affinity.values.diagonal().copy().astype(float)
        diag[diag == 0] = 1
        affinity_pct = affinity.div(diag, axis=0) * 100

        fig_hm = go.Figure(data=go.Heatmap(
            z=affinity_pct.values,
            x=affinity_pct.columns.tolist(),
            y=affinity_pct.index.tolist(),
            colorscale=[[0, "#0F1A2E"], [0.5, "#D89B3F"], [1, "#C9A961"]],
            text=affinity_pct.fillna(0).round(0).astype(int).astype(str).values,
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

        # Affinity insights
        st.divider()
        section_header("Key Insights", "What the data tells us about cross-brand behaviour")
        # Find strongest off-diagonal pair
        np.fill_diagonal(affinity_pct.values, 0)
        max_val = affinity_pct.max().max()
        if max_val > 0:
            max_pair = affinity_pct.stack().idxmax()
            insight_card("🔗", "Strongest Affinity",
                         f"{max_pair[0]} → {max_pair[1]}: {max_val:.0f}% overlap — "
                         f"these verticals share the most guests",
                         GOLD)

        stat_callout(
            "Cross-Brand Revenue Impact",
            f"{multi_brand_pct:.0f}% of guests visit 2+ brands",
            sub_text=f"These {len(multi_brand):,} guests represent a disproportionate share of total LTV"
        )

# ── Tab 3: LTV Analysis ──────────────────────────────────────

with tab_ltv:
    section_header("LTV Uplift — Multi-Brand vs Single-Brand",
                    "Do guests who visit multiple brands spend more?")

    multi_avg, single_avg, ratio = compute_ltv_uplift(scoped_guests)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Multi-Brand Avg LTV", fmt_currency(multi_avg, ccy), icon="💎", border_color=GOLD)
    with c2:
        kpi_card("Single-Brand Avg LTV", fmt_currency(single_avg, ccy), icon="👤")
    with c3:
        kpi_card("Uplift Ratio", f"{ratio:.1f}x" if ratio else "—", icon="📈",
                 border_color=GREEN if ratio > 2 else GOLD)
    with c4:
        lift_pct = (ratio - 1) * 100 if ratio > 0 else 0
        kpi_card("LTV Premium", f"+{lift_pct:.0f}%", icon="💰",
                 border_color=GREEN if lift_pct > 100 else GOLD)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

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

    # LTV distribution
    st.divider()
    section_header("LTV Distribution", "Spend concentration — a few whales or broad base?")

    col_l, col_r = st.columns(2)
    with col_l:
        # Histogram of LTV
        fig_hist = px.histogram(
            scoped_guests, x="lifetime_spend_aed", nbins=50,
            color_discrete_sequence=[GOLD],
            labels={"lifetime_spend_aed": "Lifetime Spend (AED)", "count": "Guests"},
        )
        fig_hist.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
                                title="LTV Distribution (All Guests)")
        fig_hist.update_yaxes(gridcolor="#2A3950")
        fig_hist.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_r:
        # LTV by tier
        tier_ltv = scoped_guests.groupby("guest_tier")["lifetime_spend_aed"].agg(["mean", "median", "count"]).reset_index()
        tier_ltv.columns = ["Tier", "Mean LTV", "Median LTV", "Count"]
        tier_order = {"Diamond": 0, "Platinum": 1, "Gold": 2, "Standard": 3}
        tier_ltv["order"] = tier_ltv["Tier"].map(tier_order)
        tier_ltv = tier_ltv.sort_values("order")
        fig_tier_ltv = go.Figure()
        fig_tier_ltv.add_trace(go.Bar(
            x=tier_ltv["Tier"], y=tier_ltv["Mean LTV"],
            name="Mean LTV", marker_color=GOLD,
        ))
        fig_tier_ltv.add_trace(go.Bar(
            x=tier_ltv["Tier"], y=tier_ltv["Median LTV"],
            name="Median LTV", marker_color="#4A5568",
        ))
        fig_tier_ltv.update_layout(**PLOTLY_LAYOUT, height=280, barmode="group",
                                    title="LTV by Guest Tier")
        fig_tier_ltv.update_layout(legend=dict(orientation="h", y=1.12))
        fig_tier_ltv.update_yaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_tier_ltv, use_container_width=True)

    # Revenue concentration
    sorted_guests = scoped_guests.sort_values("lifetime_spend_aed", ascending=False)
    top_10_pct = sorted_guests.head(max(1, len(sorted_guests)//10))["lifetime_spend_aed"].sum()
    total_ltv = sorted_guests["lifetime_spend_aed"].sum()
    top_10_share = top_10_pct / total_ltv * 100 if total_ltv else 0

    insight_card("📊", "Revenue Concentration",
                 f"Top 10% of guests ({len(sorted_guests)//10:,}) generate "
                 f"{top_10_share:.0f}% of lifetime value",
                 GOLD if top_10_share < 60 else AMBER)

# ── Tab 4: Guest Journey ──────────────────────────────────────

with tab_journey:
    section_header("Guest Journey — First Brand → Current Brand(s)",
                    "How do multi-brand guests move through the portfolio?")

    multi_guests = scoped_guests[scoped_guests["brands_visited_count"] >= 2]
    if multi_guests.empty or "first_seen_brand" not in multi_guests.columns:
        empty_state("Not enough multi-brand guests for journey analysis.")
    else:
        brand_to_vert = venues[["brand", "vertical"]].drop_duplicates().set_index("brand")["vertical"].to_dict()

        latest_txn = scoped_txn[scoped_txn["guest_id"].isin(multi_guests["guest_id"])].sort_values(
            "transaction_date"
        ).drop_duplicates("guest_id", keep="last")
        latest_txn = latest_txn.merge(venues[["venue_id", "vertical"]], on="venue_id", how="left")

        journey = multi_guests[["guest_id", "first_seen_brand"]].merge(
            latest_txn[["guest_id", "vertical"]], on="guest_id", how="inner"
        )
        journey["source"] = journey["first_seen_brand"].map(brand_to_vert).fillna(journey["first_seen_brand"])
        journey["target"] = journey["vertical"]

        flow = journey.groupby(["source", "target"]).size().reset_index(name="count")
        flow = flow[flow["count"] >= 2]

        if flow.empty:
            empty_state("Not enough journey data to display.")
        else:
            all_labels = sorted(set(flow["source"].tolist() + flow["target"].tolist()))
            label_to_idx = {l: i for i, l in enumerate(all_labels)}
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

            # Journey insights
            st.divider()
            section_header("Journey Insights")

            # Most common entry point
            entry_counts = journey["source"].value_counts()
            if not entry_counts.empty:
                top_entry = entry_counts.index[0]
                top_entry_pct = entry_counts.iloc[0] / len(journey) * 100
                insight_card("🚪", "Top Entry Point",
                             f"{top_entry} is where {top_entry_pct:.0f}% of multi-brand guests "
                             f"first enter the portfolio", GOLD)

            # Retention within same vertical
            same_vert = journey[journey["source"] == journey["target"]]
            retention_pct = len(same_vert) / len(journey) * 100 if len(journey) else 0
            insight_card("🔄", "Vertical Retention",
                         f"{retention_pct:.0f}% of multi-brand guests' latest visit is "
                         f"within the same vertical as their first",
                         GREEN if retention_pct < 50 else AMBER)

# ── Tab 5: Top Guests ─────────────────────────────────────────

with tab_vip:
    section_header("Top 25 Guests by Lifetime Value",
                    "The most valuable guests across the portfolio — VIP recognition targets")

    top_guests = scoped_guests.nlargest(25, "lifetime_spend_aed")

    # Summary
    top25_ltv = top_guests["lifetime_spend_aed"].sum()
    top25_share = top25_ltv / scoped_guests["lifetime_spend_aed"].sum() * 100 if scoped_guests["lifetime_spend_aed"].sum() else 0
    avg_top_visits = top_guests["total_visits"].mean()
    avg_top_brands = top_guests["brands_visited_count"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Top 25 Total LTV", fmt_currency(top25_ltv, ccy), icon="💎", border_color=GOLD)
    with c2:
        kpi_card("% of Total LTV", f"{top25_share:.1f}%", icon="📊")
    with c3:
        kpi_card("Avg Visits (Top 25)", f"{avg_top_visits:.0f}", icon="🔄")
    with c4:
        kpi_card("Avg Brands (Top 25)", f"{avg_top_brands:.1f}", icon="🔗")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Detailed table
    display_top = top_guests[
        ["guest_id", "guest_tier", "nationality", "lifetime_spend_aed",
         "brands_visited_count", "total_visits", "last_visit_date"]
    ].copy()
    display_top.columns = ["Guest ID", "Tier", "Nationality", "Lifetime Spend (AED)",
                            "Brands Visited", "Total Visits", "Last Visit"]
    display_top["Lifetime Spend (AED)"] = display_top["Lifetime Spend (AED)"].apply(
        lambda x: f"{x:,.0f}"
    )
    display_top["Last Visit"] = pd.to_datetime(display_top["Last Visit"]).dt.strftime("%d %b %Y")
    st.dataframe(display_top, use_container_width=True, hide_index=True)
    download_df(display_top, "admo_top_guests.csv", "📥 Download Top Guests")

    # VIP insights
    st.divider()
    section_header("VIP Insights")
    col_l, col_r = st.columns(2)

    with col_l:
        # Top nationalities among top 25
        vip_nat = top_guests["nationality"].value_counts().head(5).reset_index()
        vip_nat.columns = ["Nationality", "Count"]
        fig_vn = px.bar(vip_nat, x="Count", y="Nationality", orientation="h",
                        color_discrete_sequence=[GOLD])
        fig_vn.update_layout(**PLOTLY_LAYOUT, height=200, showlegend=False,
                              title="Top VIP Nationalities")
        fig_vn.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_vn, use_container_width=True)

    with col_r:
        # Top tiers among top 25
        vip_tier = top_guests["guest_tier"].value_counts().reset_index()
        vip_tier.columns = ["Tier", "Count"]
        fig_vt = px.pie(vip_tier, values="Count", names="Tier",
                        color_discrete_map={"Diamond": GOLD, "Platinum": "#9BA8B8",
                                            "Gold": "#D89B3F", "Standard": "#4A5568"},
                        hole=0.45)
        fig_vt.update_layout(**PLOTLY_LAYOUT, height=200, title="VIP Tier Mix")
        fig_vt.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
        st.plotly_chart(fig_vt, use_container_width=True)

    # Churn risk — VIPs not seen in 90+ days
    if "last_visit_date" in top_guests.columns:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=90)
        top_guests_dt = top_guests.copy()
        top_guests_dt["last_visit_date"] = pd.to_datetime(top_guests_dt["last_visit_date"])
        at_risk = top_guests_dt[top_guests_dt["last_visit_date"] < cutoff]
        if len(at_risk) > 0:
            insight_card("🚨", f"{len(at_risk)} VIP(s) at Churn Risk",
                         f"Haven't visited in 90+ days. Total LTV at risk: "
                         f"{fmt_currency(at_risk['lifetime_spend_aed'].sum(), ccy)}",
                         RED)
        else:
            insight_card("✅", "VIP Retention Strong",
                         "All top-25 guests have visited within the last 90 days.", GREEN)
