# Care Intensity Engine

MVP scoring tool for Medicare insurance agents. Analyzes beneficiary health
context (chronic conditions, providers, medications) and returns a structured
Care Intensity Score with agent talking points.

## Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic API key (optional — scoring works without it, narrative requires it)

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then add your ANTHROPIC_API_KEY
python manage.py migrate
python manage.py seed_conditions
python manage.py seed_demographics
python manage.py load_providers   # loads ../data/sample_providers.csv
python manage.py load_medications # loads ../data/sample_medications.csv
python manage.py runserver
```

## Frontend Setup (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

## Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/conditions/` | List 13 chronic conditions |
| GET | `/api/providers/` | List providers |
| GET | `/api/medications/` | List medications |
| POST | `/api/score/` | Calculate care intensity score |

### POST /api/score/ Example

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

## Using Your Own Provider/Medication Data

Replace `data/sample_providers.csv` and `data/sample_medications.csv` with
your own CSVs, then re-run the load commands.

**Provider CSV format**: `name,specialty,npi`
**Medication CSV format**: `name,dosage,category,is_specialty`

## Scoring Approach

See `context/SCORING_RATIONALE.md` for the full scoring model including
CMS-HCC V28 alignment, condition weights, and design decisions.

## Ongoing Design Conversations

After discussing scoring design with Claude, save a dated file in
`context/conversations/`. CLAUDE.md instructs Claude to read these at
the start of each session.
