# Villa Warner #48 — Listing Landing Page

Single-page, mobile-first landing site for **6600 Warner Ave #48, Huntington Beach, CA 92647**.
This is the scan target for the printed flyer's QR code.

Plain static site — `index.html` + `styles.css` + `script.js`, no build step, no framework.

## Local preview

Any static server works, e.g.:

```bash
python3 -m http.server 4321
# then open http://localhost:4321
```

## Before going live — two edits

### 1. Wire up the form email (required)

The "Ask a Question" contact form posts to **Web3Forms** so submissions email
**matthewn@sevengables.com** (the point-of-contact agent).

1. Go to <https://web3forms.com>, create a free Access Key pointed at `matthewn@sevengables.com`.
2. In `index.html`, find:
   ```html
   <input type="hidden" name="access_key" value="YOUR_WEB3FORMS_KEY" />
   ```
   and paste the key in place of `YOUR_WEB3FORMS_KEY`.
3. Deploy, then submit a test from the live page and confirm Matthew receives it.

> Alternative: swap the form `action` to Formspree (`https://formspree.io/f/XXXX`). The JS
> already handles the JSON success/error response either backend returns.

### 2. Update the mortgage rates (they change often)

In `index.html`, the **Financing** section is marked with
`<!-- EDIT RATES HERE -->`. Edit the values inside the `data-rate="…"` spans:

| Field            | `data-rate`      |
|------------------|------------------|
| As-of date       | `asof`           |
| 15 Yr Fixed      | `15yr` / `15yr-apr` |
| 30 Yr Fixed      | `30yr` / `30yr-apr` |
| 30 Yr FHA        | `30yr-fha` / `30yr-fha-apr` |
| 30 Yr VA         | `30yr-va` / `30yr-va-apr` |

Also update "Rates effective …" and the rate-assumption dates in the compliance footer if needed.

> **Note:** rate editing is now mostly automatic — see below.

## Automatic rate updates (GitHub Action + Airtable)

A GitHub Actions workflow (`.github/workflows/update-rates.yml`) pulls the latest
mortgage rates from the Seven Gables **Airtable** and bakes them into the HTML, so
the token stays server-side and **never appears in the published page**.

- **Source:** base **"Interest Rates"** → table **"From Kevin"** (`appxtXl28vrEIHz0Z` / `tblVrlngw97M9CA5j`), latest row by `Timestamp`. Rates are stored as decimals (`0.0575` = 5.75%); the script converts them. The `display date` field drives the "As of" / "Rates effective" / assumptions dates. (These rates change ~weekly.)
- **When:** every 15 minutes (`*/15 * * * *`), best-effort — GitHub's scheduled triggers can run late. Most runs are no-ops; it only commits when a value actually changed. You can also run it on demand: Actions tab → "Update mortgage rates" → *Run workflow*.
- **What it updates:** the four rates + APRs and the dates — only `data-rate="…"` elements in `index.html`. Fixed corporate legal text is never touched.
- **Liveness heartbeat:** the footer's "last verified [date]" line (`data-rate="checked"`) is set to today's Pacific date **only on a successful pull**, so it advances daily while the automation is healthy. A stale date there = something's broken. This is separate from the legal rate "As of" date, which always reflects the actual Airtable `display date` (never today's date) so rate effective dates aren't misrepresented.
- **How:** `scripts/update_rates.py` fetches Airtable, validates, patches `index.html`, commits, and Render auto-deploys the push.
- **Fail-safe:** if Airtable can't be reached, a value is missing, or a rate is out of range (1–15%, APR ≥ rate), the script exits without writing — the site keeps the last good values and GitHub emails you about the failed run.

### Token setup (required)

The token is stored as an encrypted **GitHub Actions secret** named `AIRTABLE_TOKEN`
— it is never committed or shipped to the browser.

1. Airtable → **Builder Hub → Personal access tokens → Create token**. Scope: **`data.records:read`**; access: **only the "Interest Rates" base**.
2. Repo → **Settings → Secrets and variables → Actions → New repository secret**, name `AIRTABLE_TOKEN`, paste the token. (Or `gh secret set AIRTABLE_TOKEN`.)
3. **Revoke** any broad/edit token that was shared previously.

To change rates by hand instead, edit the `data-rate="…"` values in `index.html`.

## Deploy to Render (static site)

1. `git init`, commit, push to a new GitHub repo.
2. Render → **New → Static Site** → connect the repo.
3. **Build command:** leave empty. **Publish directory:** `.` (repo root, where `index.html` lives).
   (A `render.yaml` is included so Render can auto-configure too.)
4. Deploy. Note the live URL, e.g. `https://villa-warner-48.onrender.com`.
   Optionally add a custom domain in Render → Settings.
5. Re-point the flyer's QR code to the live URL.

## Contacts

- **Contact agent (all buyer inquiries):** Matthew Nowotny, Real Estate Advisor — Seven Gables Real Estate — (657) 342-0611 — matthewn@sevengables.com
- **Lender (informational only):** Brett Hickman — Home First Financial — (949) 350-8005 — brett.hickman@yourhomefirst.com
