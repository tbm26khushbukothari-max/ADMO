# ADMO Lifestyle Dashboard — Starter Kit

## What this is

Synthetic-data foundation for a Streamlit dashboard demonstrating ADMO Lifestyle Holding's group-level data architecture. Built as a working prototype to accompany an 8-slide strategic case submission.

## What's in the box

- `generate_admo_data.py` — One-shot data generator. Already executed; output is in `/data`.
- `/data` — 16 CSV files, ~270K transactions, ~5K guests, 30 real ADMO venues.

## Key calibration facts (do not break these)

- **Nammos Dubai 2025 revenue: USD $71.6M** — matches the real-world figure (world's #1 restaurant)
- **Multi-brand guests: 30% of base, 52% of revenue** — the cross-brand intelligence story
- **Engineered alerts:** 3 problem venues + 1 degrading signature vendor + 1 critical talent gap
- **Real ADMO venues only** — Nammos Dubai, Em Sherif Harrods, CÉ LA VI Singapore, Bar Du Port Yas Marina, etc.

## Data dictionary (high-level)

| File | Rows | Purpose |
|---|---|---|
| `venue_master.csv` | 30 | The actual ADMO portfolio |
| `guest_master.csv` | 5,000 | Guest identity + LTV + tier + consent |
| `transactions.csv` | 274,000 | All bookings, 18 months |
| `daily_ops_metrics.csv` | 14,000 | Daily venue rollup (covers, revenue, NPS, costs) |
| `vendor_master.csv` | 30 | Signature + commodity vendors |
| `venue_vendor_map.csv` | 300 | Many-to-many vendor-venue dependencies |
| `events_bookings.csv` | 467 | Weddings, private dining, corporate |
| `hiring_pipeline.csv` | 201 | Open + filled roles, criticality |
| `plan_targets.csv` | 520 | Monthly revenue/covers/NPS targets |
| `reservations_today.csv` | 1,450 | Forward 30-day reservations |
| `vip_flags.csv` | 40 | GROUP VIP overlay |
| `alerts_feed.csv` | 11 | Pre-generated exception alerts |
| `guest_interactions.csv` | 3,000 | Service notes — the Butler's Notebook source |
| `dish_master.csv` | 234 | Signature dishes per venue |
| `fx_rates.csv` | 11 | Currency conversion snapshot |
| `brand_exposure_calendar.csv` | 10 | Partnerships, launches, exposure events |

## Color palette (locked)

- Deep navy: `#0F1A2E`
- Gold accent: `#C9A961`
- Off-white: `#F7F4ED`
- Alert red: `#C84B31`
- Amber: `#D89B3F`
- Success green: `#5A7D3C`

## Next steps (in Claude Code)

1. `pip install streamlit pandas plotly streamlit-extras`
2. Build `app.py` with multi-page nav (5 pages: Morning Briefing, Group CEO, Brand Operations, Guest Intelligence, Operational Health)
3. Use `@st.cache_data` on every CSV load
4. Pre-aggregate `transactions.csv` to monthly per-venue summaries for fast dashboard loads
5. Deploy to Streamlit Community Cloud via GitHub repo
