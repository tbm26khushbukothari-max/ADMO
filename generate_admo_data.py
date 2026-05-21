"""
ADMO Lifestyle Holding — Synthetic Data Generator
==================================================
Generates 16 CSVs modeling ADMO's real portfolio with engineered insights.

Run: python generate_admo_data.py
Output: ./data/*.csv (16 files)

Engineered facts (validate after generation):
- Nammos Dubai 2024 revenue ~ USD $71M (~AED 261M)
- Multi-brand guests: ~4% of guest base, ~22% of revenue
- 3 venues with engineered performance issues (for alerts)
- 1 signature vendor with degrading quality (for blast radius)
- 1 critical talent gap in Maldives (for succession map)
- Mykonos seasonality (closed Nov-Apr), Dubai summer dip, F1 spike, Ramadan effect
"""

import os
import random
import math
from datetime import date, datetime, timedelta
from pathlib import Path
import csv

# ============================================================
# REPRODUCIBILITY
# ============================================================
random.seed(42)

OUT_DIR = Path("./data")
OUT_DIR.mkdir(exist_ok=True)

# ============================================================
# CONSTANTS & REFERENCE TABLES
# ============================================================

START_DATE = date(2024, 11, 1)   # 18-month window
END_DATE = date(2026, 5, 1)

# FX to AED (fixed for demo — in real product these would be daily)
FX_TO_AED = {
    "AED": 1.0,
    "USD": 3.67,
    "EUR": 4.00,
    "GBP": 4.65,
    "SGD": 2.72,
    "JPY": 0.024,
    "TWD": 0.115,
    "BHD": 9.74,
    "QAR": 1.01,
    "OMR": 9.54,
    "LBP": 0.000041,
}

# ============================================================
# 1. VENUE MASTER — real ADMO portfolio
# ============================================================

VENUES = [
    # venue_id, brand, sub_brand, city, country, region, venue_type, open_date, seat_capacity, currency
    ("V-001", "Nammos", "Nammos Dubai", "Dubai", "UAE", "MENA", "Beach club + Fine dining", "2019-12-15", 280, "AED"),
    ("V-002", "Nammos", "Nammos Mykonos", "Mykonos", "Greece", "Europe", "Beach club + Fine dining", "2003-06-01", 320, "EUR"),
    ("V-003", "Nammos", "Nammos Mayfair London", "London", "UK", "Europe", "Fine dining", "2025-07-01", 140, "GBP"),
    ("V-004", "Nammos", "Nammos Cannes", "Cannes", "France", "Europe", "Beach club", "2024-06-15", 200, "EUR"),
    ("V-005", "Nammos", "Nammos Hotel Mykonos", "Mykonos", "Greece", "Europe", "Hotel", "2023-05-01", 60, "EUR"),
    ("V-006", "Nammos", "Nammos Resort Maldives", "Male", "Maldives", "Asia", "Resort", "2026-04-01", 80, "USD"),
    ("V-007", "Em Sherif", "Em Sherif Beirut", "Beirut", "Lebanon", "MENA", "Fine dining", "2011-09-15", 110, "USD"),
    ("V-008", "Em Sherif", "Em Sherif Harrods London", "London", "UK", "Europe", "Fine dining", "2022-11-01", 95, "GBP"),
    ("V-009", "Em Sherif", "Em Sherif Monaco", "Monaco", "Monaco", "Europe", "Fine dining", "2023-04-01", 85, "EUR"),
    ("V-010", "Em Sherif", "Em Sherif Doha", "Doha", "Qatar", "MENA", "Fine dining", "2024-01-15", 120, "QAR"),
    ("V-011", "Em Sherif", "Em Sherif Muscat", "Muscat", "Oman", "MENA", "Fine dining", "2024-09-01", 100, "OMR"),
    ("V-012", "Em Sherif", "Em Sherif Cafe Dubai", "Dubai", "UAE", "MENA", "Cafe", "2018-03-15", 70, "AED"),
    ("V-013", "Em Sherif", "Em Sherif Cafe Abu Dhabi", "Abu Dhabi", "UAE", "MENA", "Cafe", "2019-06-15", 65, "AED"),
    ("V-014", "Em Sherif", "Em Sherif Sea Cafe Manama", "Manama", "Bahrain", "MENA", "Seafood", "2022-04-01", 130, "BHD"),
    ("V-015", "Em Sherif", "Em Sherif Sea Cafe Abu Dhabi", "Abu Dhabi", "UAE", "MENA", "Seafood", "2023-09-15", 140, "AED"),
    ("V-016", "CE LA VI", "CE LA VI Singapore", "Singapore", "Singapore", "Asia", "Rooftop", "2010-06-15", 220, "SGD"),
    ("V-017", "CE LA VI", "CE LA VI Dubai", "Dubai", "UAE", "MENA", "Rooftop", "2019-04-01", 180, "AED"),
    ("V-018", "CE LA VI", "CE LA VI Tokyo", "Tokyo", "Japan", "Asia", "Rooftop", "2017-09-01", 160, "JPY"),
    ("V-019", "CE LA VI", "CE LA VI Taipei", "Taipei", "Taiwan", "Asia", "Rooftop", "2016-11-15", 150, "TWD"),
    ("V-020", "CE LA VI", "CE LA VI London Paddington", "London", "UK", "Europe", "Rooftop", "2025-09-01", 170, "GBP"),
    ("V-021", "AlphaMind", "CLAP Dubai", "Dubai", "UAE", "MENA", "Japanese", "2018-10-15", 130, "AED"),
    ("V-022", "AlphaMind", "CLAP Knightsbridge London", "London", "UK", "Europe", "Japanese", "2024-01-12", 110, "GBP"),
    ("V-023", "AlphaMind", "CLAP HOUSE Ibiza", "Ibiza", "Spain", "Europe", "Wellness/Japanese", "2025-06-01", 200, "EUR"),
    ("V-024", "AlphaMind", "Babylon DIFC Dubai", "Dubai", "UAE", "MENA", "Lebanese + Club", "2017-11-15", 180, "AED"),
    ("V-025", "AlphaMind", "Sucre Dubai", "Dubai", "UAE", "MENA", "Argentinian fire", "2022-09-01", 140, "AED"),
    ("V-026", "AlphaMind", "Bar Du Port Dubai", "Dubai", "UAE", "MENA", "Riviera", "2020-11-15", 160, "AED"),
    ("V-027", "AlphaMind", "Bar Du Port Yas Marina", "Abu Dhabi", "UAE", "MENA", "Riviera", "2025-04-01", 150, "AED"),
    ("V-028", "AlphaMind", "Iris Dubai", "Dubai", "UAE", "MENA", "Lounge", "2014-06-15", 220, "AED"),
    ("V-029", "Other ADMO", "Nalu Hudayriyat", "Abu Dhabi", "UAE", "MENA", "Lifestyle", "2024-11-01", 250, "AED"),
    ("V-030", "Other ADMO", "Son of a Fish Dubai Harbour", "Dubai", "UAE", "MENA", "Greek casual", "2025-02-15", 180, "AED"),
]

