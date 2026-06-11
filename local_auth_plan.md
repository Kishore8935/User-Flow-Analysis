# Local Auth Plan — Email + Password with Hashing

Adds email/password login alongside the existing Google OAuth flow.
Users who register with email get a hashed password stored in the DB.
Google OAuth users never have a password (column stays NULL).

---

## Dependencies to Install

```bash
npm install passport-local bcrypt
```

| Package         | Purpose                                      |
|-----------------|----------------------------------------------|
| `passport-local`| Passport strategy for username/password login|
| `bcrypt`        | Hashes passwords (never store plaintext)     |

---

## Phase A — Database: Add Password Column

**File:** `schema.sql` (run the ALTER in Neon SQL Editor)

```sql
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS password_hash TEXT DEFAULT NULL;
```

- Google OAuth users → `password_hash` stays `NULL`
- Local users → `password_hash` holds the bcrypt hash
- No other columns change

---

## Phase B — New DB Helpers in `db.js`

Add two functions:

```
findUserByEmail(email)       → look up a user by email
createLocalUser(email, hash) → INSERT a new local user row
```

These sit alongside the existing `upsertUser` / `findUserById`.

---

## Phase C — Passport Local Strategy in `auth.js`

Add a `passport-local` strategy below the existing Google strategy.

**Login flow:**
1. Find user by email (`findUserByEmail`)
2. If no user → return error "No account with that email"
3. If user has no `password_hash` (OAuth-only account) → return error "This account uses Google login"
4. `bcrypt.compare(submitted_password, stored_hash)` → if mismatch → "Incorrect password"
5. If all pass → `done(null, user)`

**Registration is NOT handled by Passport** — it's a plain POST route in `server.js`.

---

## Phase D — New Routes in `server.js`

### Registration
```
POST /auth/register
  - Validate: email present, password >= 8 chars
  - Check email not already taken (findUserByEmail)
  - Hash password: bcrypt.hash(password, 12)
  - createLocalUser(email, hash)
  - Log in the new user with req.login()
  - Redirect to /
```

### Login
```
POST /auth/login
  - passport.authenticate('local', { failureRedirect: '/login?error=...' })
  - On success → redirect to /
```

No new GET routes needed — both forms live on the existing `/login` page.

---

## Phase E — Update `public/login.html`

The login page gets two new sections added below the Google button:

**Sign In form**
```
Email input
Password input
"Sign In" button  →  POST /auth/login
```

**Register form** (toggled by a link, same page)
```
Email input
Password input (with strength hint)
"Create Account" button  →  POST /auth/register
```

A small JS snippet toggles between the two forms without a page reload.

---

## Security Rules (Non-Negotiable)

| Rule | Implementation |
|------|---------------|
| Never store plaintext passwords | `bcrypt.hash(password, 12)` before INSERT |
| Validate on the server, not just client | Check email + password length in the POST route |
| Same error message for wrong email AND wrong password | Prevents user enumeration |
| Minimum password length | 8 characters enforced server-side |
| bcrypt cost factor | 12 (slow enough to resist brute force) |

---

## Files Changed Summary

| Action     | File              | What changes                                      |
|------------|-------------------|---------------------------------------------------|
| `[MODIFY]` | `schema.sql`      | Add `password_hash TEXT NULL` column              |
| `[MODIFY]` | `db.js`           | Add `findUserByEmail`, `createLocalUser` helpers  |
| `[MODIFY]` | `auth.js`         | Add `passport-local` strategy                     |
| `[MODIFY]` | `server.js`       | Add `POST /auth/register` and `POST /auth/login`  |
| `[MODIFY]` | `public/login.html` | Add sign-in + register forms, toggle JS         |

---

## Order of Implementation

1. Run the `ALTER TABLE` in Neon SQL Editor
2. Add DB helpers to `db.js`
3. Add local strategy to `auth.js`
4. Add routes to `server.js`
5. Update `login.html`
6. Test: register → logout → login → verify row in DB has `password_hash`

---

## What This Does NOT Change

- Google OAuth flow is untouched
- Session handling is the same (Passport serialize/deserialize works for both)
- Existing users table rows are unaffected (`password_hash` defaults to NULL)
