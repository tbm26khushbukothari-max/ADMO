import streamlit as st
from lib.data import load_venues, get_scope_venue_ids, FX_AED_TO_USD

# ── Colour palette ──────────────────────────────────────────────

NAVY = "#0F1A2E"
GOLD = "#C9A961"
OFF_WHITE = "#F7F4ED"
RED = "#C84B31"
AMBER = "#D89B3F"
GREEN = "#5A7D3C"
CARD_BG = "#1A2940"

BRAND_COLORS = {
    "Nammos": "#C9A961",
    "Em Sherif": "#C84B31",
    "CE LA VI": "#5A7D3C",
    "AlphaMind": "#D89B3F",
    "Other ADMO": "#7B8FA1",
}

VERTICAL_COLORS = {
    "Nammos H&R": "#C9A961",
    "Em Sherif": "#C84B31",
    "CÉ LA VI": "#5A7D3C",
    "AlphaMind": "#D89B3F",
    "New Ventures": "#7B8FA1",
}

SEVERITY_COLORS = {"Red": RED, "Amber": AMBER, "Green": GREEN}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=OFF_WHITE, size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)

# ── Formatting helpers ──────────────────────────────────────────

def fmt_aed(value, prefix="AED "):
    if abs(value) >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{prefix}{value / 1_000:.0f}K"
    return f"{prefix}{value:,.0f}"


def fmt_usd(value):
    return fmt_aed(value, prefix="$")


def fmt_currency(value, currency="AED"):
    if currency == "USD":
        return fmt_usd(value * FX_AED_TO_USD)
    return fmt_aed(value)


# ── CSS ─────────────────────────────────────────────────────────

def metric_card_css():
    return """
    <style>
    [data-testid="stMetric"] {
        background-color: #1A2940;
        border: 1px solid #2A3950;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] { color: #9BA8B8; }
    [data-testid="stMetricValue"] { color: #C9A961; }
    div[data-testid="stMetricDelta"] > div { font-size: 0.85rem; }
    @media (max-width: 768px) {
        [data-testid="column"] { min-width: 45% !important; flex: 1 1 45% !important; }
    }
    </style>
    """


# ── Sidebar ─────────────────────────────────────────────────────

def render_sidebar():
    venues = load_venues()

    with st.sidebar:
        st.markdown(f"<h3 style='color:{GOLD}; margin-bottom:0;'>ADMO Scope</h3>", unsafe_allow_html=True)
        st.caption("Group ▸ Vertical ▸ Brand ▸ Venue")

        verticals = ["All"] + sorted(venues["vertical"].dropna().unique().tolist())
        sel_vert = st.selectbox("Vertical", verticals, key="scope_vertical")

        if sel_vert != "All":
            brand_options = ["All"] + sorted(
                venues[venues["vertical"] == sel_vert]["concept_brand"].dropna().unique().tolist()
            )
        else:
            brand_options = ["All"] + sorted(venues["concept_brand"].dropna().unique().tolist())
        sel_brand = st.selectbox("Brand", brand_options, key="scope_brand")

        if sel_brand != "All":
            venue_options = ["All"] + sorted(
                venues[venues["concept_brand"] == sel_brand]["sub_brand"].dropna().unique().tolist()
            )
        elif sel_vert != "All":
            venue_options = ["All"] + sorted(
                venues[venues["vertical"] == sel_vert]["sub_brand"].dropna().unique().tolist()
            )
        else:
            venue_options = ["All"] + sorted(venues["sub_brand"].dropna().unique().tolist())
        sel_venue = st.selectbox("Venue", venue_options, key="scope_venue")

        st.divider()
        currency = st.radio("Currency", ["AED", "USD"], horizontal=True, key="scope_currency")

    return {
        "vertical": sel_vert,
        "brand": sel_brand,
        "venue": sel_venue,
        "currency": currency,
    }


# ── Reusable components ─────────────────────────────────────────

def page_header(title, subtitle=""):
    st.markdown(f"<h1 style='color:{GOLD};'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def empty_state(message="No data for the selected scope."):
    st.info(message)


def alert_card(severity, headline, description="", venue_name="", owner="", status=""):
    sev_color = SEVERITY_COLORS.get(severity, OFF_WHITE)
    parts = [
        f"<strong style='color:{sev_color};'>{severity}</strong> &nbsp;|&nbsp; "
        f"<strong style='color:{OFF_WHITE};'>{headline}</strong>",
    ]
    detail = []
    if venue_name:
        detail.append(venue_name)
    if description:
        detail.append(description)
    if detail:
        parts.append(f"<br/><span style='color:#9BA8B8; font-size:0.85rem;'>{' — '.join(detail)}</span>")
    if owner or status:
        meta = []
        if owner:
            meta.append(f"Owner: {owner}")
        if status:
            meta.append(f"Status: {status}")
        parts.append(f"<br/><span style='color:#6B7A8D; font-size:0.8rem;'>{' | '.join(meta)}</span>")
    st.markdown(
        f"<div style='background:{CARD_BG}; border-left:4px solid {sev_color}; "
        f"border-radius:6px; padding:12px 16px; margin-bottom:10px;'>{''.join(parts)}</div>",
        unsafe_allow_html=True,
    )


def scope_desc(scope):
    parts = []
    if scope.get("vertical") and scope["vertical"] != "All":
        parts.append(scope["vertical"])
    if scope.get("brand") and scope["brand"] != "All":
        parts.append(scope["brand"])
    if scope.get("venue") and scope["venue"] != "All":
        parts.append(scope["venue"])
    return " ▸ ".join(parts) if parts else "Group (All)"