# Per-venue economic parameters
# (avg_cover_aed, beverage_share, food_cost_pct, labor_cost_pct, base_occupancy, no_show_pct, has_seasonality, mykonos_closed)
VENUE_ECONOMICS = {
    "V-001": (2100, 0.58, 0.28, 0.22, 0.94, 0.08, "dubai_summer_dip", False),
    "V-002": (1150, 0.55, 0.30, 0.28, 0.92, 0.05, "mykonos_seasonal", True),
    "V-003": (1400, 0.42, 0.32, 0.28, 0.85, 0.10, "london_seasonal", False),
    "V-004": (1300, 0.50, 0.30, 0.26, 0.88, 0.07, "cannes_seasonal", False),
    "V-005": (3200, 0.30, 0.34, 0.30, 0.78, 0.04, "mykonos_seasonal", True),
    "V-006": (4500, 0.32, 0.36, 0.32, 0.65, 0.03, "maldives_seasonal", False),
    "V-007": (380, 0.28, 0.32, 0.30, 0.82, 0.09, "none", False),
    "V-008": (650, 0.30, 0.34, 0.30, 0.90, 0.06, "london_seasonal", False),
    "V-009": (720, 0.32, 0.36, 0.32, 0.84, 0.07, "monaco_seasonal", False),
    "V-010": (520, 0.25, 0.32, 0.28, 0.86, 0.08, "ramadan_effect", False),
    "V-011": (480, 0.20, 0.32, 0.28, 0.80, 0.08, "ramadan_effect", False),
    "V-012": (180, 0.18, 0.30, 0.26, 0.88, 0.12, "dubai_summer_dip", False),
    "V-013": (170, 0.18, 0.30, 0.26, 0.85, 0.12, "dubai_summer_dip", False),
    "V-014": (340, 0.25, 0.32, 0.28, 0.82, 0.09, "ramadan_effect", False),
    "V-015": (360, 0.26, 0.32, 0.28, 0.83, 0.09, "dubai_summer_dip", False),
    "V-016": (520, 0.48, 0.30, 0.24, 0.91, 0.06, "none", False),
    "V-017": (680, 0.52, 0.30, 0.24, 0.90, 0.08, "dubai_summer_dip", False),
    "V-018": (580, 0.45, 0.32, 0.26, 0.88, 0.05, "none", False),
    "V-019": (440, 0.42, 0.32, 0.26, 0.85, 0.06, "none", False),
    "V-020": (620, 0.50, 0.32, 0.26, 0.83, 0.10, "london_seasonal", False),
    "V-021": (820, 0.45, 0.32, 0.26, 0.87, 0.08, "dubai_summer_dip", False),
    "V-022": (780, 0.45, 0.34, 0.28, 0.82, 0.10, "london_seasonal", False),
    "V-023": (920, 0.55, 0.34, 0.28, 0.78, 0.06, "ibiza_seasonal", False),
    "V-024": (740, 0.62, 0.30, 0.24, 0.86, 0.09, "dubai_summer_dip", False),
    "V-025": (680, 0.40, 0.34, 0.26, 0.84, 0.09, "dubai_summer_dip", False),
    "V-026": (620, 0.52, 0.32, 0.24, 0.88, 0.08, "dubai_summer_dip", False),
    "V-027": (580, 0.50, 0.32, 0.24, 0.78, 0.10, "dubai_summer_dip", False),
    "V-028": (520, 0.65, 0.28, 0.22, 0.85, 0.10, "dubai_summer_dip", False),
    "V-029": (480, 0.42, 0.32, 0.26, 0.72, 0.10, "dubai_summer_dip", False),
    "V-030": (520, 0.40, 0.32, 0.26, 0.74, 0.10, "dubai_summer_dip", False),
}

# Engineered "problem" venues for the alerts engine
PROBLEM_VENUES = {
    "V-027": "ramp_underperform",   # Bar Du Port Yas Marina opened Apr 2025, ramp slower than plan
    "V-011": "labor_cost_spike",     # Em Sherif Muscat labor cost climbing
    "V-019": "nps_decline",          # CE LA VI Taipei NPS sliding
}

# ============================================================
# 2. GUEST MASTER
# ============================================================

NATIONALITIES = [
    ("UAE", 0.18, ["Dubai", "Abu Dhabi", "Sharjah"]),
    ("Saudi Arabia", 0.08, ["Riyadh", "Jeddah"]),
    ("Qatar", 0.04, ["Doha"]),
    ("Kuwait", 0.03, ["Kuwait City"]),
    ("Bahrain", 0.02, ["Manama"]),
    ("UK", 0.18, ["London", "Manchester"]),
    ("USA", 0.13, ["New York", "Los Angeles", "Miami"]),
    ("France", 0.08, ["Paris", "Nice", "Cannes"]),
    ("Russia", 0.05, ["Moscow", "Saint Petersburg"]),
    ("India", 0.08, ["Mumbai", "Delhi", "Bangalore"]),
    ("Lebanon", 0.04, ["Beirut"]),
    ("Singapore", 0.03, ["Singapore"]),
    ("Italy", 0.03, ["Milan", "Rome"]),
    ("Germany", 0.03, ["Berlin", "Munich"]),
]

LANG_BY_NATIONALITY = {
    "UAE": "AR", "Saudi Arabia": "AR", "Qatar": "AR", "Kuwait": "AR",
    "Bahrain": "AR", "Lebanon": "AR",
    "UK": "EN", "USA": "EN", "Singapore": "EN", "India": "EN",
    "France": "FR",
    "Russia": "RU", "Italy": "IT", "Germany": "DE",
}

DIETARY_FLAGS = [
    ("none", 0.70),
    ("halal", 0.12),
    ("gluten-free", 0.06),
    ("vegetarian", 0.05),
    ("pescatarian", 0.03),
    ("vegan", 0.02),
    ("halal,gluten-free", 0.01),
    ("vegetarian,gluten-free", 0.01),
]

ACQUISITION_CHANNELS = [
    ("Direct", 0.35),
    ("Concierge", 0.25),
    ("Hotel partner", 0.15),
    ("Referral", 0.15),
    ("Digital", 0.10),
]


def weighted_choice(items):
    """items: list of (value, weight) tuples"""
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    upto = 0
    for value, weight in items:
        upto += weight
        if upto >= r:
            return value
    return items[-1][0]


def pick_nationality():
    total = sum(w for _, w, _ in NATIONALITIES)
    r = random.uniform(0, total)
    upto = 0
    for nat, w, cities in NATIONALITIES:
        upto += w
        if upto >= r:
            return nat, random.choice(cities)
    return NATIONALITIES[0][0], NATIONALITIES[0][2][0]


def generate_guests(n=5000):
    """Generate guest master with engineered tier distribution and brand-affinity."""
    guests = []
    # Pre-decide brands_visited per guest: 70% single, 20% two, 8% three, 2% all four
    for i in range(1, n + 1):
        guest_id = f"G-{100000 + i}"
        nationality, home_city = pick_nationality()
        home_country = "UAE" if home_city in ["Dubai", "Abu Dhabi", "Sharjah"] else nationality
        language = LANG_BY_NATIONALITY.get(nationality, "EN")
        dietary = weighted_choice(DIETARY_FLAGS)
        if dietary == "none":
            dietary = ""

        # Brands visited (engineered cross-brand distribution)
        r = random.random()
        if r < 0.70:
            brands_visited = 1
        elif r < 0.90:
            brands_visited = 2
        elif r < 0.98:
            brands_visited = 3
        else:
            brands_visited = 4

        # Tier (correlated with brands_visited, but with overlap)
        # Multi-brand guests are much more likely to be Platinum/Diamond
        tier_roll = random.random()
        if brands_visited >= 3:
            # heavily skewed Diamond/Platinum
            if tier_roll < 0.30:
                tier = "Diamond"
            elif tier_roll < 0.75:
                tier = "Platinum"
            elif tier_roll < 0.95:
                tier = "Gold"
            else:
                tier = "Standard"
        elif brands_visited == 2:
            if tier_roll < 0.05:
                tier = "Diamond"
            elif tier_roll < 0.25:
                tier = "Platinum"
            elif tier_roll < 0.65:
                tier = "Gold"
            else:
                tier = "Standard"
        else:  # single brand
            if tier_roll < 0.01:
                tier = "Diamond"
            elif tier_roll < 0.05:
                tier = "Platinum"
            elif tier_roll < 0.22:
                tier = "Gold"
            else:
                tier = "Standard"

        # First seen date (skewed slightly recent — portfolio growing)
        days_back = int(random.triangular(0, 900, 200))
        first_seen = END_DATE - timedelta(days=days_back)

        # First brand: skewed by portfolio age
        first_brand_roll = random.random()
        if first_brand_roll < 0.45:
            first_brand = "Nammos"
        elif first_brand_roll < 0.70:
            first_brand = "Em Sherif"
        elif first_brand_roll < 0.88:
            first_brand = "CE LA VI"
        else:
            first_brand = "AlphaMind"

        # LTV: log-normal-ish by tier, in AED
        if tier == "Diamond":
            ltv = int(random.uniform(800000, 5000000))
        elif tier == "Platinum":
            ltv = int(random.uniform(150000, 800000))
        elif tier == "Gold":
            ltv = int(random.uniform(30000, 150000))
        else:
            ltv = int(random.uniform(2000, 30000))

        # Total visits: correlated with LTV
        avg_cover_assumed = 800  # rough portfolio avg
        total_visits = max(1, int(ltv / avg_cover_assumed / random.uniform(1.5, 3.5)))

        last_visit_days = int(random.triangular(0, days_back, 30))
        last_visit = END_DATE - timedelta(days=last_visit_days)

        # Event hosts
        if tier in ("Diamond", "Platinum") and random.random() < 0.40:
            event_count = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        elif tier == "Gold" and random.random() < 0.05:
            event_count = 1
        else:
            event_count = 0

        # Consent flags (for guest intelligence privacy slide)
        consent_roll = random.random()
        if consent_roll < 0.62:
            consent_status = "Full"
        elif consent_roll < 0.85:
            consent_status = "Partial"
        else:
            consent_status = "None"

        guests.append({
            "guest_id": guest_id,
            "nationality": nationality,
            "home_city": home_city,
            "home_country": home_country,
            "guest_tier": tier,
            "first_seen_date": first_seen.isoformat(),
            "first_seen_brand": first_brand,
            "dietary_flags": dietary,
            "preferred_language": language,
            "lifetime_spend_aed": ltv,
            "total_visits": total_visits,
            "brands_visited_count": brands_visited,
            "last_visit_date": last_visit.isoformat(),
            "acquisition_channel": weighted_choice(ACQUISITION_CHANNELS),
            "event_host_count": event_count,
            "consent_status": consent_status,
        })
    return guests


