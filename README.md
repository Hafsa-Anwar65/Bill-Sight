# Billsight

See what your electricity bill really charges, verified line by line.

Upload a photo of a Pakistani electricity bill (K-Electric, IESCO, LESCO and other DISCOs) and get:

- every charge and tax line, read from the bill and classified,
- proof that the reading is correct: the lines are added up and compared with the totals printed on the bill,
- the 12 WTQ Level-2 questions answered from the bill's own numbers,
- a usage chart, a free-form "ask anything" box (English, Urdu or Roman Urdu),
- `level1.csv` and `level2.csv` in the WTQ submission format, for one bill or a whole folder.
- "What this bill tells you": factual tips such as the late fee you avoid, peak vs off-peak cost, arrears, subsidy and next month's forecast.
- A due-date calendar reminder (.ics), a printable report, copy buttons, recent bills, light and dark themes.
- Upload a photo, scan or PDF, or paste a screenshot with Ctrl + V.
- Optional user accounts: sign up, and every bill you analyse is saved to "My bills" with a payable trend. Guests can still use everything without an account.

## How accuracy is achieved

| Step | What happens | Where |
| --- | --- | --- |
| 1. Read | Gemini vision reads the bill into a strict JSON schema (temperature 0, seed 42). The prompt has layout rules for KE and WAPDA bills and tells the model to ignore handwriting and stamps. | `backend/app/prompts.py`, `extract.py` |
| 2. Normalize | Python re-parses every date and month, re-classifies each line from its printed label, fixes subsidy signs and rebuilds the usage history. | `normalize.py` |
| 3. Verify | Up to 8 arithmetic checks: lines vs printed totals, charges + taxes = current bill, charges + taxes + arrears = payable, units = meter readings, late tiers, history continuity. | `validate.py` |
| 4. Retry | If a check fails, the bill is read again with the failed checks as feedback. The best attempt is kept. | `extract.py` |
| 6. Guard | Free-form chat answers are scanned for numbers; any number not found in the bill data triggers a corrected answer. | `service.py` |
| 5. Answer | The 12 questions are answered with pandas, not by the language model, so every number is computed and every answer states its months and method. | `analysis.py` |

The language model is only used to read the image (step 1) and for the optional free-form question box.

## Setup (Windows PowerShell)

```powershell
cd bill-decoder
copy .env.example .env          # then put your GEMINI_API_KEY in .env

cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest                 # 89 tests, no API key needed
```

## Run the web app

The built frontend is already in `frontend/dist`, so one command serves everything:

```powershell
cd backend
.venv\Scripts\activate
uvicorn app.api:app --port 8000
```

Open http://localhost:8000.

To work on the frontend with hot reload (needs Node.js), keep the backend running and in a second terminal:

```powershell
cd frontend
npm install
npm run dev                      # http://localhost:5173, /api is proxied to port 8000
npm run build                    # rebuilds frontend/dist
```

## Batch: generate the submission CSVs

Name each image by its bill ID (`IESCO_0002.jpg`, `KESC_0006.png`, ...) and put them in one folder.

```powershell
cd backend
python -m app.cli ..\bills --out ..\output --ids ..\level1_template.csv
```

- `--ids` is optional: a CSV with a `bill_id` column. Rows come out in that order, and missing images get an empty row.
- Output: `output/level1.csv` (`bill_id,json`), `output/level2.csv` (`bill_id,question_id,question,answer`, Q1 to Q12) and `output/report.json` with every check per bill.
- Results are cached by image hash in `backend/.cache`. Use `--no-cache` to force a fresh read.

The same export is available in the web app under **Batch export**.

## Level-1 JSON format

```json
{
  "provider": "IESCO",
  "bill_month": "2026-09",
  "charges": [{"type": "energy", "amount": 7711}, {"type": "subsidy", "amount": -1002}, {"type": "fpa", "amount": 599}],
  "taxes": [{"type": "other_tax", "amount": 1295}],
  "units_consumed": 177,
  "current_bill": 8004,
  "payable_within_due_date": 8603,
  "payable_after_due_date": 8939
}
```

