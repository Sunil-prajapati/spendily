# Spec: Date Filter for Profile Page

## Overview
Add a date-range filter to the `/profile` page so the signed-in user can narrow the expense
summary (count and total spent) and the "Spending by Category" breakdown to a chosen period.
The filter is driven by `from` and `to` query parameters (`YYYY-MM-DD`) submitted from a
small GET form on the profile page, with quick-select presets (This Month, Last 30 Days,
All Time) and a Clear action. This builds on the profile page from Step 04 and gives users
a first way to slice their data before the expense list and edit/delete steps arrive.

## Depends on
- Step 01 — Database Setup (`expenses.date` stored as `YYYY-MM-DD` text)
- Step 03 — Login Feature (`session['user_id']`, `login_required`)
- Step 04 — Profile Page and Backend Connectivity (`get_expense_summary`,
  `get_category_breakdown`, `profile.html`)

## Routes
- `GET /profile` — now accepts optional `from` and `to` query params and returns the
  summary and category breakdown filtered to that inclusive date range — logged-in
  (existing route; no new routes)

No other new routes.

## Database changes
No new tables or columns. Modify two existing functions in `database/db.py` to accept
optional bounds (default `None` = no bound, preserving current behaviour):

- `get_expense_summary(user_id, date_from=None, date_to=None)`
- `get_category_breakdown(user_id, date_from=None, date_to=None)`

Both append `AND date >= ?` / `AND date <= ?` clauses only when the bound is provided,
building the SQL from fixed string fragments and passing values as `?` parameters (never
interpolating user input). Dates are `YYYY-MM-DD` text, so string comparison is correct.

## Templates
- **Create:** none
- **Modify:** `templates/profile.html` — add a filter card above the stats containing a
  GET form (`action` via `url_for('profile')`) with `from` and `to` `<input type="date">`
  fields pre-filled with the active values, an "Apply" button, preset links (This Month,
  Last 30 Days, All Time) built with `url_for('profile', ...)`, and a "Clear" link. Show an
  inline error message when the range is invalid, and label the stats/breakdown with the
  active range (e.g. "1 Oct 2026 – 16 Oct 2026" or "All time"). The empty-state text for
  the breakdown should read "No expenses in this period." when a filter is active.

## Files to change
- `database/db.py` — add optional date bounds to the two query functions
- `app.py` — parse/validate `from` and `to` in `profile()`, compute preset ranges, pass
  bounds to the DB functions and the active range/error to the template
- `templates/profile.html` — filter UI and active-range label
- `static/css/style.css` — styles for the filter card, inputs, preset links (CSS variables
  only)

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never f-strings with user input in SQL
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic stays in `database/db.py`; `profile()` only parses params, calls helpers, renders
- Validate `from`/`to` with `datetime.strptime(value, "%Y-%m-%d")`; an unparseable value is
  ignored and an error message is shown — never a 500
- If `from` is later than `to`, show an error and fall back to the unfiltered view
- Both bounds are inclusive; either may be supplied alone
- Preset ranges are computed server-side from `date.today()`; use `url_for()` for every
  link — no hardcoded URLs
- Keep `login_required` on `/profile`; the filter only ever applies to `session["user_id"]`
- Keep the existing `₹` currency formatting used in `app.py`
- No inline `<style>` tags; no JS required (form works without JavaScript)

## Definition of done
- [ ] `/profile` with no params shows the same totals and breakdown as before (all expenses)
- [ ] Submitting the form with `from=2026-10-05` and `to=2026-10-10` for the demo account
      shows 3 expenses totalling ₹137.00 and a breakdown containing only Transport, Bills
      and Health
- [ ] Supplying only `from` or only `to` filters with a single open-ended bound
- [ ] The date inputs stay pre-filled with the active range after applying the filter
- [ ] "This Month", "Last 30 Days" and "All Time" presets each load the correct range
- [ ] "Clear" returns to the unfiltered view
- [ ] A range with no expenses shows 0 expenses, ₹0.00 and "No expenses in this period."
- [ ] `from` later than `to` shows an error message and the unfiltered data
- [ ] `?from=garbage` shows an error message and does not raise a 500
- [ ] A SQL-injection attempt such as `?from=' OR 1=1 --` does not change results or error
- [ ] Visiting `/profile?from=...` while logged out still redirects to `/login`
- [ ] The filter card uses only CSS variables from `static/css/style.css` — no hex colors