# ============================================================
# 3. SEASONALITY & DAY-OF-WEEK MULTIPLIERS
# ============================================================

def seasonality_mult(d: date, profile: str) -> float:
    """Return revenue multiplier 0..1.5 based on date and venue seasonality profile."""
    m = d.month
    if profile == "mykonos_seasonal":
        # Closed Nov-Apr
        if m in (11, 12, 1, 2, 3, 4):
            return 0.0
        # Peak Jul-Aug
        if m in (7, 8):
            return 1.50
        if m in (6, 9):
            return 1.20
        return 1.00
    if profile == "maldives_seasonal":
        if m in (12, 1, 2, 3):
            return 1.30
        if m in (6, 7, 8):
            return 0.70
        return 1.00
    if profile == "cannes_seasonal":
        if m in (11, 12, 1, 2):
            return 0.50
        if m in (5, 6, 7, 8, 9):
            return 1.30
        return 1.00
    if profile == "ibiza_seasonal":
        if m in (6, 7, 8):
            return 1.45
        if m in (11, 12, 1, 2, 3):
            return 0.40
        return 0.90
    if profile == "monaco_seasonal":
        if m in (5, 6, 7, 8, 9):
            return 1.20
        if m in (1, 2):
            return 0.75
        return 1.00
    if profile == "london_seasonal":
        if m in (11, 12):
            return 1.25
        if m in (1, 2):
            return 0.80
        if m in (7, 8):
            return 0.90
        return 1.00
    if profile == "dubai_summer_dip":
        if m in (7, 8):
            return 0.65
        if m in (11, 12, 1, 2):
            return 1.20
        return 1.00
    if profile == "ramadan_effect":
        # Ramadan 2025: Feb 28 - Mar 30. Ramadan 2026: Feb 17 - Mar 19.
        ramadan_25 = (date(2025, 2, 28), date(2025, 3, 30))
        ramadan_26 = (date(2026, 2, 17), date(2026, 3, 19))
        for start, end in (ramadan_25, ramadan_26):
            if start <= d <= end:
                return 0.70
        return 1.00
    return 1.00


def dow_mult(d: date, venue_type: str) -> float:
    """Day of week multiplier."""
    dow = d.weekday()  # Mon=0
    if venue_type in ("Beach club + Fine dining", "Beach club", "Rooftop", "Lounge", "Lebanese + Club", "Wellness/Japanese"):
        # Heavy weekends + Thursday/Friday
        return [0.7, 0.7, 0.8, 1.0, 1.4, 1.5, 1.2][dow]
    if venue_type in ("Fine dining",):
        return [0.7, 0.8, 0.9, 1.1, 1.3, 1.4, 1.1][dow]
    if venue_type == "Cafe":
        return [1.0, 1.0, 1.0, 1.0, 1.1, 1.3, 1.3][dow]
    if venue_type in ("Hotel", "Resort"):
        return [0.9, 0.9, 0.9, 1.0, 1.2, 1.3, 1.1][dow]
    return [0.8, 0.8, 0.9, 1.0, 1.3, 1.4, 1.2][dow]


def f1_weekend_bump(d: date, city: str) -> float:
    """Abu Dhabi GP first weekend of December (approx)."""
    if city in ("Abu Dhabi", "Dubai") and d.month == 12 and 5 <= d.day <= 9:
        return 1.45
    return 1.00


def problem_venue_mult(d: date, venue_id: str) -> float:
    """Apply engineered underperformance for flagged venues."""
    if venue_id == "V-027":  # Bar Du Port Yas Marina — ramp issue
        # Opened 2025-04-01. Underperform until ~3 months ago, then started recovering.
        if d >= date(2025, 4, 1):
            days_open = (d - date(2025, 4, 1)).days
            # Targets a stable 0.78; actually around 0.55-0.65 first 8 months
            if days_open < 240:
                return 0.65
            elif days_open < 330:
                return 0.78
            else:
                return 0.85
    return 1.00


# ============================================================
# 4. TRANSACTIONS
# ============================================================

def generate_transactions(guests):
    """Generate ~50K transactions, calibrated so Nammos Dubai 2024 lands near $71M."""
    transactions = []

    # Build guest-to-brands mapping (sticky)
    guest_brand_map = {}
    for g in guests:
        n_brands = g["brands_visited_count"]
        first_brand = g["first_seen_brand"]
        all_brands = ["Nammos", "Em Sherif", "CE LA VI", "AlphaMind"]
        chosen = [first_brand]
        remaining = [b for b in all_brands if b != first_brand]
        random.shuffle(remaining)
        chosen.extend(remaining[:n_brands - 1])
        guest_brand_map[g["guest_id"]] = chosen

    # Brand → venue list
    brand_venues = {}
    for v in VENUES:
        brand_venues.setdefault(v[1], []).append(v[0])

    # Target ~50,000 transactions
    # Distribute roughly: Nammos Dubai gets the most (highest grossing in world)
    # We'll generate per-venue and per-day, sampling guests appropriately.

    # First, calculate per-venue target txn count
    # Nammos Dubai: world's #1 restaurant doing $71M/yr.
    # At cap 280 * 1.6 turns * 340 days * 94% occ = ~143K covers/yr.
    # At ~3 covers per check, that's ~48K transactions per year, ~72K for 18 months.
    venue_txn_targets = {}
    for v in VENUES:
        vid, brand, sub, city, country, region, vtype, open_str, cap, ccy = v
        open_d = date.fromisoformat(open_str)
        operating_start = max(open_d, START_DATE)
        if operating_start > END_DATE:
            venue_txn_targets[vid] = 0
            continue
        days_operating = (END_DATE - operating_start).days
        # Base rate: ~3 transactions per day per 30 capacity (i.e. ~1 check per 10 cap per service)
        # tuned to real luxury hospitality: 280-cap venue at high turn = ~150 checks/day
        # for 18 months = ~80K checks max; we throttle by occupancy multipliers
        service_turns = 1.6 if vtype in ("Beach club + Fine dining", "Beach club", "Rooftop", "Lounge", "Lebanese + Club") else 1.3
        if vtype == "Cafe":
            service_turns = 2.0
        if vtype in ("Hotel", "Resort"):
            service_turns = 1.0
        # Each transaction = 1 booking/table (typically 2-12 covers per booking, mean ~7)
        # Calibration: ~1 booking per 8 covers; capacity * turns gives covers/day
        # Factor 0.70 lands Nammos Dubai at ~$71M
        base_rate = (cap * service_turns) / 8.0 * 0.70
        # Scale Nammos Dubai (world's #1)
        if vid == "V-001":
            base_rate *= 1.15
        # Mykonos seasonal — operating ~180 days/yr
        if vid in ("V-002", "V-005"):
            days_operating = days_operating * 6 / 12  # rough
        venue_txn_targets[vid] = int(base_rate * days_operating)

    # Total target is now driven by realistic per-venue volumes (~250-300K total)
    # We'll trust the bottoms-up calculation rather than re-scaling.

    # Generate transactions per venue
    txn_counter = 0
    for v in VENUES:
        vid, brand, sub, city, country, region, vtype, open_str, cap, ccy = v
        target = venue_txn_targets.get(vid, 0)
        if target == 0:
            continue

        open_d = date.fromisoformat(open_str)
        operating_start = max(open_d, START_DATE)

        avg_cover_aed, bev_share, food_cost_pct, labor_cost_pct, base_occ, no_show_pct, season_profile, _ = VENUE_ECONOMICS[vid]

        # Eligible guests: those who have this brand in their mapping
        eligible_guests = [g for g in guests if brand in guest_brand_map[g["guest_id"]]]
        # Plus some walk-ins (no guest_id)

        operating_days = (END_DATE - operating_start).days
        if operating_days <= 0:
            continue

        for _ in range(target):
            # Pick a date
            day_offset = random.randint(0, operating_days - 1)
            txn_date = operating_start + timedelta(days=day_offset)

            # Seasonality kill switch
            season = seasonality_mult(txn_date, season_profile)
            if season <= 0.01:
                continue  # venue closed

            # Walk-in vs known guest
            if random.random() < 0.25 or not eligible_guests:
                guest_id = ""  # walk-in
            else:
                guest = random.choice(eligible_guests)
                guest_id = guest["guest_id"]

            # Time slot
            time_slot_roll = random.random()
            if vtype == "Cafe":
                if time_slot_roll < 0.3:
                    slot = "Breakfast"
                elif time_slot_roll < 0.7:
                    slot = "Lunch"
                else:
                    slot = "Dinner"
            elif vtype in ("Lounge", "Lebanese + Club"):
                slot = "Dinner" if time_slot_roll < 0.4 else "Late night"
            elif "Beach" in vtype:
                if time_slot_roll < 0.35:
                    slot = "Lunch"
                else:
                    slot = "Dinner"
            else:
                slot = "Lunch" if time_slot_roll < 0.25 else "Dinner"

            # Cover count per booking (table) — typical luxury venue table = 2-12 guests
            cover_count = max(2, int(random.triangular(2, 14, 6)))

            # Revenue per cover (apply variability + multipliers)
            base_pc = avg_cover_aed
            mults = (
                season *
                dow_mult(txn_date, vtype) *
                f1_weekend_bump(txn_date, city) *
                problem_venue_mult(txn_date, vid)
            )
            pc = base_pc * mults * random.uniform(0.7, 1.4)
            total_aed = pc * cover_count
            beverage_aed = total_aed * bev_share * random.uniform(0.85, 1.15)
            food_aed = total_aed - beverage_aed
            if food_aed < 0:
                food_aed = total_aed * 0.4
                beverage_aed = total_aed * 0.6

            # Convert to local currency
            fx = FX_TO_AED.get(ccy, 1.0)
            total_local = total_aed / fx
            food_local = food_aed / fx
            beverage_local = beverage_aed / fx

            # Reservation lead time
            if vid == "V-001":
                lead_time = max(0, int(random.triangular(0, 90, 14)))
            elif vtype == "Cafe":
                lead_time = max(0, int(random.triangular(0, 7, 0)))
            elif vtype in ("Fine dining", "Beach club + Fine dining"):
                lead_time = max(0, int(random.triangular(0, 60, 7)))
            else:
                lead_time = max(0, int(random.triangular(0, 30, 3)))

            # Occasion flag
            occ_roll = random.random()
            if occ_roll < 0.04:
                occasion = "Birthday"
            elif occ_roll < 0.06:
                occasion = "Anniversary"
            elif occ_roll < 0.075:
                occasion = "Corporate"
            elif occ_roll < 0.082:
                occasion = "Private dining"
            elif occ_roll < 0.085:
                occasion = "Wedding"
            else:
                occasion = ""

            # Satisfaction — slightly skewed by problem venues
            base_sat = 8.4
            if vid in PROBLEM_VENUES:
                if PROBLEM_VENUES[vid] == "nps_decline" and txn_date > date(2025, 12, 1):
                    base_sat = 7.5
            sat = max(1, min(10, int(random.gauss(base_sat, 1.2))))

            txn_counter += 1
            transactions.append({
                "transaction_id": f"T-{txn_date.strftime('%Y%m%d')}-{txn_counter:06d}",
                "guest_id": guest_id,
                "venue_id": vid,
                "transaction_date": txn_date.isoformat(),
                "time_slot": slot,
                "cover_count": cover_count,
                "food_revenue_aed": round(food_aed, 2),
                "beverage_revenue_aed": round(beverage_aed, 2),
                "total_revenue_aed": round(total_aed, 2),
                "food_revenue_local": round(food_local, 2),
                "beverage_revenue_local": round(beverage_local, 2),
                "total_revenue_local": round(total_local, 2),
                "currency": ccy,
                "avg_check_per_cover_aed": round(total_aed / cover_count, 2),
                "reservation_lead_time_days": lead_time,
                "occasion_flag": occasion,
                "guest_satisfaction_score": sat,
            })

    return transactions


