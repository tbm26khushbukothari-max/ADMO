import streamlit as st

st.set_page_config(page_title="Brands | ADMO", page_icon="♦", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.ui import (
    render_sidebar, page_header, metric_card_css, empty_state, section_header,
    kpi_card, download_df, insight_card, persona_banner, target_vs_actual,
    fmt_currency, scope_desc, GOLD, OFF_WHITE, CARD_BG, BORDER, MUTED, DIM,
    RED, AMBER, GREEN,
    PLOTLY_LAYOUT, VERTICAL_COLORS, BRAND_COLORS,
)
from lib.data import (
    load_monthly_summary, load_venues, load_guests, load_transactions,
    load_brand_health, load_daily_ops, load_plan_targets, load_events,
    get_scope_venue_ids, filter_by_scope, compute_growth_pct,
    compute_budget_variance,
)

st.markdown(metric_card_css(), unsafe_allow_html=True)
scope = render_sidebar()
venues = load_venues()
venue_ids = get_scope_venue_ids(venues, scope)
ccy = scope.get("currency", "AED")

page_header("Brands", f"Scope: {scope_desc(scope)}")

persona_banner(
    "Brands",
    "Brand GMs, VP Strategy, Marketing Directors",
    ["How's my brand performing vs plan?", "Is brand health improving?",
     "What's the guest quality?", "Which venues are pulling weight?",
     "What's my competitive position?"],
)

summary = filter_by_scope(load_monthly_summary(), venue_ids)
guests = load_guests()
health = load_brand_health()
daily_ops = load_daily_ops()
targets = load_plan_targets()
events = load_events()

if summary.empty:
    empty_state()
    st.stop()

brands_in_scope = sorted(summary["concept_brand"].dropna().unique())

tab_scores, tab_health, tab_perf, tab_guests, tab_context = st.tabs([
    "📊 Brand Scorecards", "🏥 Brand Health", "📈 Performance Deep Dive",
    "👥 Guest Mix", "📖 Operating Context"
])

# ── Tab 1: Brand scorecards ────────────────────────────────────

with tab_scores:
    section_header("Brand Performance Cards",
                    "Revenue, covers, avg check, growth rate, satisfaction and events per brand")

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
            n_venues = len(brand_vids & venue_ids)
            avg_sat = bdata["avg_satisfaction"].mean() if not bdata.empty else 0

            # Operational metrics
            brand_ops = daily_ops[daily_ops["venue_id"].isin(brand_vids)]
            avg_nps = brand_ops["nps_score"].mean() if not brand_ops.empty else 0
            avg_occ = brand_ops["occupancy_pct"].mean() if not brand_ops.empty else 0
            avg_food = brand_ops["food_cost_pct"].mean() if not brand_ops.empty else 0

            # Events
            brand_events = events[events["venue_id"].isin(brand_vids)] if not events.empty else pd.DataFrame()
            events_rev = brand_events["total_revenue_aed"].sum() if not brand_events.empty else 0
            events_count = len(brand_events) if not brand_events.empty else 0

            # Budget
            _, tgt, var = compute_budget_variance(bdata, targets, brand_vids)

            with cols[j]:
                vert = venues[venues["concept_brand"] == brand]["vertical"].iloc[0] if len(
                    venues[venues["concept_brand"] == brand]) else ""
                color = VERTICAL_COLORS.get(vert, GOLD)
                g_color = GREEN if growth >= 0 else RED
                nps_color = GREEN if avg_nps >= 50 else (AMBER if avg_nps >= 30 else RED)
                sat_color = GREEN if avg_sat >= 8 else (AMBER if avg_sat >= 7 else RED)
                st.markdown(
                    f"<div style='background:linear-gradient(135deg,{CARD_BG} 0%,#162236 100%); "
                    f"border-top:3px solid {color}; border:1px solid {BORDER}; "
                    f"border-radius:10px; padding:18px; margin-bottom:12px;'>"
                    f"<div style='color:{color}; font-weight:700; font-size:1.05rem; "
                    f"margin-bottom:8px;'>{brand}</div>"
                    f"<div style='color:{MUTED}; font-size:0.72rem;'>REVENUE</div>"
                    f"<div style='color:{GOLD}; font-size:1.3rem; font-weight:700;'>"
                    f"{fmt_currency(rev, ccy)}</div>"
                    f"<div style='display:flex; justify-content:space-between; margin-top:8px;'>"
                    f"<span style='color:{MUTED}; font-size:0.78rem;'>Covers</span>"
                    f"<span style='color:{OFF_WHITE};'>{covers:,.0f}</span></div>"
                    f"<div style='display:flex; justify-content:space-between;'>"
                    f"<span style='color:{MUTED}; font-size:0.78rem;'>Avg Check</span>"
                    f"<span style='color:{OFF_WHITE};'>{fmt_currency(avg_chk, ccy)}</span></div>"
                    f"<div style='display:flex; justify-content:space-between;'>"
                    f"<span style='color:{MUTED}; font-size:0.78rem;'>Satisfaction</span>"
                    f"<span style='color:{sat_color};'>{avg_sat:.1f}/10</span></div>"
                    f"<div style='display:flex; justify-content:space-between;'>"
                    f"<span style='color:{MUTED}; font-size:0.78rem;'>NPS</span>"
                    f"<span style='color:{nps_color};'>{avg_nps:.0f}</span></div>"
                    f"<div style='display:flex; justify-content:space-between;'>"
                    f"<span style='color:{MUTED}; font-size:0.78rem;'>Occupancy</span>"
                    f"<span style='color:{OFF_WHITE};'>{avg_occ:.0%}</span></div>"
                    f"<div style='display:flex; justify-content:space-between;'>"
                    f"<span style='color:{MUTED}; font-size:0.78rem;'>Food Cost</span>"
                    f"<span style='color:{OFF_WHITE};'>{avg_food:.1%}</span></div>"
                    f"<div style='display:flex; justify-content:space-between;'>"
                    f"<span style='color:{MUTED}; font-size:0.78rem;'>Events Rev</span>"
                    f"<span style='color:{OFF_WHITE};'>{fmt_currency(events_rev, ccy)}</span></div>"
                    f"<div style='display:flex; justify-content:space-between;'>"
                    f"<span style='color:{MUTED}; font-size:0.78rem;'>Growth</span>"
                    f"<span style='color:{g_color}; font-weight:600;'>{growth:+.1f}%</span></div>"
                    f"<div style='color:{DIM}; font-size:0.72rem; margin-top:8px; "
                    f"text-align:center; border-top:1px solid {BORDER}; padding-top:6px;'>"
                    f"{n_venues} venue(s) &bull; {vert} &bull; Plan: {var:+.1f}%</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # Venue list
    st.divider()
    section_header("Venues in Scope")
    venue_display = venues[venues["venue_id"].isin(venue_ids)][
        ["sub_brand", "vertical", "concept_brand", "city", "country", "venue_type", "seat_capacity"]
    ].copy()
    venue_display.columns = ["Venue", "Vertical", "Brand", "City", "Country", "Type", "Capacity"]
    st.dataframe(venue_display.sort_values("Brand"), use_container_width=True, hide_index=True)
    download_df(venue_display, "admo_brand_venues.csv")

# ── Tab 2: Brand Health ───────────────────────────────────────

with tab_health:
    section_header("Brand Health Composite (0–100)",
                    "Weighted score: Revenue 30% | Guest 25% | Ops 25% | Talent 20%")

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
                h = row["health_score"]
                color = GREEN if h >= 75 else (AMBER if h >= 60 else RED)
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=h,
                    gauge=dict(
                        axis=dict(range=[0, 100], tickcolor=OFF_WHITE),
                        bar=dict(color=color),
                        bgcolor="#1A2940",
                        bordercolor="#2A3950",
                        steps=[
                            dict(range=[0, 60], color="rgba(200,75,49,0.15)"),
                            dict(range=[60, 75], color="rgba(216,155,63,0.15)"),
                            dict(range=[75, 100], color="rgba(90,125,60,0.15)"),
                        ],
                    ),
                    title=dict(text=row["brand"], font=dict(color=GOLD, size=14)),
                    number=dict(font=dict(color=OFF_WHITE)),
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", font=dict(color=OFF_WHITE),
                    height=200, margin=dict(l=20, r=20, t=50, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)
                # Sub-score breakdown
                st.markdown(
                    f"<div style='text-align:center; font-size:0.78rem; color:{MUTED};'>"
                    f"Rev <span style='color:{OFF_WHITE};'>{row['revenue_score']:.0f}</span> | "
                    f"Guest <span style='color:{OFF_WHITE};'>{row['guest_score']:.0f}</span> | "
                    f"Ops <span style='color:{OFF_WHITE};'>{row['ops_score']:.0f}</span> | "
                    f"Talent <span style='color:{OFF_WHITE};'>{row['talent_score']:.0f}</span></div>",
                    unsafe_allow_html=True,
                )

        # Health insights
        st.divider()
        best_brand = latest.loc[latest["health_score"].idxmax()]
        worst_brand = latest.loc[latest["health_score"].idxmin()]
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            insight_card("🏆", "Healthiest Brand",
                         f"{best_brand['brand']} at {best_brand['health_score']:.0f}/100", GREEN)
        with col_i2:
            worst_sub = "Ops" if worst_brand["ops_score"] == min(worst_brand["revenue_score"],
                                                                   worst_brand["guest_score"],
                                                                   worst_brand["ops_score"],
                                                                   worst_brand["talent_score"]) else "Revenue"
            insight_card("⚠", "Needs Focus",
                         f"{worst_brand['brand']} at {worst_brand['health_score']:.0f}/100 — weakest: {worst_sub}",
                         RED if worst_brand["health_score"] < 65 else AMBER)
        with col_i3:
            avg_health = latest["health_score"].mean()
            insight_card("📊", "Portfolio Avg",
                         f"Health score: {avg_health:.0f}/100",
                         GREEN if avg_health >= 75 else AMBER)

        st.divider()
        section_header("Health Score Trend", "Track trajectory over time — is the brand improving?")
        fig_trend = px.line(
            health_scoped, x="month", y="health_score", color="brand",
            color_discrete_map=BRAND_COLORS if len(original_brands_in_scope) <= 5 else {},
            labels={"health_score": "Health Score", "month": "", "brand": "Brand"},
        )
        fig_trend.update_layout(**PLOTLY_LAYOUT, height=300)
        fig_trend.update_yaxes(gridcolor="#2A3950", range=[40, 100])
        fig_trend.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_trend, use_container_width=True)

        # Sub-score trends
        st.divider()
        section_header("Sub-Score Trends", "Drill into what's driving health changes")
        sub_metric = st.radio("Sub-Score", ["revenue_score", "guest_score", "ops_score", "talent_score"],
                              format_func=lambda x: x.replace("_", " ").title(),
                              horizontal=True, key="health_sub")
        fig_sub = px.line(
            health_scoped, x="month", y=sub_metric, color="brand",
            color_discrete_map=BRAND_COLORS if len(original_brands_in_scope) <= 5 else {},
            labels={sub_metric: sub_metric.replace("_", " ").title(), "month": "", "brand": "Brand"},
        )
        fig_sub.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_sub.update_yaxes(gridcolor="#2A3950", range=[30, 100])
        fig_sub.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_sub, use_container_width=True)

