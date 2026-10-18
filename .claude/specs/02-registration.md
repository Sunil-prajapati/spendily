# Spec: Registration

## Overview
Allow new users to create a Spendly account via a registration form. This step
wires up the `POST /register` handler, validates user input, stores a hashed
password in the database, flashes a success message, and redirects to the login
page. It is the first step that writes user data and introduces Flask's `flash`
and `session` imports — patterns every subsequent step reuses.

## Depends on
Step 01 — Database Setup (`users` table and `create_user()` must exist).

## Routes
- `GET  /register` — render the registration form — public
- `POST /register` — validate fields, create user, flash success, redirect to `/login` — public

## Database changes
No new tables or columns. Uses the existing `users` table and `create_user()`
function from `database/db.py`.

## Templates
- **Modify:** `templates/base.html` — add a `{% with messages = get_flashed_messages(with_categories=true) %}` block inside `<main>` (before `{% block content %}`) to render flash messages
- **Modify:** `templates/register.html` — already scaffolded; verify the form posts to `/register`, displays `{{ error }}`, and that all three fields (`name`, `email`, `password`) are present with correct `name` attributes
- **No change:** `templates/login.html` — exists as the redirect target; not modified in this step

## Files to change
- `app.py` — complete the `POST /register` handler and add `flash` import
- `templates/base.html` — add flash message rendering block

## Files to create
None.

## New dependencies
No new pip packages.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (enforced inside `create_user()`)
- Passwords hashed with `werkzeug.security.generate_password_hash` (enforced inside `create_user()`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `flask.flash` for the post-registration success message; do **not** embed the message in the redirect URL
- Catch `sqlite3.IntegrityError` on duplicate email and re-render the form with a user-facing error string (not a 500)
- Validate server-side: all three fields required, password ≥ 8 characters
- `app.secret_key` must be set before `flash` will work (already present in scaffold — do not remove it)

## Definition of done
- [ ] Visiting `/register` renders a form with fields: Full name, Email, Password
- [ ] Submitting the form with all valid fields creates a new row in `users` (verify with a DB browser or `SELECT * FROM users`)
- [ ] After successful registration the browser redirects to `/login`
- [ ] A flash success message (e.g. "Account created! Please sign in.") appears on the login page
- [ ] Submitting with any empty field re-renders the form with an error message — no user is created
- [ ] Submitting a password shorter than 8 characters re-renders the form with an error message
- [ ] Registering with an email that already exists re-renders the form with a duplicate-email error — no exception page
- [ ] Passwords are stored as hashes (not plain text) — confirm by inspecting `users.password_hash` in the DB
- [ ] Flash messages are visible on the login page after redirect and disappear on refresh