# ============================================================
# 5. DAILY OPS METRICS
# ============================================================

def generate_daily_ops(transactions):
    """Roll up transactions into daily venue metrics."""
    from collections import defaultdict
    daily = defaultdict(lambda: {
        "covers_total": 0, "revenue_total_aed": 0.0,
        "food_revenue_aed": 0.0, "beverage_revenue_aed": 0.0,
        "sat_sum": 0, "sat_count": 0,
        "events_count": 0, "events_revenue_aed": 0.0,
        "wait_list_proxy": 0,
    })

    for t in transactions:
        key = (t["transaction_date"], t["venue_id"])
        daily[key]["covers_total"] += t["cover_count"]
        daily[key]["revenue_total_aed"] += t["total_revenue_aed"]
        daily[key]["food_revenue_aed"] += t["food_revenue_aed"]
        daily[key]["beverage_revenue_aed"] += t["beverage_revenue_aed"]
        daily[key]["sat_sum"] += t["guest_satisfaction_score"]
        daily[key]["sat_count"] += 1
        if t["occasion_flag"] in ("Wedding", "Private dining", "Corporate"):
            daily[key]["events_count"] += 1
            daily[key]["events_revenue_aed"] += t["total_revenue_aed"]

    rows = []
    for (d, vid), v in daily.items():
        avg_sat = v["sat_sum"] / v["sat_count"] if v["sat_count"] else 0
        # NPS: simple promoters - detractors
        # treating 9-10 promoter, 7-8 passive, <=6 detractor — but we have averages, so approximate
        nps_approx = int((avg_sat - 6.5) * 20)  # rough mapping
        nps_approx = max(-30, min(95, nps_approx))

        # Cost % with slight randomness
        econ = VENUE_ECONOMICS.get(vid)
        if econ:
            food_cost_pct = econ[2] + random.uniform(-0.02, 0.03)
            labor_cost_pct = econ[3] + random.uniform(-0.02, 0.03)
            # Engineered cost spike for V-011
            if vid == "V-011" and date.fromisoformat(d) > date(2026, 1, 1):
                labor_cost_pct += 0.08
        else:
            food_cost_pct = 0.30
            labor_cost_pct = 0.25

        # Occupancy proxy: covers / (capacity * 2 services/day)
        venue_cap = next((vv[8] for vv in VENUES if vv[0] == vid), 100)
        occupancy = min(1.0, v["covers_total"] / (venue_cap * 1.8))

        rows.append({
            "date": d,
            "venue_id": vid,
            "covers_total": v["covers_total"],
            "revenue_total_aed": round(v["revenue_total_aed"], 2),
            "food_revenue_aed": round(v["food_revenue_aed"], 2),
            "beverage_revenue_aed": round(v["beverage_revenue_aed"], 2),
            "food_cost_pct": round(food_cost_pct, 4),
            "labor_cost_pct": round(labor_cost_pct, 4),
            "occupancy_pct": round(occupancy, 4),
            "nps_score": nps_approx,
            "events_count": v["events_count"],
            "events_revenue_aed": round(v["events_revenue_aed"], 2),
            "avg_satisfaction": round(avg_sat, 2),
        })
    return rows


# ============================================================
# 6. VENDORS
# ============================================================

VENDORS = [
    # signature seafood
    ("VEN-001", "Aegean Premium Seafood", "Signature seafood", True, 0.96, 4.8, "Low"),
    ("VEN-002", "Maldivian Reef Co.", "Signature seafood", True, 0.94, 4.6, "Low"),
    ("VEN-003", "Mediterranean Catch Ltd", "Signature seafood", True, 0.91, 4.5, "Medium"),
    # signature meat
    ("VEN-004", "Tokyo Wagyu Direct", "Signature meat", True, 0.88, 4.7, "Medium"),
    ("VEN-005", "Argentina Beef Heritage", "Signature meat", True, 0.93, 4.7, "Low"),
    # signature spices/produce
    ("VEN-006", "Lebanese Heritage Spices Co.", "Signature spices", True, 0.95, 4.9, "Low"),
    ("VEN-007", "Levant Produce Specialists", "Signature produce", True, 0.92, 4.6, "Low"),
    ("VEN-008", "Greek Island Olive Oil Co-op", "Signature oils", True, 0.94, 4.8, "Low"),
    # wine / beverage signature
    ("VEN-009", "Burgundy Grand Cru Imports", "Signature wine", True, 0.89, 4.7, "Medium"),
    ("VEN-010", "Champagne Maison Direct", "Signature wine", True, 0.93, 4.8, "Low"),
    ("VEN-011", "Japanese Sake & Whisky Imports", "Signature beverage", True, 0.90, 4.6, "Medium"),
    # the engineered "degrading" vendor — this is the blast radius visual driver
    ("VEN-012", "Mykonos Local Producers Co.", "Signature produce", True, 0.78, 3.8, "High"),
    # commodity
    ("VEN-013", "UAE Linen Group", "Commodity linen", False, 0.99, 4.5, "Low"),
    ("VEN-014", "Emirates Cleaning Services", "Commodity cleaning", False, 0.96, 4.3, "Low"),
    ("VEN-015", "Global Cleaning Supplies UAE", "Commodity supplies", False, 0.97, 4.2, "Low"),
    ("VEN-016", "London Linen Services", "Commodity linen", False, 0.98, 4.4, "Low"),
    ("VEN-017", "European Cleaning Network", "Commodity cleaning", False, 0.95, 4.1, "Low"),
    ("VEN-018", "Pan-Asia Hospitality Supplies", "Commodity supplies", False, 0.94, 4.0, "Low"),
    ("VEN-019", "Gulf Beverage Distribution", "Commodity beverage", False, 0.97, 4.3, "Low"),
    ("VEN-020", "Global Coffee Roasters", "Commodity coffee", False, 0.96, 4.4, "Low"),
    # back-of-house tech / services
    ("VEN-021", "POS Hospitality Cloud", "Tech/POS", False, 0.99, 4.6, "Low"),
    ("VEN-022", "Reservation Engine Co.", "Tech/Reservations", False, 0.97, 4.5, "Low"),
    ("VEN-023", "Premium Insurance Brokers", "Insurance", False, 0.99, 4.4, "Low"),
    ("VEN-024", "Energy Optimization Group", "Utilities", False, 0.98, 4.3, "Low"),
    # signature design / interiors
    ("VEN-025", "Elastic Architects London", "Signature design", True, 0.95, 4.9, "Low"),
    ("VEN-026", "Dior Hospitality Partnerships", "Signature partnership", True, 1.00, 5.0, "Low"),
    # specialty
    ("VEN-027", "Truffle Specialists Italy", "Signature produce", True, 0.87, 4.6, "Medium"),
    ("VEN-028", "Caviar House Direct", "Signature produce", True, 0.92, 4.8, "Low"),
    ("VEN-029", "Specialty Tea Imports", "Signature beverage", True, 0.91, 4.5, "Low"),
    ("VEN-030", "Bakery Artisans International", "Signature bakery", True, 0.93, 4.7, "Low"),
]


