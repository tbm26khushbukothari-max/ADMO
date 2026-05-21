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
BORDER = "#2A3950"
MUTED = "#9BA8B8"
DIM = "#6B7A8D"

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
    font=dict(color=OFF_WHITE, family="DM Sans, Inter, sans-serif", size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor=CARD_BG, font_color=OFF_WHITE, bordercolor=GOLD),
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


def fmt_delta(current, previous):
    """Return (delta_str, is_positive) for period-over-period."""
    if previous == 0:
        return "—", True
    pct = (current - previous) / abs(previous) * 100
    return f"{pct:+.1f}%", pct >= 0


# ── Global CSS ──────────────────────────────────────────────────

def metric_card_css():
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

    /* ── KPI metric cards ── */
    [data-testid="stMetric"] {{
        background: linear-gradient(135deg, {CARD_BG} 0%, #162236 100%);
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 14px 18px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(201,169,97,0.12);
        border-color: {GOLD}66;
    }}
    [data-testid="stMetricLabel"] {{ color: {MUTED}; font-size: 0.82rem; letter-spacing: 0.03em; }}
    [data-testid="stMetricValue"] {{ color: {GOLD}; font-weight: 600; }}
    div[data-testid="stMetricDelta"] > div {{ font-size: 0.82rem; }}

    /* ── Tabs ── */
    button[data-baseweb="tab"] {{
        color: {MUTED} !important;
        font-weight: 500;
        border-radius: 6px 6px 0 0;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {GOLD} !important;
        border-bottom: 2px solid {GOLD};
    }}

    /* ── Tables ── */
    [data-testid="stDataFrame"] th {{
        background-color: {CARD_BG} !important;
        color: {GOLD} !important;
        font-weight: 600;
    }}

    /* ── Sidebar polish ── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0D1625 0%, {NAVY} 100%);
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label {{
        color: {MUTED};
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}

    /* ── Divider subtler ── */
    hr {{ border-color: {BORDER} !important; opacity: 0.4; }}

    /* ── Mobile stacking ── */
    @media (max-width: 768px) {{
        [data-testid="column"] {{ min-width: 45% !important; flex: 1 1 45% !important; }}
    }}

    /* ── Expander ── */
    details[data-testid="stExpander"] summary {{
        color: {GOLD};
        font-weight: 500;
    }}

    /* ── Download button ── */
    [data-testid="stDownloadButton"] button {{
        background: transparent !important;
        border: 1px solid {BORDER} !important;
        color: {MUTED} !important;
        font-size: 0.8rem;
    }}
    [data-testid="stDownloadButton"] button:hover {{
        border-color: {GOLD} !important;
        color: {GOLD} !important;
    }}

    /* ── Navigation links in sidebar ── */
    [data-testid="stSidebarNav"] {{
        padding-top: 0;
    }}
    [data-testid="stSidebarNav"] a {{
        color: {OFF_WHITE} !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        border-radius: 6px;
        display: block;
        transition: all 0.15s ease;
    }}
    [data-testid="stSidebarNav"] a:hover {{
        background: rgba(201,169,97,0.1) !important;
        color: {GOLD} !important;
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background: rgba(201,169,97,0.15) !important;
        color: {GOLD} !important;
        border-left: 3px solid {GOLD};
        font-weight: 600 !important;
    }}
    [data-testid="stSidebarNav"] span {{
        font-size: 0.92rem !important;
    }}

    /* ── Hide deploy / hamburger ── */
    #MainMenu {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    footer {{ visibility: hidden; }}
    </style>
    """


# ── ADMO Logo (inline SVG) ─────────────────────────────────────

def admo_logo_svg(width=180):
    """Render the ADMO wordmark as inline SVG."""
    return (
        f'<svg width="{width}" viewBox="0 0 360 80" xmlns="http://www.w3.org/2000/svg">'
        '<defs><linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" style="stop-color:#E8D5A3"/>'
        '<stop offset="50%" style="stop-color:#C9A961"/>'
        '<stop offset="100%" style="stop-color:#A68B45"/>'
        '</linearGradient></defs>'
        '<text x="0" y="58" font-family="DM Sans, Georgia, serif" font-size="56"'
        ' font-weight="700" letter-spacing="12" fill="url(#goldGrad)">ADMO</text>'
        '<line x1="0" y1="72" x2="350" y2="72" stroke="#C9A961" stroke-width="1.5" opacity="0.5"/>'
        '</svg>'
    )


def render_hero():
    """Full landing hero with logo, tagline and live clock."""
    import datetime
    now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
    logo = admo_logo_svg(220)
    st.markdown(
f"""<div style="text-align:center; padding:28px 0 12px 0;">
{logo}
<p style="color:{MUTED}; font-size:1rem; margin:8px 0 2px 0; letter-spacing:0.12em;">LIFESTYLE HOLDING</p>
<p style="color:{DIM}; font-size:0.82rem; margin:0;">Executive Intelligence Platform &nbsp;&bull;&nbsp; {now}</p>
</div>""",
        unsafe_allow_html=True,
    )


# ── Sidebar ─────────────────────────────────────────────────────

def render_sidebar():
    venues = load_venues()

    with st.sidebar:
        # Logo in sidebar
        st.markdown(
            f"<div style='text-align:center; padding:8px 0 4px 0;'>{admo_logo_svg(130)}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='text-align:center; color:{DIM}; font-size:0.72rem; "
            f"letter-spacing:0.12em; margin:0 0 16px 0;'>LIFESTYLE HOLDING</p>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div style='background:{CARD_BG}; border-radius:8px; padding:10px 14px; "
            f"border-left:3px solid {GOLD}; margin-bottom:16px;'>"
            f"<span style='color:{GOLD}; font-weight:600; font-size:0.85rem;'>Scope Filter</span>"
            f"<br/><span style='color:{DIM}; font-size:0.72rem;'>Group ▸ Vertical ▸ Brand ▸ Venue</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

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

        # Scope summary badge
        scope_dict = {
            "vertical": sel_vert,
            "brand": sel_brand,
            "venue": sel_venue,
            "currency": currency,
        }
        desc = scope_desc(scope_dict)
        n_venues = len(get_scope_venue_ids(venues, scope_dict))
        st.markdown(
            f"<div style='background:rgba(201,169,97,0.08); border-radius:6px; padding:8px 12px; "
            f"margin-top:8px; text-align:center;'>"
            f"<span style='color:{GOLD}; font-size:0.82rem; font-weight:500;'>{desc}</span><br/>"
            f"<span style='color:{DIM}; font-size:0.72rem;'>{n_venues} venue(s) selected</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    return scope_dict


# ── Reusable components ─────────────────────────────────────────

def page_header(title, subtitle=""):
    st.markdown(
        f"<h1 style='color:{GOLD}; font-weight:700; margin-bottom:0; font-family:DM Sans, serif;'>"
        f"{title}</h1>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.caption(subtitle)


def empty_state(message="No data for the selected scope."):
    st.info(message)


def section_header(title, description=""):
    """Styled section header within a page — used inside tabs or sections."""
    html = (
        f"<div style='margin:8px 0 16px 0;'>"
        f"<span style='color:{GOLD}; font-size:1.15rem; font-weight:600;'>{title}</span>"
    )
    if description:
        html += f"<br/><span style='color:{DIM}; font-size:0.8rem;'>{description}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def kpi_card(label, value, delta=None, delta_good=True, border_color=GOLD, icon=""):
    """Rich HTML KPI card with optional delta and icon."""
    delta_html = ""
    if delta is not None:
        delta_color = GREEN if delta_good else RED
        delta_html = (
            f"<div style='color:{delta_color}; font-size:0.78rem; font-weight:500; "
            f"margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{delta}</div>"
        )
    icon_html = (
        f"<div style='font-size:1rem; line-height:1; margin-bottom:6px;'>{icon}</div>"
        if icon else ""
    )
    st.markdown(
        f"<div style='background:linear-gradient(135deg,{CARD_BG} 0%,#162236 100%); "
        f"border:1px solid {BORDER}; border-top:3px solid {border_color}; "
        f"border-radius:10px; padding:14px 16px; min-height:140px; "
        f"display:flex; flex-direction:column; justify-content:center; "
        f"transition:all 0.15s;'>"
        f"{icon_html}"
        f"<div style='color:{MUTED}; font-size:0.72rem; text-transform:uppercase; "
        f"letter-spacing:0.04em; margin-bottom:6px; line-height:1.3;'>{label}</div>"
        f"<div style='color:{GOLD}; font-size:1.35rem; font-weight:700; line-height:1.2; "
        f"white-space:nowrap;'>{value}</div>"
        f"{delta_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def alert_card(severity, headline, description="", venue_name="", owner="", status=""):
    sev_color = SEVERITY_COLORS.get(severity, OFF_WHITE)
    sev_icons = {"Red": "●", "Amber": "●", "Green": "●"}
    icon = sev_icons.get(severity, "●")
    parts = [
        f"<span style='color:{sev_color}; font-size:0.7rem;'>{icon}</span> &nbsp;"
        f"<strong style='color:{OFF_WHITE};'>{headline}</strong>",
    ]
    detail = []
    if venue_name:
        detail.append(venue_name)
    if description:
        detail.append(description)
    if detail:
        parts.append(
            f"<br/><span style='color:{MUTED}; font-size:0.82rem;'>"
            f"{'  —  '.join(detail)}</span>"
        )
    if owner or status:
        meta = []
        if owner:
            meta.append(f"Owner: {owner}")
        if status:
            meta.append(f"Status: {status}")
        parts.append(
            f"<br/><span style='color:{DIM}; font-size:0.75rem;'>{'  |  '.join(meta)}</span>"
        )
    st.markdown(
        f"<div style='background:{CARD_BG}; border-left:4px solid {sev_color}; "
        f"border-radius:6px; padding:12px 16px; margin-bottom:8px; "
        f"transition:all 0.15s;'>{''.join(parts)}</div>",
        unsafe_allow_html=True,
    )


def stat_callout(label, value, sub_text="", border_color=GOLD):
    """Big centered stat callout card."""
    sub_html = f"<br/><span style='color:{DIM}; font-size:0.82rem;'>{sub_text}</span>" if sub_text else ""
    st.markdown(
        f"<div style='background:{CARD_BG}; border:1px solid {border_color}44; "
        f"border-radius:10px; padding:24px; text-align:center;'>"
        f"<span style='color:{MUTED}; font-size:0.88rem;'>{label}</span><br/>"
        f"<span style='color:{GOLD}; font-size:2rem; font-weight:700;'>{value}</span>"
        f"{sub_html}</div>",
        unsafe_allow_html=True,
    )


def download_df(df, filename, label="Download CSV"):
    """Inline CSV download button."""
    csv = df.to_csv(index=False)
    st.download_button(label, csv, file_name=filename, mime="text/csv")


def insight_card(icon, title, body, color=GOLD):
    """Auto-generated insight card with icon, title and body text."""
    st.markdown(
        f"<div style='background:{CARD_BG}; border-left:3px solid {color}; "
        f"border-radius:6px; padding:10px 14px; margin-bottom:8px; font-size:0.85rem;'>"
        f"<strong style='color:{color};'>{icon} {title}</strong><br/>"
        f"<span style='color:{OFF_WHITE};'>{body}</span></div>",
        unsafe_allow_html=True,
    )


def rag_badge(label, status, detail=""):
    """Render a RAG (Red/Amber/Green) badge with label."""
    color_map = {"red": RED, "amber": AMBER, "green": GREEN}
    c = color_map.get(status.lower(), MUTED)
    detail_html = f"<br/><span style='color:{MUTED}; font-size:0.75rem;'>{detail}</span>" if detail else ""
    st.markdown(
        f"<div style='background:{CARD_BG}; border:1px solid {BORDER}; "
        f"border-radius:8px; padding:10px 14px; text-align:center;'>"
        f"<span style='color:{c}; font-size:1.4rem;'>●</span><br/>"
        f"<span style='color:{OFF_WHITE}; font-weight:600; font-size:0.88rem;'>{label}</span>"
        f"{detail_html}</div>",
        unsafe_allow_html=True,
    )


def persona_banner(title, persona, questions):
    """Show who this page is for and the key questions it answers."""
    qs_html = "".join(
        f"<span style='background:rgba(201,169,97,0.12); border:1px solid {GOLD}33; "
        f"border-radius:20px; padding:3px 12px; font-size:0.78rem; color:{GOLD}; "
        f"white-space:nowrap;'>{q}</span>"
        for q in questions
    )
    st.markdown(
        f"<div style='background:linear-gradient(135deg,{CARD_BG} 0%,#162236 100%); "
        f"border:1px solid {BORDER}; border-radius:10px; padding:16px 20px; margin-bottom:16px;'>"
        f"<div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;'>"
        f"<div>"
        f"<span style='color:{MUTED}; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em;'>DESIGNED FOR</span><br/>"
        f"<span style='color:{OFF_WHITE}; font-weight:600; font-size:1rem;'>{persona}</span>"
        f"</div>"
        f"</div>"
        f"<div style='display:flex; gap:8px; flex-wrap:wrap; margin-top:10px;'>{qs_html}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def target_vs_actual(label, actual, target, ccy="AED", fmt_fn=None):
    """Show a KPI with target comparison and variance."""
    if fmt_fn is None:
        fmt_fn = lambda v: fmt_currency(v, ccy)
    variance = ((actual - target) / target * 100) if target else 0
    v_color = GREEN if variance >= 0 else RED
    v_icon = "▲" if variance >= 0 else "▼"
    st.markdown(
        f"<div style='background:linear-gradient(135deg,{CARD_BG} 0%,#162236 100%); "
        f"border:1px solid {BORDER}; border-top:3px solid {GOLD}; "
        f"border-radius:10px; padding:14px 16px; min-height:140px; "
        f"display:flex; flex-direction:column; justify-content:center;'>"
        f"<div style='color:{MUTED}; font-size:0.72rem; text-transform:uppercase; "
        f"letter-spacing:0.04em; margin-bottom:6px; line-height:1.3;'>{label}</div>"
        f"<div style='color:{GOLD}; font-size:1.35rem; font-weight:700; "
        f"white-space:nowrap;'>{fmt_fn(actual)}</div>"
        f"<div style='display:flex; justify-content:space-between; align-items:center; "
        f"margin-top:6px; gap:4px;'>"
        f"<span style='color:{DIM}; font-size:0.72rem; white-space:nowrap;'>Target: {fmt_fn(target)}</span>"
        f"<span style='color:{v_color}; font-size:0.78rem; font-weight:600; "
        f"white-space:nowrap;'>{v_icon} {variance:+.1f}%</span>"
        f"</div></div>",
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
