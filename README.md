# Restaurant Review Intelligence — GTA Restaurant MVP

A portfolio-ready MVP that turns restaurant customer reviews into operational intelligence.

## Included

- 30-day restaurant health overview
- Restaurant-specific multi-label issue taxonomy
- Category + sentiment + rating + text review explorer
- Menu-item intelligence
- Period-over-period complaint alerts
- Weekly owner report
- Optional OpenAI owner brief
- GitHub Pages front end
- GitHub Actions weekly pipeline
- Synthetic demo dataset so it works immediately

## Run locally

```bash
python3 scripts/pipeline.py
python3 -m http.server 8000
```

Open `http://localhost:8000`.

The project initially reads `data/sample_reviews.csv`.

## Use your own review file

Create `data/reviews.csv` with these columns:

```text
review_id,business,location,review_date,rating,review,source,author
```

Then run:

```bash
python3 scripts/pipeline.py
```

## Deploy on GitHub Pages

1. Create a repo and upload the entire contents, including the hidden `.github` folder.
2. Settings → Pages → Deploy from branch → `main` → `/ (root)`.
3. Settings → Actions → General → Workflow permissions → Read and write.
4. Actions → `Restaurant review intelligence` → Run workflow.

## Optional AI owner brief

The project works without OpenAI. To enable it, add a GitHub Actions secret:

`OPENAI_API_KEY`

Optional repository variable:

`OPENAI_MODEL`

The deterministic analytics remain the source of truth; the AI only summarizes structured evidence.

## Google data: what to use

### Public Google Places API (demo only)

`scripts/import_google_places.py` is included for a quick public demo.

```bash
export GOOGLE_MAPS_API_KEY="..."
export GOOGLE_PLACE_ID="..."
python3 scripts/import_google_places.py
python3 scripts/pipeline.py
```

Google Place Details currently returns at most 5 reviews for a place, so this is not enough for full historical restaurant intelligence.

### Real customer onboarding

For a production service, use the Google Business Profile API with the restaurant owner's authorization for locations they manage. Build OAuth onboarding before commercial deployment.

For early pilots, use the synthetic dataset or a customer-provided/approved review export, then add Business Profile OAuth once pilot demand is validated.

## Recommended sales demo

Show the owner:

1. What customers love
2. What is hurting ratings
3. Which issue is increasing fastest
4. Which dishes receive the best/worst feedback
5. The exact reviews behind each insight
6. A one-page weekly action brief

Position it as **restaurant operational intelligence**, not generic sentiment analysis.

## Next production upgrades

- Google Business Profile OAuth onboarding
- Multi-tenant database for restaurants and locations
- Scheduled ingestion per location
- Stronger aspect-level AI/embedding classifier
- Competitor benchmarking
- Email delivery of weekly reports
- AI response drafting with owner approval
- Authentication and subscriptions only after pilot validation