def venue_vendor_map():
    """Many-to-many. Engineered: VEN-012 serves Nammos Mykonos + Hotel + Cannes."""
    mappings = []
    # Spread signature vendors across relevant brands
    sig_map = {
        "VEN-001": ["V-002", "V-005", "V-001", "V-006"],  # Aegean - Nammos + Em Sherif Sea Cafe
        "VEN-002": ["V-006", "V-014", "V-015"],
        "VEN-003": ["V-014", "V-015"],
        "VEN-004": ["V-017", "V-021", "V-022"],  # Wagyu for CE LA VI and CLAP
        "VEN-005": ["V-025"],  # Argentina beef for Sucre
        "VEN-006": ["V-007", "V-008", "V-009", "V-010", "V-011", "V-012", "V-013"],  # all Em Sherif
        "VEN-007": ["V-007", "V-008", "V-009", "V-010", "V-011"],
        "VEN-008": ["V-002", "V-005", "V-001", "V-004", "V-030"],  # Greek olive oil
        "VEN-009": ["V-001", "V-003", "V-005", "V-008", "V-009", "V-006"],
        "VEN-010": ["V-001", "V-002", "V-003", "V-004", "V-005", "V-016", "V-017", "V-020"],
        "VEN-011": ["V-016", "V-017", "V-018", "V-019", "V-020", "V-021", "V-022"],
        "VEN-012": ["V-002", "V-005", "V-004"],  # ENGINEERED: Mykonos + Cannes blast radius
        # Commodity vendors broader
        "VEN-013": [v[0] for v in VENUES if v[3] in ("Dubai", "Abu Dhabi")],
        "VEN-014": [v[0] for v in VENUES if v[3] in ("Dubai", "Abu Dhabi")],
        "VEN-015": [v[0] for v in VENUES if v[3] in ("Dubai", "Abu Dhabi")],
        "VEN-016": ["V-003", "V-008", "V-020", "V-022"],
        "VEN-017": ["V-002", "V-003", "V-004", "V-005", "V-008", "V-009", "V-020", "V-022", "V-023"],
        "VEN-018": ["V-016", "V-018", "V-019"],
        "VEN-019": [v[0] for v in VENUES if v[3] in ("Dubai", "Abu Dhabi")],
        "VEN-020": [v[0] for v in VENUES],
        "VEN-021": [v[0] for v in VENUES],  # POS — all venues
        "VEN-022": [v[0] for v in VENUES],
        "VEN-023": [v[0] for v in VENUES],
        "VEN-024": [v[0] for v in VENUES],
        "VEN-025": ["V-001", "V-003", "V-008", "V-020", "V-022"],
        "VEN-026": ["V-001"],  # Dior — only Nammos Dubai
        "VEN-027": ["V-001", "V-003", "V-005", "V-008", "V-009"],
        "VEN-028": ["V-001", "V-008", "V-009", "V-003"],
        "VEN-029": ["V-007", "V-008", "V-012", "V-013"],
        "VEN-030": [v[0] for v in VENUES if v[1] == "Em Sherif"],
    }
    map_id = 1
    for ven, venues in sig_map.items():
        for vid in venues:
            mappings.append({
                "mapping_id": f"VV-{map_id:04d}",
                "vendor_id": ven,
                "venue_id": vid,
            })
            map_id += 1
    return mappings


# ============================================================
# 7. EVENTS / BOOKINGS
# ============================================================

def generate_events(guests, transactions):
    """~800 private events with realistic patterns."""
    events = []
    # Eligible hosts: those with event_host_count > 0
    eligible = [g for g in guests if g["event_host_count"] > 0]

    # Suitable event venues (not cafes)
    event_venues = [v for v in VENUES if v[6] not in ("Cafe",)]

    event_id_counter = 1
    for g in eligible:
        for _ in range(g["event_host_count"]):
            venue = random.choice(event_venues)
            vid, brand, sub, city, country, region, vtype, open_str, cap, ccy = venue
            open_d = date.fromisoformat(open_str)
            operating_start = max(open_d, START_DATE)
            if operating_start > END_DATE:
                continue

            # Pick date
            day_offset = random.randint(0, (END_DATE - operating_start).days)
            event_date = operating_start + timedelta(days=day_offset)

            # Filter mykonos seasonality
            econ = VENUE_ECONOMICS.get(vid)
            if econ and seasonality_mult(event_date, econ[6]) <= 0.01:
                continue

            event_type_roll = random.random()
            if g["event_host_count"] >= 2 or g["guest_tier"] in ("Diamond", "Platinum"):
                if event_type_roll < 0.30:
                    event_type = "Wedding"
                    guest_count = random.randint(80, 250)
                elif event_type_roll < 0.65:
                    event_type = "Private Dining"
                    guest_count = random.randint(20, 80)
                elif event_type_roll < 0.85:
                    event_type = "Corporate"
                    guest_count = random.randint(30, 150)
                else:
                    event_type = "Anniversary"
                    guest_count = random.randint(30, 100)
            else:
                if event_type_roll < 0.50:
                    event_type = "Private Dining"
                    guest_count = random.randint(15, 60)
                else:
                    event_type = "Corporate"
                    guest_count = random.randint(25, 80)

            # Revenue per head: roughly 2-4x normal cover spend
            avg_cover = econ[0] if econ else 600
            per_head_aed = avg_cover * random.uniform(2.0, 4.0)
            total_aed = per_head_aed * guest_count
            deposit_aed = total_aed * random.uniform(0.20, 0.30)

            repeat_flag = "Yes" if g["event_host_count"] >= 2 else "No"

            events.append({
                "event_id": f"E-{event_date.strftime('%Y%m%d')}-{event_id_counter:04d}",
                "guest_id": g["guest_id"],
                "venue_id": vid,
                "event_date": event_date.isoformat(),
                "event_type": event_type,
                "guest_count": guest_count,
                "total_revenue_aed": round(total_aed, 2),
                "deposit_aed": round(deposit_aed, 2),
                "per_head_revenue_aed": round(per_head_aed, 2),
                "repeat_host_flag": repeat_flag,
            })
            event_id_counter += 1
    return events


# ============================================================
# 8. HIRING PIPELINE
# ============================================================