# ── Tab 3: Performance Deep Dive ─────────────────────────────

with tab_perf:
    section_header("Brand Revenue Comparison",
                    "Monthly revenue by brand — spot divergences and seasonal patterns")

    brand_monthly = summary.groupby(["month", "concept_brand"])["revenue_aed"].sum().reset_index()
    if ccy == "USD":
        brand_monthly["revenue_aed"] *= 1 / 3.67
    fig_brand_rev = px.line(
        brand_monthly, x="month", y="revenue_aed", color="concept_brand",
        labels={"revenue_aed": f"Revenue ({ccy})", "month": "", "concept_brand": "Brand"},
    )
    fig_brand_rev.update_layout(**PLOTLY_LAYOUT, height=340)
    fig_brand_rev.update_yaxes(gridcolor="#2A3950")
    fig_brand_rev.update_xaxes(gridcolor="#2A3950")
    st.plotly_chart(fig_brand_rev, use_container_width=True)

    # Satisfaction trend by brand
    st.divider()
    section_header("Satisfaction Trend by Brand", "Are guests getting happier or more frustrated?")
    ops_with_brand = daily_ops.merge(
        venues[["venue_id", "concept_brand"]], on="venue_id", how="left"
    )
    ops_with_brand = ops_with_brand[ops_with_brand["venue_id"].isin(venue_ids)]
    if not ops_with_brand.empty:
        ops_with_brand["month"] = ops_with_brand["date"].dt.to_period("M").dt.to_timestamp()
        sat_brand = ops_with_brand.groupby(["month", "concept_brand"])["avg_satisfaction"].mean().reset_index()
        fig_sat = px.line(
            sat_brand, x="month", y="avg_satisfaction", color="concept_brand",
            labels={"avg_satisfaction": "Avg Satisfaction", "month": "", "concept_brand": "Brand"},
        )
        fig_sat.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_sat.update_yaxes(gridcolor="#2A3950", range=[6, 10])
        fig_sat.update_xaxes(gridcolor="#2A3950")
        st.plotly_chart(fig_sat, use_container_width=True)

    # Events revenue by brand
    st.divider()
    section_header("Events Revenue by Brand", "Which brands are driving private events?")
    scoped_events = events[events["venue_id"].isin(venue_ids)] if not events.empty else pd.DataFrame()
    if not scoped_events.empty:
        events_with_brand = scoped_events.merge(
            venues[["venue_id", "concept_brand"]], on="venue_id", how="left"
        )
        events_brand = events_with_brand.groupby("concept_brand").agg(
            events_count=("event_id", "count"),
            events_rev=("total_revenue_aed", "sum"),
            avg_per_head=("per_head_revenue_aed", "mean"),
        ).reset_index().sort_values("events_rev", ascending=False)

        col_l, col_r = st.columns(2)
        with col_l:
            fig_ev = px.bar(
                events_brand, x="events_rev", y="concept_brand", orientation="h",
                color_discrete_sequence=[GOLD],
                labels={"events_rev": f"Events Revenue ({ccy})", "concept_brand": ""},
            )
            fig_ev.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False)
            fig_ev.update_xaxes(gridcolor="#2A3950")
            st.plotly_chart(fig_ev, use_container_width=True)
        with col_r:
            for _, r in events_brand.iterrows():
                kpi_card(r["concept_brand"],
                         f"{r['events_count']} events | {fmt_currency(r['avg_per_head'], ccy)}/head",
                         icon="🎉")
                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

