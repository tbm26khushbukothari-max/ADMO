from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ── Vertical / concept-brand hierarchy ──────────────────────────

VERTICAL_MAP = {
    "Nammos": "Nammos H&R",
    "Em Sherif": "Em Sherif",
    "CE LA VI": "CÉ LA VI",
    "AlphaMind": "AlphaMind",
    "Other ADMO": "New Ventures",
}

CONCEPT_BRAND_MAP = {
    "V-001": "Nammos", "V-002": "Nammos", "V-003": "Nammos",
    "V-004": "Nammos", "V-005": "Nammos", "V-006": "Nammos",
    "V-007": "Em Sherif", "V-008": "Em Sherif", "V-009": "Em Sherif",
    "V-010": "Em Sherif", "V-011": "Em Sherif",
    "V-012": "Em Sherif Café", "V-013": "Em Sherif Café",
    "V-014": "Em Sherif Sea Café", "V-015": "Em Sherif Sea Café",
    "V-016": "CÉ LA VI", "V-017": "CÉ LA VI", "V-018": "CÉ LA VI",
    "V-019": "CÉ LA VI", "V-020": "CÉ LA VI",
    "V-021": "CLAP", "V-022": "CLAP", "V-023": "CLAP",
    "V-024": "Babylon", "V-025": "Sucre",
    "V-026": "Bar Du Port", "V-027": "Bar Du Port",
    "V-028": "Iris",
    "V-029": "Nalu", "V-030": "Son of a Fish",
}

FX_AED_TO_USD = 1 / 3.67

# ── Core loaders ────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_venues():
    df = pd.read_csv(DATA_DIR / "venue_master.csv")
    df["open_date"] = pd.to_datetime(df["open_date"])
    df["vertical"] = df["brand"].map(VERTICAL_MAP)
    df["concept_brand"] = df["venue_id"].map(CONCEPT_BRAND_MAP)
    return df


@st.cache_data(show_spinner=False)
def load_guests():
    df = pd.read_csv(DATA_DIR / "guest_master.csv")
    df["first_seen_date"] = pd.to_datetime(df["first_seen_date"])
    df["last_visit_date"] = pd.to_datetime(df["last_visit_date"])
    return df


@st.cache_data(show_spinner=False)
def load_transactions():
    df = pd.read_csv(DATA_DIR / "transactions.csv")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    return df