def generate_hiring():
    """~200 roles. 1 critical role for Nammos Maldives (engineered talent gap)."""
    roles = []
    role_templates = [
        ("Executive Chef", "Senior", "High"),
        ("Head Chef", "Senior", "High"),
        ("Sous Chef", "Mid", "Medium"),
        ("Restaurant Manager", "Senior", "High"),
        ("Floor Manager", "Mid", "Medium"),
        ("Head Sommelier", "Senior", "High"),
        ("Sommelier", "Mid", "Medium"),
        ("Bar Manager", "Mid", "Medium"),
        ("Mixologist", "Mid", "Low"),
        ("Server", "Junior", "Low"),
        ("Host", "Junior", "Low"),
        ("Pastry Chef", "Mid", "Medium"),
        ("Reservations Manager", "Mid", "Medium"),
        ("Events Manager", "Senior", "High"),
        ("Director of Operations", "Senior", "High"),
        ("Marketing Manager", "Mid", "Medium"),
        ("Finance Controller", "Senior", "High"),
        ("HR Manager", "Mid", "Medium"),
    ]

    role_id = 1
    # Engineered critical gap: Nammos Maldives Executive Chef (opening Apr 2026)
    roles.append({
        "position_id": f"H-2026-{role_id:04d}",
        "venue_id": "V-006",
        "role": "Executive Chef",
        "seniority": "Senior",
        "criticality": "Critical",
        "open_date": "2026-01-15",
        "days_open": (date.today() - date(2026, 1, 15)).days if date.today() > date(2026, 1, 15) else 120,
        "status": "Open",
        "blocks_opening": "Yes",
    })
    role_id += 1

    # Generate ~80 open + ~120 filled
    for _ in range(80):
        venue = random.choice(VENUES)
        role_name, seniority, criticality = random.choice(role_templates)
        open_date = END_DATE - timedelta(days=random.randint(5, 180))
        roles.append({
            "position_id": f"H-2026-{role_id:04d}",
            "venue_id": venue[0],
            "role": role_name,
            "seniority": seniority,
            "criticality": criticality,
            "open_date": open_date.isoformat(),
            "days_open": (END_DATE - open_date).days,
            "status": "Open",
            "blocks_opening": "Yes" if (venue[0] == "V-006" and seniority == "Senior") else "No",
        })
        role_id += 1

    for _ in range(120):
        venue = random.choice(VENUES)
        role_name, seniority, criticality = random.choice(role_templates)
        open_date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days - 60))
        close_date = open_date + timedelta(days=random.randint(15, 90))
        roles.append({
            "position_id": f"H-2025-{role_id:04d}",
            "venue_id": venue[0],
            "role": role_name,
            "seniority": seniority,
            "criticality": criticality,
            "open_date": open_date.isoformat(),
            "days_open": (close_date - open_date).days,
            "status": "Filled",
            "blocks_opening": "No",
        })
        role_id += 1

    return roles


# ============================================================
# 9. PLAN TARGETS
# ============================================================

def generate_plan_targets():
    """Monthly revenue/cover/NPS targets per venue."""
    targets = []
    current = date(START_DATE.year, START_DATE.month, 1)
    while current <= END_DATE:
        for v in VENUES:
            vid, brand, sub, city, country, region, vtype, open_str, cap, ccy = v
            open_d = date.fromisoformat(open_str)
            if open_d > current.replace(day=28):
                continue
            econ = VENUE_ECONOMICS.get(vid)
            if not econ:
                continue
            avg_cover, _, _, _, base_occ, _, season_profile, _ = econ
            season = seasonality_mult(current.replace(day=15), season_profile)
            if season <= 0.01:
                # Closed month — minimal target
                covers_target = 0
                revenue_target = 0
            else:
                # Approximate target
                days_in_month = 30
                covers_per_day = cap * 1.7 * base_occ
                covers_target = int(covers_per_day * days_in_month * season * 0.97)  # plan is ~97% of expected
                revenue_target = int(covers_target * avg_cover * 0.97)
            targets.append({
                "venue_id": vid,
                "month": current.isoformat(),
                "revenue_target_aed": revenue_target,
                "covers_target": covers_target,
                "nps_target": 70,
            })
        # Next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return targets


# ============================================================
# 10. RESERVATIONS TODAY (forward-looking 30 days)
# ============================================================

def generate_reservations_today(guests):
    """Forward-looking reservations for the next 30 days."""
    reservations = []
    res_id = 1
    today = END_DATE  # treat END_DATE as "today" for the demo

    for v in VENUES:
        vid, brand, sub, city, country, region, vtype, open_str, cap, ccy = v
        open_d = date.fromisoformat(open_str)
        if open_d > today:
            continue
        econ = VENUE_ECONOMICS.get(vid)
        if not econ:
            continue

        # ~30-60 reservations per venue across 30 days
        n_reservations = random.randint(25, 75)
        for _ in range(n_reservations):
            res_date = today + timedelta(days=random.randint(0, 30))
            season = seasonality_mult(res_date, econ[6])
            if season <= 0.01:
                continue

            # VIP probability higher for Nammos Dubai, Em Sherif Harrods, CE LA VI Singapore
            vip_boost = 0.15 if vid in ("V-001", "V-008", "V-016", "V-002") else 0.05
            if random.random() < vip_boost:
                guest = random.choice([g for g in guests if g["guest_tier"] in ("Diamond", "Platinum")])
            else:
                guest = random.choice(guests)

            party_size = max(2, int(random.triangular(2, 12, 4)))
            time_slot = random.choice(["Lunch", "Dinner", "Late night"]) if vtype != "Cafe" else random.choice(["Breakfast", "Lunch", "Dinner"])

            occ_roll = random.random()
            occasion = ""
            if occ_roll < 0.05:
                occasion = "Birthday"
            elif occ_roll < 0.07:
                occasion = "Anniversary"

            reservations.append({
                "reservation_id": f"R-{res_date.strftime('%Y%m%d')}-{res_id:05d}",
                "venue_id": vid,
                "reservation_date": res_date.isoformat(),
                "time_slot": time_slot,
                "guest_id": guest["guest_id"],
                "guest_tier": guest["guest_tier"],
                "party_size": party_size,
                "occasion": occasion,
                "special_requests": random.choice(["", "", "", "Quiet table", "Birthday cake", "Window seat", "Allergy: shellfish", "Wine pairing"]),
                "status": random.choices(["Confirmed", "Deposit paid", "Waitlist"], weights=[0.7, 0.2, 0.1])[0],
            })
            res_id += 1
    return reservations


# ============================================================
# 11. VIP FLAGS
# ============================================================

def generate_vip_flags(guests):
    """~40 GROUP VIP flags — celebrities, board, royalty (anonymized)."""
    vip_flags = []
    diamond_platinum = [g for g in guests if g["guest_tier"] in ("Diamond", "Platinum")]
    # Pick 40 random high-tier guests as GROUP VIPs
    selected = random.sample(diamond_platinum, min(40, len(diamond_platinum)))
    categories = [
        ("Board Member", 0.15),
        ("ADMO Investor", 0.20),
        ("UAE Royal Family", 0.10),
        ("GCC Royal Family", 0.10),
        ("Global Celebrity", 0.20),
        ("F&B Press / Critic", 0.10),
        ("Influencer (>5M)", 0.15),
    ]
    for g in selected:
        cat = weighted_choice(categories)
        vip_flags.append({
            "vip_id": f"VIP-{g['guest_id'][2:]}",
            "guest_id": g["guest_id"],
            "category": cat,
            "sensitivity_level": random.choice(["High", "Maximum", "Maximum"]),
            "notes": f"Group VIP — coordinate seating and service personally. Category: {cat}.",
            "flagged_date": (END_DATE - timedelta(days=random.randint(30, 800))).isoformat(),
        })
    return vip_flags


# ============================================================
# 12. ALERTS FEED (engine output)
# ============================================================

