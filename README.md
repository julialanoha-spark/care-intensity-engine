# Medicare Plan Decision Support

A decision-support tool for Medicare insurance agents. Enter a beneficiary's health profile — chronic conditions, providers, and medications — and get an instant Care Intensity Score alongside a live plan browser with AI-generated talking points tailored to the selected plan.

## What It Does

**Care Intensity Score** — A 0–100 score (Low / Moderate / High / Very High) calculated from the beneficiary's demographic profile, chronic conditions, provider specialties, medications, and comorbidity interactions. Grounded in CMS-HCC V28 (CY 2024). Updates in real time as the agent fills in the profile.

**Plan Browser** — Enter a 5-digit ZIP code to auto-load all MA plans available in that market. Search, filter by star rating, carrier, plan type (HMO/PPO/HMO-POS), and SNP type (C-SNP, D-SNP). Each plan card shows premium, PCP copay, specialist copay, medical deductible, Rx deductible, and MOOP.

**AI Reasoning** — Select any plan to generate GPT-4o talking points specific to that beneficiary's profile and that plan's benefits. Reasoning updates automatically when the beneficiary profile changes. Flags D-SNP eligibility mismatches when the beneficiary is not Medicaid dual-eligible.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Django 5.1 + Django REST Framework, SQLite |
| Scoring engine | Pure Python — `backend/care_engine/scoring.py` |
| Plan data | SQLite (`plan_fit_2026.db`) — 8,081 MA plans |
| LLM reasoning | OpenAI GPT-4o via `/api/reasoning/` |
| Frontend | Vue 3 + Vite + Pinia |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key (score works without it; plan reasoning requires it)

---

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add OPENAI_API_KEY
python manage.py migrate
python manage.py seed_conditions
python manage.py seed_demographics
python manage.py load_providers     # loads ../data/providers_real.csv
python manage.py load_medications   # loads ../data/meds_real.csv
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/conditions/` | List 13 chronic conditions |
| GET | `/api/providers/` | List providers with specialty tiers |
| GET | `/api/medications/` | List medications |
| GET | `/api/plans/?zip=XXXXX` | Load MA plans by ZIP code |
| GET | `/api/plans/?search=...&zip=XXXXX` | Search plans by name + market |
| POST | `/api/score/` | Calculate care intensity score (fast, no LLM) |
| POST | `/api/reasoning/` | Generate plan-specific talking points (GPT-4o) |

### POST /api/score/

```json
{
  "age_band": "75_80",
  "sex": "female",
  "medicaid_dual": false,
  "condition_ids": [1, 3],
  "cancer_severity": "active",
  "provider_ids": [2, 5],
  "medication_ids": [4, 8, 12]
}
```

### POST /api/reasoning/

Same payload as `/api/score/`, plus the selected plan identifiers:

```json
{
  "age_band": "75_80",
  "sex": "female",
  "medicaid_dual": false,
  "condition_ids": [1, 3],
  "cancer_severity": "active",
  "provider_ids": [2, 5],
  "medication_ids": [4, 8, 12],
  "plan_contract_id": "H1234",
  "plan_plan_id": "001",
  "plan_segment_id": "0"
}
```

---

## Scoring Model

```
Score = Demographic (0–15) + Conditions (0–35) + Providers (0–25)
      + Medications (0–25) + Comorbidity Interactions (0–10)
Theoretical max: 110 → capped at 100
```

| Range | Intensity |
|---|---|
| 0–24 | Low |
| 25–49 | Moderate |
| 50–74 | High |
| 75–100 | Very High |

Providers and medications act as additive complexity signals — adding care data never decreases the score. See `context/SCORING_RATIONALE.md` for full weight tables, CMS-HCC V28 alignment, and design decisions.

---

## Provider / Medication Data

Replace `data/providers_real.csv` and `data/meds_real.csv` with your own CSVs, then re-run the load commands.

**Provider CSV columns**: `name, specialty, npi`
**Medication CSV columns**: `name, dosage, category, is_specialty`

---

## Scoring Design Context

After discussing scoring changes with Claude, save a dated log in `context/conversations/`. `CLAUDE.md` instructs Claude to read `context/SCORING_RATIONALE.md` and these logs before touching any scoring logic.