@st.cache_data(show_spinner=False)
def load_daily_ops():
    df = pd.read_csv(DATA_DIR / "daily_ops_metrics.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(show_spinner=False)
def load_vendors():
    return pd.read_csv(DATA_DIR / "vendor_master.csv")


@st.cache_data(show_spinner=False)
def load_venue_vendor_map():
    return pd.read_csv(DATA_DIR / "venue_vendor_map.csv")


@st.cache_data(show_spinner=False)
def load_events():
    df = pd.read_csv(DATA_DIR / "events_bookings.csv")
    df["event_date"] = pd.to_datetime(df["event_date"])
    return df


@st.cache_data(show_spinner=False)
def load_hiring():
    df = pd.read_csv(DATA_DIR / "hiring_pipeline.csv")
    df["open_date"] = pd.to_datetime(df["open_date"])
    return df


@st.cache_data(show_spinner=False)
def load_plan_targets():
    df = pd.read_csv(DATA_DIR / "plan_targets.csv")
    df["month"] = pd.to_datetime(df["month"])
    return df


@st.cache_data(show_spinner=False)
def load_reservations():
    df = pd.read_csv(DATA_DIR / "reservations_today.csv")
    df["reservation_date"] = pd.to_datetime(df["reservation_date"])
    return df


@st.cache_data(show_spinner=False)
def load_vip_flags():
    return pd.read_csv(DATA_DIR / "vip_flags.csv")


@st.cache_data(show_spinner=False)
def load_alerts():
    df = pd.read_csv(DATA_DIR / "alerts_feed.csv")
    df["raised_at"] = pd.to_datetime(df["raised_at"])
    return df


@st.cache_data(show_spinner=False)
def load_interactions():
    df = pd.read_csv(DATA_DIR / "guest_interactions.csv")
    df["interaction_date"] = pd.to_datetime(df["interaction_date"])
    return df


@st.cache_data(show_spinner=False)
def load_dishes():
    return pd.read_csv(DATA_DIR / "dish_master.csv")


@st.cache_data(show_spinner=False)
def load_fx_rates():
    return pd.read_csv(DATA_DIR / "fx_rates.csv")


@st.cache_data(show_spinner=False)
def load_brand_exposure():
    df = pd.read_csv(DATA_DIR / "brand_exposure_calendar.csv")
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    return df


# ── Pre-aggregated monthly summary ─────────────────────────────

@st.cache_data(show_spinner=False)
def load_monthly_summary():
    txn = load_transactions()
    txn["month"] = txn["transaction_date"].dt.to_period("M").dt.to_timestamp()
    summary = (
        txn.groupby(["month", "venue_id"])
        .agg(
            revenue_aed=("total_revenue_aed", "sum"),
            food_revenue_aed=("food_revenue_aed", "sum"),
            beverage_revenue_aed=("beverage_revenue_aed", "sum"),
            covers=("cover_count", "sum"),
            transactions=("transaction_id", "count"),
            avg_check=("avg_check_per_cover_aed", "mean"),
            avg_satisfaction=("guest_satisfaction_score", "mean"),
        )
        .reset_index()
    )
    venues = load_venues()[["venue_id", "brand", "sub_brand", "city", "region", "vertical", "concept_brand"]]
    return summary.merge(venues, on="venue_id", how="left")


# ── New CSV loaders (auto-generate on first access) ────────────

@st.cache_data(show_spinner=False)
def load_headcount():
    path = DATA_DIR / "headcount.csv"
    if not path.exists():
        _generate_headcount(path)
    df = pd.read_csv(path)
    df["month"] = pd.to_datetime(df["month"])
    return df


@st.cache_data(show_spinner=False)
def load_succession_map():
    path = DATA_DIR / "succession_map.csv"
    if not path.exists():
        _generate_succession_map(path)
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_brand_health():
    path = DATA_DIR / "brand_health.csv"
    if not path.exists():
        _generate_brand_health(path)
    df = pd.read_csv(path)
    df["month"] = pd.to_datetime(df["month"])
    return df


@st.cache_data(show_spinner=False)
def load_savings():
    path = DATA_DIR / "savings_tracking.csv"
    if not path.exists():
        _generate_savings(path)
    return pd.read_csv(path)


# ── CSV generators ──────────────────────────────────────────────

def _generate_headcount(path):
    import random
    random.seed(42)
    venues = pd.read_csv(DATA_DIR / "venue_master.csv")
    categories = ["Kitchen", "FOH", "Management", "Admin", "Events"]
    cat_shares = [0.30, 0.35, 0.12, 0.10, 0.13]
    rows = []
    for _, v in venues.iterrows():
        base_fte = max(20, int(v["seat_capacity"] * 0.6))
        open_d = pd.to_datetime(v["open_date"])
        for m in pd.date_range("2024-11-01", "2026-05-01", freq="MS"):
            if m < open_d:
                continue
            for cat, share in zip(categories, cat_shares):
                base = max(2, int(base_fte * share))
                actual = max(1, base + random.randint(-2, 2))
                budgeted = max(actual, int(base * 1.05))
                rows.append({
                    "venue_id": v["venue_id"],
                    "month": m.strftime("%Y-%m-%d"),
                    "role_category": cat,
                    "headcount": actual,
                    "budgeted_headcount": budgeted,
                })
    pd.DataFrame(rows).to_csv(path, index=False)


def _generate_succession_map(path):
    import random
    random.seed(42)
    venues = pd.read_csv(DATA_DIR / "venue_master.csv")
    key_roles = ["Executive Chef", "Restaurant Manager", "Head Sommelier",
                 "Events Manager", "Director of Operations"]
    first_names = ["Ahmed", "Sara", "Marco", "Yuki", "Priya", "Dimitris",
                   "Fatima", "Carlos", "Lina", "James", "Sofia", "Ravi",
                   "Elena", "Khalid", "Mei", "Pierre", "Amira", "Takeshi"]
    last_names = ["Al Maktoum", "Chen", "Papadopoulos", "Singh", "Rossi",
                  "Dubois", "Tanaka", "Martinez", "Al Rashid", "Kim",
                  "Petrova", "Costa", "Nair", "Yamamoto", "Haddad"]
    readiness_opts = ["Ready Now", "1-2 Years", "No Successor"]
    rows = []
    for _, v in venues.iterrows():
        n_roles = random.randint(1, 3)
        for role in random.sample(key_roles, min(n_roles, len(key_roles))):
            inc = f"{random.choice(first_names)} {random.choice(last_names)}"
            r = random.random()
            if v["venue_id"] == "V-006" and role == "Executive Chef":
                readiness = "No Successor"
                risk = "Critical"
                succ = ""
            elif r < 0.4:
                readiness = "Ready Now"
                risk = "Low"
                succ = f"{random.choice(first_names)} {random.choice(last_names)}"
            elif r < 0.75:
                readiness = "1-2 Years"
                risk = "Medium"
                succ = f"{random.choice(first_names)} {random.choice(last_names)}"
            else:
                readiness = "No Successor"
                risk = "High"
                succ = ""
            rows.append({
                "venue_id": v["venue_id"],
                "role": role,
                "incumbent_name": inc,
                "successor_name": succ,
                "readiness": readiness,
                "risk_level": risk,
            })
    pd.DataFrame(rows).to_csv(path, index=False)


def _generate_brand_health(path):
    import random
    random.seed(42)
    brands = ["Nammos", "Em Sherif", "CE LA VI", "AlphaMind", "Other ADMO"]
    base_scores = {
        "Nammos": {"revenue": 88, "guest": 85, "ops": 82, "talent": 80},
        "Em Sherif": {"revenue": 78, "guest": 80, "ops": 76, "talent": 74},
        "CE LA VI": {"revenue": 74, "guest": 72, "ops": 70, "talent": 72},
        "AlphaMind": {"revenue": 70, "guest": 68, "ops": 65, "talent": 66},
        "Other ADMO": {"revenue": 60, "guest": 62, "ops": 58, "talent": 55},
    }
    rows = []
    for brand in brands:
        bs = base_scores[brand]
        for m in pd.date_range("2024-11-01", "2026-05-01", freq="MS"):
            month_idx = (m.year - 2024) * 12 + m.month
            rev = max(30, min(100, bs["revenue"] + random.randint(-5, 5) + (month_idx - 12) * 0.3))
            guest = max(30, min(100, bs["guest"] + random.randint(-4, 4)))
            ops = max(30, min(100, bs["ops"] + random.randint(-4, 4)))
            talent = max(30, min(100, bs["talent"] + random.randint(-3, 3)))
            if brand == "AlphaMind" and m >= pd.Timestamp("2026-01-01"):
                ops -= 8
                rev -= 5
            if brand == "CE LA VI" and m >= pd.Timestamp("2025-12-01"):
                guest -= 6
            composite = rev * 0.30 + guest * 0.25 + ops * 0.25 + talent * 0.20
            rows.append({
                "brand": brand,
                "month": m.strftime("%Y-%m-%d"),
                "health_score": round(composite, 1),
                "revenue_score": round(rev, 1),
                "guest_score": round(guest, 1),
                "ops_score": round(ops, 1),
                "talent_score": round(talent, 1),
            })
    pd.DataFrame(rows).to_csv(path, index=False)


def _generate_savings(path):
    rows = [
        {"savings_id": "SAV-001", "category": "Consolidation", "vendor_id": "VEN-013",
         "venue_ids": "V-001;V-012;V-013;V-017;V-021;V-024;V-025;V-026;V-028",
         "description": "Linen services consolidation across Dubai venues",
         "annual_savings_aed": 1200000, "status": "Captured", "captured_date": "2025-06-01"},
        {"savings_id": "SAV-002", "category": "Renegotiation", "vendor_id": "VEN-020",
         "venue_ids": "all",
         "description": "Global coffee contract renegotiation — volume discount",
         "annual_savings_aed": 850000, "status": "Captured", "captured_date": "2025-03-15"},
        {"savings_id": "SAV-003", "category": "Consolidation", "vendor_id": "VEN-014",
         "venue_ids": "V-001;V-012;V-013;V-017;V-021;V-024;V-025;V-026;V-028;V-029;V-030",
         "description": "Cleaning services single-supplier model for UAE",
         "annual_savings_aed": 950000, "status": "Captured", "captured_date": "2025-09-01"},
        {"savings_id": "SAV-004", "category": "Renegotiation", "vendor_id": "VEN-021",
         "venue_ids": "all",
         "description": "POS platform group-wide license renewal",
         "annual_savings_aed": 1400000, "status": "Captured", "captured_date": "2025-01-10"},
        {"savings_id": "SAV-005", "category": "Consolidation", "vendor_id": "VEN-019",
         "venue_ids": "V-001;V-012;V-013;V-015;V-017;V-021;V-024;V-025;V-026;V-027;V-028",
         "description": "Beverage distribution consolidation UAE",
         "annual_savings_aed": 1100000, "status": "Captured", "captured_date": "2025-07-01"},
        {"savings_id": "SAV-006", "category": "Renegotiation", "vendor_id": "VEN-023",
         "venue_ids": "all",
         "description": "Group insurance umbrella policy",
         "annual_savings_aed": 2500000, "status": "Captured", "captured_date": "2025-04-01"},
        {"savings_id": "SAV-007", "category": "Substitution", "vendor_id": "VEN-012",
         "venue_ids": "V-002;V-004;V-005",
         "description": "Replace degrading Mykonos supplier — Aegean Premium as alternative",
         "annual_savings_aed": 350000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-008", "category": "Consolidation", "vendor_id": "VEN-016",
         "venue_ids": "V-003;V-008;V-020;V-022",
         "description": "London linen services merge with EU cleaning contract",
         "annual_savings_aed": 680000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-009", "category": "Renegotiation", "vendor_id": "VEN-010",
         "venue_ids": "V-001;V-002;V-003;V-004;V-005;V-016;V-017;V-020",
         "description": "Champagne volume rebate — 8-venue commitment",
         "annual_savings_aed": 1800000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-010", "category": "Consolidation", "vendor_id": "VEN-018",
         "venue_ids": "V-016;V-018;V-019",
         "description": "Pan-Asia supplies consolidation across Singapore, Tokyo, Taipei",
         "annual_savings_aed": 520000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-011", "category": "Renegotiation", "vendor_id": "VEN-009",
         "venue_ids": "V-001;V-003;V-005;V-008;V-009;V-006",
         "description": "Wine imports — Burgundy direct purchasing agreement",
         "annual_savings_aed": 1200000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-012", "category": "Consolidation", "vendor_id": "VEN-022",
         "venue_ids": "all",
         "description": "Reservation platform group license consolidation",
         "annual_savings_aed": 900000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-013", "category": "Substitution", "vendor_id": "VEN-004",
         "venue_ids": "V-017;V-021;V-022",
         "description": "Wagyu sourcing — direct from Japan vs. distributor",
         "annual_savings_aed": 420000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-014", "category": "Renegotiation", "vendor_id": "VEN-024",
         "venue_ids": "all",
         "description": "Energy optimisation — group-wide smart metering contract",
         "annual_savings_aed": 1600000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-015", "category": "Consolidation", "vendor_id": "VEN-017",
         "venue_ids": "V-002;V-003;V-004;V-005;V-008;V-009;V-020;V-022;V-023",
         "description": "European cleaning services single contract",
         "annual_savings_aed": 780000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-016", "category": "Renegotiation", "vendor_id": "VEN-011",
         "venue_ids": "V-016;V-017;V-018;V-019;V-020;V-021;V-022",
         "description": "Japanese sake & whisky — volume commitment across Asia + CLAP",
         "annual_savings_aed": 550000, "status": "Pipeline", "captured_date": ""},
        {"savings_id": "SAV-017", "category": "Substitution", "vendor_id": "",
         "venue_ids": "V-029;V-030",
         "description": "New Ventures — substitute commodity suppliers with group contracts",
         "annual_savings_aed": 180000, "status": "Identified", "captured_date": ""},
        {"savings_id": "SAV-018", "category": "Consolidation", "vendor_id": "",
         "venue_ids": "V-010;V-011;V-014",
         "description": "Gulf region Em Sherif — consolidate local procurement",
         "annual_savings_aed": 350000, "status": "Identified", "captured_date": ""},
        {"savings_id": "SAV-019", "category": "Renegotiation", "vendor_id": "VEN-025",
         "venue_ids": "V-001;V-003;V-008;V-020;V-022",
         "description": "Design & interiors — retainer vs. project-based pricing",
         "annual_savings_aed": 480000, "status": "Identified", "captured_date": ""},
        {"savings_id": "SAV-020", "category": "Consolidation", "vendor_id": "",
         "venue_ids": "V-006;V-016;V-018;V-019",
         "description": "Resort & Asia — shared cold-chain logistics",
         "annual_savings_aed": 620000, "status": "Identified", "captured_date": ""},
    ]
    pd.DataFrame(rows).to_csv(path, index=False)


# ── Scope filtering ─────────────────────────────────────────────

def get_scope_venue_ids(venues_df, scope):
    df = venues_df
    if scope.get("vertical") and scope["vertical"] != "All":
        df = df[df["vertical"] == scope["vertical"]]
    if scope.get("brand") and scope["brand"] != "All":
        df = df[df["concept_brand"] == scope["brand"]]
    if scope.get("venue") and scope["venue"] != "All":
        df = df[df["sub_brand"] == scope["venue"]]
    return set(df["venue_id"])


def filter_by_scope(df, venue_ids, venue_col="venue_id"):
    if not venue_ids:
        return df.iloc[0:0]
    return df[df[venue_col].isin(venue_ids)]


# ── Derived metrics ─────────────────────────────────────────────

def compute_repeat_guest_rate(txn_df, venue_ids):
    scoped = txn_df[txn_df["venue_id"].isin(venue_ids) & (txn_df["guest_id"] != "")]
    if scoped.empty:
        return 0.0
    visits = scoped.groupby("guest_id")["transaction_id"].count()
    return (visits > 1).mean() * 100


def compute_slot_splits(txn_df, venue_ids):
    scoped = txn_df[txn_df["venue_id"].isin(venue_ids)]
    if scoped.empty:
        return pd.Series(dtype=float)
    return scoped["time_slot"].value_counts(normalize=True) * 100


def compute_growth_pct(summary_df, venue_ids):
    scoped = summary_df[summary_df["venue_id"].isin(venue_ids)]
    if scoped.empty:
        return 0.0
    monthly = scoped.groupby("month")["revenue_aed"].sum().sort_index()
    if len(monthly) < 6:
        return 0.0
    recent = monthly.iloc[-3:].sum()
    prior = monthly.iloc[-6:-3].sum()
    if prior == 0:
        return 0.0
    return (recent - prior) / prior * 100


def compute_cross_brand_affinity(txn_df, guests_df):
    multi = guests_df[guests_df["brands_visited_count"] >= 2]["guest_id"]
    scoped = txn_df[txn_df["guest_id"].isin(multi)]
    if scoped.empty:
        return pd.DataFrame()
    venues = load_venues()[["venue_id", "vertical"]]
    merged = scoped.merge(venues, on="venue_id")[["guest_id", "vertical"]].drop_duplicates()
    verticals = sorted(merged["vertical"].unique())
    matrix = pd.DataFrame(0, index=verticals, columns=verticals)
    for _, grp in merged.groupby("guest_id"):
        verts = grp["vertical"].unique()
        for a in verts:
            for b in verts:
                matrix.loc[a, b] += 1
    return matrix


def compute_ltv_uplift(guests_df):
    multi = guests_df[guests_df["brands_visited_count"] >= 2]
    single = guests_df[guests_df["brands_visited_count"] == 1]
    if single.empty or multi.empty:
        return 0.0, 0.0, 0.0
    m_avg = multi["lifetime_spend_aed"].mean()
    s_avg = single["lifetime_spend_aed"].mean()
    return m_avg, s_avg, (m_avg / s_avg if s_avg > 0 else 0)


def compute_waitlist_rate(reservations_df, venue_ids):
    scoped = reservations_df[reservations_df["venue_id"].isin(venue_ids)]
    if scoped.empty:
        return 0.0
    return (scoped["status"] == "Waitlist").mean() * 100


def compute_anomaly_flags(daily_ops_df, venue_id, window=30, sigma=2):
    scoped = daily_ops_df[daily_ops_df["venue_id"] == venue_id].sort_values("date").copy()
    if len(scoped) < window + 1:
        return pd.DataFrame()
    scoped["rolling_mean"] = scoped["revenue_total_aed"].rolling(window, min_periods=10).mean()
    scoped["rolling_std"] = scoped["revenue_total_aed"].rolling(window, min_periods=10).std()
    scoped["is_anomaly"] = (
        (scoped["revenue_total_aed"] > scoped["rolling_mean"] + sigma * scoped["rolling_std"])
        | (scoped["revenue_total_aed"] < scoped["rolling_mean"] - sigma * scoped["rolling_std"])
    )
    return scoped[scoped["is_anomaly"]][["date", "revenue_total_aed"]]