def generate_alerts(daily_ops, vendors, hiring):
    """Generate ~30 active alerts from the engine."""
    alerts = []
    alert_id = 1

    # 1. Problem venue alerts
    for vid, issue_type in PROBLEM_VENUES.items():
        if issue_type == "ramp_underperform":
            alerts.append({
                "alert_id": f"A-{alert_id:04d}",
                "severity": "Amber",
                "category": "Revenue",
                "venue_id": vid,
                "headline": "Ramp tracking 22% behind plan",
                "description": "Bar Du Port Yas Marina is 8 months post-opening; covers are 22% below ramp curve. Driver: lower repeat rate vs. Bar Du Port Dubai at same maturity.",
                "owner": "Brand CEO — AlphaMind",
                "raised_at": (END_DATE - timedelta(days=14)).isoformat(),
                "status": "Open",
            })
            alert_id += 1
        elif issue_type == "labor_cost_spike":
            alerts.append({
                "alert_id": f"A-{alert_id:04d}",
                "severity": "Red",
                "category": "Cost",
                "venue_id": vid,
                "headline": "Labor cost +8 pts above benchmark",
                "description": "Em Sherif Muscat labor cost % is 36% vs. portfolio benchmark of 28% for fine dining. Hiring inefficiency suspected. Action: Group Talent to audit.",
                "owner": "Group Talent + Brand COO",
                "raised_at": (END_DATE - timedelta(days=21)).isoformat(),
                "status": "Open",
            })
            alert_id += 1
        elif issue_type == "nps_decline":
            alerts.append({
                "alert_id": f"A-{alert_id:04d}",
                "severity": "Amber",
                "category": "Guest",
                "venue_id": vid,
                "headline": "NPS down 14 points over 60 days",
                "description": "CE LA VI Taipei NPS has slid from 74 to 60 over the past 60 days. Cluster of complaints around service speed during dinner peak.",
                "owner": "Brand CEO — CE LA VI",
                "raised_at": (END_DATE - timedelta(days=7)).isoformat(),
                "status": "Investigating",
            })
            alert_id += 1

    # 2. Vendor alert (the engineered degrading vendor)
    alerts.append({
        "alert_id": f"A-{alert_id:04d}",
        "severity": "Red",
        "category": "Vendor",
        "venue_id": "V-002",
        "headline": "Signature vendor quality declining",
        "description": "Mykonos Local Producers Co. (VEN-012) quality score 3.8, OTD 78%. Blast radius: Nammos Mykonos, Nammos Hotel Mykonos, Nammos Cannes. Action: identify alternate sources before May 2026 season opening.",
        "owner": "Group Procurement",
        "raised_at": (END_DATE - timedelta(days=18)).isoformat(),
        "status": "Open",
    })
    alert_id += 1

    # 3. Critical hiring gap
    alerts.append({
        "alert_id": f"A-{alert_id:04d}",
        "severity": "Red",
        "category": "Talent",
        "venue_id": "V-006",
        "headline": "Critical role open — blocks Maldives opening",
        "description": "Nammos Resort Maldives Executive Chef position open 120+ days. Opening date 1 April 2026 at risk. Group Talent escalation required.",
        "owner": "Group Talent + Nammos H&R CEO",
        "raised_at": (END_DATE - timedelta(days=120)).isoformat(),
        "status": "Escalated",
    })
    alert_id += 1

    # 4. A few opportunity alerts (positive signals)
    alerts.append({
        "alert_id": f"A-{alert_id:04d}",
        "severity": "Green",
        "category": "Opportunity",
        "venue_id": "V-008",
        "headline": "Cross-brand conversion accelerating",
        "description": "Em Sherif Harrods → Nammos Mayfair conversion rate up to 28% in last 90 days (vs. 19% trailing 12m). Suggest formalized concierge cross-referral protocol.",
        "owner": "Group Marketing",
        "raised_at": (END_DATE - timedelta(days=5)).isoformat(),
        "status": "Open",
    })
    alert_id += 1

    alerts.append({
        "alert_id": f"A-{alert_id:04d}",
        "severity": "Green",
        "category": "Opportunity",
        "venue_id": "V-001",
        "headline": "Dior partnership extension revenue lift",
        "description": "Dior Dioriviera partnership lifting Nammos Dubai weekly revenue by avg +18%. Quantified uplift: AED 14.2M YTD. Evaluation: extend or replicate across Mykonos.",
        "owner": "Group Strategy + Brand CEO",
        "raised_at": (END_DATE - timedelta(days=10)).isoformat(),
        "status": "Open",
    })
    alert_id += 1

    # 5. Generic operational
    sample_venues = ["V-022", "V-023", "V-027", "V-029"]
    for vid in sample_venues:
        alerts.append({
            "alert_id": f"A-{alert_id:04d}",
            "severity": random.choice(["Amber", "Green"]),
            "category": random.choice(["Cost", "Guest", "Revenue"]),
            "venue_id": vid,
            "headline": random.choice([
                "Food cost trending up vs. plan",
                "Wait list conversion improving",
                "Occupancy below seasonal benchmark",
                "Service speed complaint cluster",
            ]),
            "description": "Auto-generated alert from daily ops engine. Detail expansion available on venue drill-down.",
            "owner": random.choice(["Venue GM", "Brand COO", "Group Operations"]),
            "raised_at": (END_DATE - timedelta(days=random.randint(2, 30))).isoformat(),
            "status": random.choice(["Open", "Investigating"]),
        })
        alert_id += 1

    return alerts


# ============================================================
# 13. GUEST INTERACTIONS (notes, complaints, preferences)
# ============================================================

def generate_guest_interactions(guests):
    """~3000 service notes — preferences captured, complaints, compliments."""
    interactions = []
    int_id = 1
    high_tier = [g for g in guests if g["guest_tier"] in ("Diamond", "Platinum", "Gold")]

    interaction_types = [
        ("Preference noted", "Always orders Krug Grande Cuvée; flag pre-arrival.", "Beverage", "Server"),
        ("Preference noted", "Prefers banquette by window; not near speakers.", "Seating", "Host"),
        ("Compliment", "Praised pastry chef on lemon tart; mention by name on next visit.", "F&B", "Server"),
        ("Complaint resolved", "Sound level too high during dinner; service comp offered, accepted.", "Service", "GM"),
        ("Complaint unresolved", "Reservation honored 25 min late; expressed dissatisfaction.", "Service", "Host"),
        ("Family note", "Daughter Layla, age 12 (as of 2026); birthday Aug 14.", "Family", "Server"),
        ("Family note", "Wife Priya; allergic to shellfish.", "Family", "GM"),
        ("Occasion", "Hosted 25th anniversary; partner = Mrs. Al Mansouri.", "Occasion", "Events"),
        ("Preference noted", "Allergic to truffle.", "Dietary", "Chef"),
        ("Compliment", "Praised wine pairing recommended by sommelier.", "Beverage", "Sommelier"),
    ]

    for _ in range(3000):
        guest = random.choice(high_tier)
        venue = random.choice(VENUES)
        int_type, note, category, source = random.choice(interaction_types)
        interaction_date = END_DATE - timedelta(days=random.randint(1, 800))
        interactions.append({
            "interaction_id": f"I-{int_id:06d}",
            "guest_id": guest["guest_id"],
            "venue_id": venue[0],
            "interaction_date": interaction_date.isoformat(),
            "interaction_type": int_type,
            "category": category,
            "note": note,
            "captured_by": source,
        })
        int_id += 1
    return interactions


# ============================================================
# 14. DISH MASTER (signature dishes)
# ============================================================

def generate_dishes():
    """~400 dishes across venues, with margin/velocity engineered."""
    dishes = []
    dish_id = 1
    brand_dishes = {
        "Nammos": [
            ("Mediterranean Sea Bass Carpaccio", 240, 0.31, True),
            ("Wagyu Ribeye 400g", 680, 0.36, True),
            ("Lobster Linguine", 320, 0.34, True),
            ("Greek Octopus Carbonara", 220, 0.30, False),
            ("Truffle Pizza", 280, 0.33, False),
            ("Tuna Tartare", 180, 0.29, True),
            ("Spicy Crab Sushi", 165, 0.30, False),
            ("Prawn Tempura", 145, 0.30, False),
            ("Nammos Signature Salad", 95, 0.20, True),
            ("Greek Yogurt with Honey", 65, 0.18, False),
        ],
        "Em Sherif": [
            ("Hummus Beiruti", 45, 0.20, True),
            ("Kibbeh Nayyeh", 95, 0.30, True),
            ("Mixed Mezze Platter", 180, 0.25, True),
            ("Charcoal Lamb Chops", 240, 0.34, True),
            ("Fattoush with Aubergine", 65, 0.18, False),
            ("Moudardara", 55, 0.16, False),
            ("Mouhallabieh", 45, 0.15, True),
            ("Set Menu 30 dishes", 580, 0.28, True),
            ("Sea Bream Whole", 280, 0.32, False),
            ("Manakish Wood-Fired", 35, 0.18, False),
        ],
        "CE LA VI": [
            ("A4 Miyazaki Wagyu Tataki", 320, 0.36, True),
            ("Black Truffle Sushi Rice Okayu", 280, 0.34, True),
            ("Modern Asian 5-Course Degustation", 480, 0.32, True),
            ("Slow-Cooked Pork Chop Yuzu", 220, 0.30, False),
            ("Coffee-Glazed BBQ Pork Belly", 195, 0.29, False),
            ("Chicken Laksa Spring Roll", 95, 0.26, False),
            ("Dulce Miso Toffee Pudding", 85, 0.20, True),
            ("Signature Cocktail Pour", 110, 0.18, True),
        ],
        "AlphaMind": [
            ("CLAP Omakase", 580, 0.32, True),
            ("Sucre Fire Steak", 420, 0.34, True),
            ("Babylon Mixed Mezze", 195, 0.26, True),
            ("Bar Du Port Riviera Plateau", 380, 0.30, True),
            ("CLAP Sashimi Selection", 280, 0.32, False),
        ],
        "Other ADMO": [
            ("Greek Whole Fish", 220, 0.31, True),
            ("Surf Ceviche", 145, 0.28, False),
        ],
    }
    for v in VENUES:
        vid, brand, sub, city, country, region, vtype, open_str, cap, ccy = v
        brand_menu = brand_dishes.get(brand, brand_dishes["Other ADMO"])
        for dish_name, price_aed, food_cost_pct, signature in brand_menu:
            dishes.append({
                "dish_id": f"D-{dish_id:04d}",
                "venue_id": vid,
                "dish_name": dish_name,
                "price_aed": price_aed,
                "food_cost_pct": food_cost_pct,
                "margin_aed": round(price_aed * (1 - food_cost_pct), 2),
                "signature_flag": "Yes" if signature else "No",
                "category": random.choice(["Starter", "Main", "Dessert", "Beverage"]),
            })
            dish_id += 1
    return dishes