- Charge types: `energy, fixed, fpa, quarterly_adjustment, surcharge, meter_rent, subsidy, other`.
- Tax types: `gst, electricity_duty, income_tax, municipal_tax, other_tax`. IESCO/LESCO summary bills print one combined "Taxes" line, so it is `other_tax`.
- `payable_after_due_date` is the first after-due-date amount. All tiers are in the full record and in answer Q4.

## How each Level-2 answer is computed

| Q | Method |
| --- | --- |
| 1 | Net-metered only if the bill prints export units or net metering; otherwise standard. |
| 2 | Highest units in the 12 months ending with this bill's month. |
| 3 | Sum of FPA/FCA lines plus the month they relate to (KE "FCA :Jul-26", IESCO yellow note). |
| 4 | Every printed late-payment tier: surcharge, date and total. |
| 5 | This month vs the same month a year earlier. |
| 6 | Average of the 12 months before this bill vs this month. |
| 7 | Latest full June–August vs latest full December–February: totals, per-month averages, difference. |
| 8 | Each history month with a billed amount: paid in full, partly, or not paid. KE prints 3 months of payments. |
| 9 | The last 3 months including this one: values and direction. |
| 10 | Seasonal forecast: next month last year × (this month ÷ same month last year), ratio capped to 0.5–2. |
| 11 | 12-month cost ÷ 12, using printed billed amounts and estimating months without one from units × this bill's average rate. |
| 12 | Fixed charge + this month's other charges and taxes scaled to last month's units. Last month's actual bill is quoted too. |

## Project structure

```
backend/
  app/
    api.py        FastAPI routes (/api/analyze, /api/ask, /api/export) and serves the frontend
    cli.py        batch mode
    service.py    pipeline shared by API and CLI
    extract.py    read -> normalize -> verify -> retry
    llm.py        Gemini client: deterministic settings, retries, image preparation
    prompts.py    extraction, retry and question prompts
    normalize.py  dates, months, line types, history repair
    validate.py   arithmetic checks
    analysis.py   the 12 answers and dashboard numbers (pandas)
    export.py     level1.csv / level2.csv
    schema.py     pydantic models
    cache.py      on-disk cache
    accounts.py   sign up / sign in, sessions, saved bills per user
    db.py         SQLite database (backend/data/billsight.db)
  tests/          89 tests; fixtures are hand-transcribed sample bills
frontend/         React + TypeScript (Vite), no UI library
```

## Accounts and privacy

- Accounts live in a local SQLite file, `backend/data/billsight.db` (ignored by git).
- Passwords are hashed with scrypt and a random salt. Sessions use a random token in an HttpOnly cookie; only its SHA-256 hash is stored.
- Each user can only list, open or delete their own bills. Bill images are never stored, only the extracted numbers.
- When serving over HTTPS, set `SECURE_COOKIES=1` in `.env`.

## AI usage

- **Model:** Google Gemini (`LLM_MODEL`, default `gemini-3.5-flash-lite`) via the `google-genai` SDK, with temperature 0, seed 42 and a JSON response schema.
- **Used for:** reading bill images, and answering optional free-form questions grounded in the extracted data.
- **Not used for:** the 12 Level-2 answers, totals or any arithmetic. These are deterministic Python.
- **Privacy:** names, addresses, CNIC, and reference, consumer or meter numbers are never extracted or stored.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| "GEMINI_API_KEY is not set" | Create `.env` in the project root (next to this README) and restart the server. |
| "Model ... was not found" | Set `LLM_MODEL` in `.env` to an exact model ID from Google AI Studio. |
| A check fails | Press **Read again** (skips the cache). Use a straight, well-lit photo of the full page. |
| Port 8000 busy | `uvicorn app.api:app --port 8001` (for `npm run dev`, also change the proxy in `vite.config.ts`). |
