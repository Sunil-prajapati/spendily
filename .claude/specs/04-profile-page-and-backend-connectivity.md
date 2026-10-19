# Spec: Profile Page and Backend Connectivity

## Overview
Replace the `/profile` stub with a real page that shows the signed-in user's account
details sourced live from the database — name, email, and member-since date — plus a
simple expense summary (total number of expenses logged and total amount spent). This
is the first authenticated page in Spendly that reads beyond the `users` table, proving
out the pattern (query `database/db.py`, pass real rows into a template) that the
upcoming expense-listing and dashboard steps will build on.

## Depends on
- Step 01 — Database Setup (`users` and `expenses` tables must exist)
- Step 02 — Registration (a user account must exist)
- Step 03 — Login Feature (`session['user_id']`, `login_required`, conditional navbar)

## Routes
- `GET /profile` — render the signed-in user's profile with account details and
  expense summary stats — logged-in (already decorated with `login_required`; only the
  stub body changes)

No other new routes.

## Database changes
No new tables or columns. Add one new query function to `database/db.py`:

- `get_expense_summary(user_id)` — returns a `sqlite3.Row` (or dict-like) with the
  signed-in user's expense count and total amount spent, or zeros if they have none
  ```sql
  SELECT COUNT(*) AS expense_count, COALESCE(SUM(amount), 0) AS total_spent
  FROM expenses
  WHERE user_id = ?
  ```

## Templates
- **Create:** `templates/profile.html` — extends `base.html`; shows the user's name,
  email, "Member since" date (formatted from `created_at`), and a small stats card with
  `expense_count` and `total_spent`
- **Modify:** `templates/base.html` — when `session.user_id` is set, add a "Profile"
  link (pointing to `/profile`) in `.nav-links` alongside the existing "Sign out" link

## Files to change
- `database/db.py` — add `get_expense_summary(user_id)`
- `app.py` — import `get_expense_summary`; replace the `/profile` stub body with a
  real `render_template` call that fetches the user (`get_user_by_id`) and their
  expense summary
- `templates/base.html` — add conditional "Profile" nav link for logged-in users

## Files to create
- `templates/profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `GET /profile` must never render raw string output — always `render_template`
- Do not expose `password_hash` to the template context or render it anywhere
- Reuse `get_user_by_id` (already defined) to fetch the profile owner — don't write a
  duplicate query
- `database/db.py` is the only place that talks to SQLite — no inline queries in `app.py`
- Keep `get_expense_summary` resilient to a user with zero expenses (must return 0 /
  0, not `None`, via `COALESCE`)

## Definition of done
- [ ] Logging in and visiting `/profile` shows the real name and email of the signed-in
      user (not placeholder text)
- [ ] The profile page shows a "Member since" date derived from `created_at`
- [ ] The profile page shows the correct expense count and total spent for the demo
      account (`demo@spendly.com` / `demo123`), matching the 8 seeded expenses
- [ ] A newly registered user with no expenses sees `0` expenses and `$0.00` total,
      not an error
- [ ] Visiting `/profile` while logged out redirects to `/login` (via existing
      `login_required`)
- [ ] The navbar shows a "Profile" link when logged in, in addition to "Sign out"
- [ ] No template renders `password_hash` anywhere in the page source
- [ ] `templates/profile.html` extends `base.html` and uses only CSS variables from
      `static/css/style.css` — no hardcoded hex colors