# ============================================================
# 15. FX RATES (snapshot table)
# ============================================================

def generate_fx_rates():
    rates = []
    for ccy, rate in FX_TO_AED.items():
        rates.append({
            "currency": ccy,
            "rate_to_aed": rate,
            "as_of_date": END_DATE.isoformat(),
            "source": "Snapshot — demo only",
        })
    return rates


# ============================================================
# 16. BRAND EXPOSURE CALENDAR
# ============================================================

def generate_brand_exposure():
    events = [
        ("BX-001", "V-001", "2026-03-01", "2026-05-31", "Dior Dioriviera Partnership", "Partnership", "High", "+18% revenue lift confirmed"),
        ("BX-002", "V-001", "2025-12-05", "2025-12-08", "Abu Dhabi GP Weekend", "Major Event", "Maximum", "+45% bookings"),
        ("BX-003", "V-008", "2026-02-15", "2026-02-22", "Em Sherif Art Foundation London Opening", "Brand Activation", "High", "PR push planned"),
        ("BX-004", "V-002", "2026-06-15", "2026-09-15", "Mykonos High Season", "Seasonal", "Maximum", "Annual peak"),
        ("BX-005", "V-006", "2026-04-01", "2026-04-30", "Nammos Maldives Opening", "Launch", "Maximum", "Global press coverage"),
        ("BX-006", "V-003", "2025-07-01", "2025-08-31", "Nammos Mayfair Soft Opening Run", "Launch", "Maximum", "London press cycle"),
        ("BX-007", "V-020", "2025-09-01", "2025-10-31", "CE LA VI London Opening", "Launch", "High", "Press preview cycle"),
        ("BX-008", "V-023", "2025-06-01", "2025-09-30", "CLAP HOUSE Ibiza Inaugural Summer", "Launch", "High", "Ibiza season exposure"),
        ("BX-009", "V-001", "2026-02-17", "2026-03-19", "Ramadan Period", "Cultural", "Medium", "Iftar bookings spike"),
        ("BX-010", "V-027", "2025-12-05", "2025-12-08", "F1 Yas Marina", "Major Event", "Maximum", "+50% expected"),
    ]
    rows = []
    for e in events:
        rows.append({
            "exposure_id": e[0],
            "venue_id": e[1],
            "start_date": e[2],
            "end_date": e[3],
            "name": e[4],
            "type": e[5],
            "exposure_level": e[6],
            "notes": e[7],
        })
    return rows


# ============================================================
# WRITE OUT
# ============================================================

def write_csv(filename, rows, fieldnames):
    path = OUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {filename}: {len(rows):,} rows")


def main():
    print("=" * 60)
    print("ADMO Lifestyle — Synthetic Data Generator")
    print("=" * 60)

    print("\n1. Generating venue master...")
    venue_rows = [{
        "venue_id": v[0], "brand": v[1], "sub_brand": v[2], "city": v[3],
        "country": v[4], "region": v[5], "venue_type": v[6],
        "open_date": v[7], "seat_capacity": v[8], "local_currency": v[9],
    } for v in VENUES]
    write_csv("venue_master.csv", venue_rows,
              ["venue_id", "brand", "sub_brand", "city", "country", "region",
               "venue_type", "open_date", "seat_capacity", "local_currency"])

    print("\n2. Generating guest master (5,000 guests)...")
    guests = generate_guests(5000)
    write_csv("guest_master.csv", guests, list(guests[0].keys()))

    print("\n3. Generating transactions (~50,000)...")
    transactions = generate_transactions(guests)
    write_csv("transactions.csv", transactions, list(transactions[0].keys()))

    print("\n4. Generating daily ops metrics...")
    daily_ops = generate_daily_ops(transactions)
    write_csv("daily_ops_metrics.csv", daily_ops, list(daily_ops[0].keys()))

    print("\n5. Generating vendor master...")
    vendor_rows = [{
        "vendor_id": v[0], "vendor_name": v[1], "category": v[2],
        "signature_flag": "Yes" if v[3] else "No",
        "on_time_delivery_pct": v[4], "quality_score": v[5], "risk_flag": v[6],
    } for v in VENDORS]
    write_csv("vendor_master.csv", vendor_rows,
              ["vendor_id", "vendor_name", "category", "signature_flag",
               "on_time_delivery_pct", "quality_score", "risk_flag"])

    print("\n6. Generating venue-vendor map...")
    vv_map = venue_vendor_map()
    write_csv("venue_vendor_map.csv", vv_map, ["mapping_id", "vendor_id", "venue_id"])

    print("\n7. Generating events / bookings...")
    events = generate_events(guests, transactions)
    write_csv("events_bookings.csv", events, list(events[0].keys()))

    print("\n8. Generating hiring pipeline...")
    hiring = generate_hiring()
    write_csv("hiring_pipeline.csv", hiring, list(hiring[0].keys()))

    print("\n9. Generating plan targets...")
    targets = generate_plan_targets()
    write_csv("plan_targets.csv", targets, list(targets[0].keys()))

    print("\n10. Generating reservations (forward 30 days)...")
    reservations = generate_reservations_today(guests)
    write_csv("reservations_today.csv", reservations, list(reservations[0].keys()))

    print("\n11. Generating VIP flags...")
    vip_flags = generate_vip_flags(guests)
    write_csv("vip_flags.csv", vip_flags, list(vip_flags[0].keys()))

    print("\n12. Generating alerts feed...")
    alerts = generate_alerts(daily_ops, vendor_rows, hiring)
    write_csv("alerts_feed.csv", alerts, list(alerts[0].keys()))

    print("\n13. Generating guest interactions (Butler's Notebook)...")
    interactions = generate_guest_interactions(guests)
    write_csv("guest_interactions.csv", interactions, list(interactions[0].keys()))

    print("\n14. Generating dish master...")
    dishes = generate_dishes()
    write_csv("dish_master.csv", dishes, list(dishes[0].keys()))

    print("\n15. Generating FX rates...")
    fx = generate_fx_rates()
    write_csv("fx_rates.csv", fx, list(fx[0].keys()))

    print("\n16. Generating brand exposure calendar...")
    exposure = generate_brand_exposure()
    write_csv("brand_exposure_calendar.csv", exposure, list(exposure[0].keys()))

    # ============================================================
    # SANITY CHECKS
    # ============================================================
    print("\n" + "=" * 60)
    print("SANITY CHECKS")
    print("=" * 60)

    # Nammos Dubai 2024 revenue (target ~$71M = ~AED 260M)
    nammos_dubai_2024 = sum(
        t["total_revenue_aed"] for t in transactions
        if t["venue_id"] == "V-001" and t["transaction_date"].startswith("2025")
    )
    print(f"\n  Nammos Dubai 2025 revenue (AED): {nammos_dubai_2024:,.0f}")
    print(f"  Nammos Dubai 2025 revenue (USD): {nammos_dubai_2024 / 3.67:,.0f}")
    print(f"  Target USD: ~$71M")

    # Multi-brand guest revenue share
    multi_brand_guests = {g["guest_id"] for g in guests if g["brands_visited_count"] >= 2}
    total_guest_rev = sum(t["total_revenue_aed"] for t in transactions if t["guest_id"])
    multi_rev = sum(t["total_revenue_aed"] for t in transactions if t["guest_id"] in multi_brand_guests)
    multi_pct_of_base = len(multi_brand_guests) / len(guests) * 100
    multi_pct_of_rev = multi_rev / total_guest_rev * 100 if total_guest_rev > 0 else 0
    print(f"\n  Multi-brand guests: {len(multi_brand_guests):,} ({multi_pct_of_base:.1f}% of base)")
    print(f"  Multi-brand share of revenue: {multi_pct_of_rev:.1f}%")
    print(f"  Target: ~30% of base, ~50%+ of revenue (engineered)")

    # Total revenue across portfolio
    total_rev = sum(t["total_revenue_aed"] for t in transactions)
    print(f"\n  Total portfolio revenue (18 months, AED): {total_rev:,.0f}")
    print(f"  Total transactions: {len(transactions):,}")

    print("\n" + "=" * 60)
    print("DONE. Output written to ./data/")
    print("=" * 60)


if __name__ == "__main__":
    main()
