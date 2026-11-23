# AFROEURO Daily Hub — live-data upgrade

## Upload to GitHub

Upload `index.html`, `data.json`, `update_feeds.py`, and `.github/workflows/update-feeds.yml` to the root of your `afroeuro-daily-hub` repository, preserving the `.github/workflows` folder structure.

In **Settings → Pages**, select **Deploy from a branch**, branch **main**, folder **/(root)**, then save. Your site should be `https://afroeurodaily.github.io/afroeuro-daily-hub/` (assuming the account is `afroeurodaily`). The root domain `https://afroeurodaily.github.io/` needs a repository named `afroeurodaily.github.io`.

In **Actions**, run **Update AFROEURO feeds** manually once. Scheduled runs are best-effort (approximately twice hourly; GitHub may delay them). Under **Settings → Actions → General**, ensure workflow permissions permit repository content writes. GitHub Pages deployment can take a few minutes.

## Data and limitations

- Currency: Frankfurter v2 reference exchange rates, fetched by the visitor's browser, no API key. Reference rates are not instant trading or remittance rates.
- Football: ESPN site-facing, undocumented endpoints fetched by GitHub Actions. Availability, coverage, and permitted usage may change; review ESPN terms before commercial publication. If ESPN blocks the request, the last successful feed is retained.
- News: Google News RSS headlines linking to publishers. Confirm reuse and attribution requirements before commercial launch.
- Admin panel: the original Python server and `/api/content` are **not** deployed on GitHub Pages; static pages cannot run Python. The page keeps the community-update placeholder. A separately hosted backend is required for publishing from an admin panel.
- The first upload has empty `data.json`; run the workflow to populate it.
- Before public launch add a legal notice/Impressum, privacy policy, contact details, and appropriate disclosures.