# ── Tab 4: Guest Mix ──────────────────────────────────────────

with tab_guests:
    section_header("Guest Tier Distribution",
                    "What's the quality of the guest base visiting these brands?")

    txn = filter_by_scope(load_transactions(), venue_ids)
    guest_ids_in_scope = set(txn["guest_id"].dropna().unique())
    scoped_guests = guests[guests["guest_id"].isin(guest_ids_in_scope)]

    if scoped_guests.empty:
        empty_state("No guest data.")
    else:
        # Summary KPIs
        total_guests = len(scoped_guests)
        diamond_pct = len(scoped_guests[scoped_guests["guest_tier"] == "Diamond"]) / total_guests * 100 if total_guests else 0
        avg_ltv = scoped_guests["lifetime_spend_aed"].mean()
        avg_visits = scoped_guests["total_visits"].mean()
        multi_brand_pct = len(scoped_guests[scoped_guests["brands_visited_count"] >= 2]) / total_guests * 100 if total_guests else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            kpi_card("Total Guests", f"{total_guests:,}", icon="👥")
        with c2:
            kpi_card("Diamond Tier", f"{diamond_pct:.1f}%", icon="💎",
                     border_color=GOLD if diamond_pct > 5 else MUTED)
        with c3:
            kpi_card("Avg LTV", fmt_currency(avg_ltv, ccy), icon="💰")
        with c4:
            kpi_card("Avg Visits", f"{avg_visits:.1f}", icon="🔄")
        with c5:
            kpi_card("Multi-Brand", f"{multi_brand_pct:.1f}%", icon="🔗",
                     border_color=GOLD if multi_brand_pct > 25 else MUTED)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        col_l, col_r = st.columns(2)
        with col_l:
            section_header("Tier Distribution")
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
            section_header("Nationality Mix (Top 10)")
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

        # Acquisition channels
        st.divider()
        section_header("Acquisition Channels", "How are guests discovering these brands?")
        if "acquisition_channel" in scoped_guests.columns:
            acq = scoped_guests["acquisition_channel"].value_counts().reset_index()
            acq.columns = ["Channel", "Count"]
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                fig_acq = px.pie(
                    acq, values="Count", names="Channel",
                    color_discrete_sequence=[GOLD, "#D89B3F", "#C84B31", "#5A7D3C", "#9BA8B8",
                                             "#7B8FA1", "#4A5568"],
                    hole=0.45,
                )
                fig_acq.update_layout(**PLOTLY_LAYOUT, height=280)
                fig_acq.update_traces(textinfo="percent+label", textfont_color=OFF_WHITE)
                st.plotly_chart(fig_acq, use_container_width=True)
            with col_a2:
                # Insights
                top_channel = acq.iloc[0]["Channel"] if len(acq) > 0 else "Unknown"
                top_pct = acq.iloc[0]["Count"] / total_guests * 100 if len(acq) > 0 else 0
                insight_card("📢", "Top Channel", f"{top_channel} brings {top_pct:.0f}% of guests", GOLD)

                diamond_guests = scoped_guests[scoped_guests["guest_tier"] == "Diamond"]
                if len(diamond_guests) > 0 and "acquisition_channel" in diamond_guests.columns:
                    top_diamond_ch = diamond_guests["acquisition_channel"].value_counts().index[0]
                    insight_card("💎", "Diamond Channel",
                                 f"Most Diamond guests come via {top_diamond_ch}", GOLD)

