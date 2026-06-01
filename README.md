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
