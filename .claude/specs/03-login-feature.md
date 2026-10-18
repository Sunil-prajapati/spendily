# Spec: Login Feature

## Overview
Allow registered users to sign in to Spendly with their email and password, persist
their identity across requests using Flask's server-side session, and sign out on
demand. This step introduces `session`, a `login_required` guard, and a conditional
navbar — the security foundation every protected route in Steps 4–9 depends on.

## Depends on
- Step 01 — Database Setup (`users` table must exist)
- Step 02 — Registration (a user account must exist to sign in with)

## Routes
- `POST /login` — verify credentials, set `session['user_id']`, redirect to `/profile` — public
- `GET  /logout` — clear session, redirect to `/` — logged-in (safe to call when already logged out)

Note: `GET /login` already renders `login.html` — only the POST handler is new.

## Database changes
No new tables or columns. Add one new query function to `database/db.py`:

- `get_user_by_email(email)` — returns a `sqlite3.Row` for the matching user, or `None` if not found
  ```sql
  SELECT * FROM users WHERE email = ? LIMIT 1
  ```

## Templates
- **Modify:** `templates/base.html` — make the nav links conditional:
  - When `session.user_id` is set: show a "Sign out" link pointing to `/logout`; hide "Sign in" / "Get started"
  - When not logged in: show "Sign in" and "Get started" links (current default)
- **No new templates** — `templates/login.html` already has the form

## Files to change
- `database/db.py` — add `get_user_by_email(email)`
- `app.py` — add `session` to Flask imports; add POST handler to `/login`; implement `/logout`; add `login_required` decorator; import `get_user_by_email`
- `templates/base.html` — conditional nav based on session state

## Files to create
None.

## New dependencies
No new pip packages. Uses `flask.session` (built-in) and `werkzeug.security.check_password_hash` (already installed).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plain text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Store only `session['user_id']` (integer) — never store the password hash or full user object in the session
- `app.secret_key` must remain set (already present) for sessions to work
- The `login_required` decorator must redirect to `/login` with a flash message when the user is not authenticated
- `POST /login` must not leak whether the email or password was wrong — use a single generic error: "Invalid email or password."
- `/logout` uses `session.clear()` (not `session.pop`) to wipe all session data
- After login redirect to `/profile`; after logout redirect to `/`

## Definition of done
- [ ] Visiting `/login` and submitting a valid email + password redirects to `/profile`
- [ ] After login, `session['user_id']` is set (verify with Flask debug toolbar or a `print(session)` in the profile route)
- [ ] Submitting an incorrect password re-renders the login form with "Invalid email or password." — no 500 error
- [ ] Submitting an email that does not exist re-renders the login form with the same generic error
- [ ] Visiting `/logout` clears the session and redirects to `/`
- [ ] After logout, visiting `/profile` redirects back to `/login`
- [ ] The navbar shows "Sign out" when logged in and "Sign in" / "Get started" when logged out
- [ ] Hard-coding `/profile` in the address bar while logged out redirects to `/login`
- [ ] The demo account (`demo@spendly.com` / `demo123`) can log in successfully
