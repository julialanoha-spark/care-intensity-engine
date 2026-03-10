# Care Intensity Engine — Project Context

This is a Medicare insurance agent decision-support tool. It calculates a
Care Intensity Score (0–100) for a simulated beneficiary profile, then
generates actionable talking points for use on live calls.

## CRITICAL: Read Before Modifying Scoring Logic

Before making any changes to scoring weights, condition tiers, or demographic
factors, read:

- `context/SCORING_RATIONALE.md` — scoring weights, HCC alignment, and design decisions
- `context/conversations/` — dated logs of past scoring design discussions

The scoring model is grounded in CMS-HCC V28 (CY 2024). Changes should be
documented in `context/SCORING_RATIONALE.md` under the Change Log section.

## Architecture

| Layer | Location | Details |
|---|---|---|
| Backend | `backend/` | Django 5.1 + DRF, SQLite |
| Scoring engine | `backend/care_engine/scoring.py` | Pure Python, deterministic |
| Scoring context | `backend/care_engine/discussion_topics.py` | Rule-based plan topics |
| LLM narrative | `backend/care_engine/llm.py` | Claude API (haiku), narrative only |
| Frontend | `frontend/` | Vue 3 + Vite + Pinia |
| Reference data | `data/` | Sample CSVs for providers + medications |

## Scoring Summary (current weights)

```
Score = Demographic (0-15) + Conditions (0-35) + Providers (0-25) + Medications (0-25) + Interactions (0-10)
Max theoretical: 110 → capped at 100
```

### Intensity Levels
- 0–24: Low
- 25–49: Moderate
- 50–74: High
- 75–100: Very High

See `context/SCORING_RATIONALE.md` for full weight tables and HCC references.

## Quick Start

```bash
# Backend
cd backend && source venv/bin/activate
python manage.py runserver

# Frontend
cd frontend && npm run dev
# http://localhost:5173
```

## Adding a Scoring Conversation

After a scoring design discussion with Claude, save a new file:
`context/conversations/YYYY-MM-DD-<topic>.md`

Use the template in `context/SCORING_RATIONALE.md` Change Log section.

## Open Design Questions

See `context/SCORING_RATIONALE.md` — Open Questions section.