# ── Tab 5: Operating Context ──────────────────────────────────

with tab_context:
    section_header("Brand & Vertical Context",
                    "Origin stories, positioning and expansion plans")

    BRAND_NOTES = {
        "Nammos H&R": {
            "origin": "Founded in Mykonos (2003). Now the world's highest-grossing beach club.",
            "expansion": "London (2025), Maldives (2026)",
            "positioning": "Ultra-premium beach lifestyle",
            "key_metric": "Highest RevPASH in portfolio",
            "risk": "Seasonal exposure — Mykonos & Dubai peak windows",
        },
        "Em Sherif": {
            "origin": "Founded in Beirut (2011) by Mireille Hayek. Signature: 30-course set menu.",
            "expansion": "Expansion across GCC + London",
            "positioning": "Authentic Lebanese fine dining",
            "key_metric": "Highest guest satisfaction scores",
            "risk": "Menu complexity drives higher food cost %",
        },
        "CÉ LA VI": {
            "origin": "Rooftop dining from Singapore's Marina Bay Sands (2010).",
            "expansion": "Pan-Asian concept across 5 cities",
            "positioning": "Rooftop lifestyle dining",
            "key_metric": "Strongest geographic diversification",
            "risk": "Taipei venue underperforming — market fit review needed",
        },
        "AlphaMind": {
            "origin": "Multi-concept portfolio: CLAP, Babylon, Sucre, Bar Du Port, Iris.",
            "expansion": "Dubai-centric with selective international",
            "positioning": "Nightlife & experiential dining",
            "key_metric": "Highest cover count per venue",
            "risk": "Bar Du Port Yas ramp-up slower than planned; Iris cost pressure",
        },
        "New Ventures": {
            "origin": "Emerging concepts: Nalu (lifestyle, Abu Dhabi) and Son of a Fish (Greek casual).",
            "expansion": "Both opened 2024-25, early growth phase",
            "positioning": "Casual lifestyle & new market segments",
            "key_metric": "Fastest growth trajectory",
            "risk": "Still pre-breakeven — watching unit economics closely",
        },
    }

    for vert in sorted(set(venues[venues["venue_id"].isin(venue_ids)]["vertical"])):
        note = BRAND_NOTES.get(vert, {})
        if note:
            color = VERTICAL_COLORS.get(vert, GOLD)
            st.markdown(
                f"<div style='background:linear-gradient(135deg,{CARD_BG} 0%,#162236 100%); "
                f"border-left:4px solid {color}; border:1px solid {BORDER}; "
                f"border-radius:8px; padding:18px 20px; margin-bottom:12px;'>"
                f"<div style='color:{color}; font-weight:700; font-size:1.05rem; "
                f"margin-bottom:8px;'>{vert}</div>"
                f"<div style='color:{OFF_WHITE}; font-size:0.88rem; margin-bottom:6px;'>"
                f"{note.get('origin', '')}</div>"
                f"<div style='display:flex; gap:24px; margin-top:8px; flex-wrap:wrap;'>"
                f"<div><span style='color:{MUTED}; font-size:0.72rem; text-transform:uppercase;'>"
                f"Positioning</span><br/>"
                f"<span style='color:{OFF_WHITE}; font-size:0.82rem;'>"
                f"{note.get('positioning', '')}</span></div>"
                f"<div><span style='color:{MUTED}; font-size:0.72rem; text-transform:uppercase;'>"
                f"Expansion</span><br/>"
                f"<span style='color:{GOLD}; font-size:0.82rem;'>"
                f"{note.get('expansion', '')}</span></div>"
                f"<div><span style='color:{MUTED}; font-size:0.72rem; text-transform:uppercase;'>"
                f"Key Strength</span><br/>"
                f"<span style='color:{GREEN}; font-size:0.82rem;'>"
                f"{note.get('key_metric', '')}</span></div>"
                f"<div><span style='color:{MUTED}; font-size:0.72rem; text-transform:uppercase;'>"
                f"Key Risk</span><br/>"
                f"<span style='color:{AMBER}; font-size:0.82rem;'>"
                f"{note.get('risk', '')}</span></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
