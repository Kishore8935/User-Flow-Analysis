# RadOps — Auth & Database Implementation Plan

## 🛠️ Prerequisites (Install Before Starting)

Before writing any code, make sure the following are installed and configured:

### 1. Node.js & npm
The runtime for your backend server. **Required.**
- **Download**: https://nodejs.org (choose LTS version)
- **Verify install**:
  ```bash
  node -v   # should print v18+ or higher
  npm -v    # should print 8+ or higher
  ```

### 2. Git (optional but recommended)
For source control.
- **Download**: https://git-scm.com

### 3. Google Cloud Console Setup (OAuth Credentials)
You need to create a Google OAuth App manually:
1. Go to https://console.cloud.google.com
2. Create a new project (or use an existing one).
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client IDs**.
4. Set **Application type** to **Web application**.
5. Under **Authorized redirect URIs**, add: `http://localhost:3000/auth/google/callback`
6. Copy your **Client ID** and **Client Secret** — you will need these in Phase 2.

### 4. Neon Tech Database Connection String
1. Go to https://neon.tech and log in.
2. Create or open your project.
3. From the **Dashboard**, copy the **Connection String** (looks like `postgres://user:pass@ep-xxx.aws.neon.tech/dbname?sslmode=require`).
4. Keep this safe — you will need it in Phase 2.

---

## Phase 1 — Project Restructure & Server Bootstrap

**Goal:** Set up the Node.js project and have Express serve your existing dashboard files.

### Tasks
- [ ] Initialize a Node.js project with `npm init`
- [ ] Install core dependencies: `express`, `dotenv`
- [ ] Move `index.html` and `style.css` into a `public/` directory
- [ ] Create `server.js` — Express server that serves the `public/` directory
- [ ] Test: open `http://localhost:3000` and confirm the existing dashboard loads

### Files Changed
| Action | File |
|--------|------|
| `[NEW]` | `package.json` |
| `[NEW]` | `server.js` |
| `[NEW]` | `.env` (template) |
| `[MOVE]` | `index.html` → `public/index.html` |
| `[MOVE]` | `style.css` → `public/style.css` |

---

## Phase 2 — Database: Neon Connection + Users Table

**Goal:** Connect to your Neon PostgreSQL instance and create the `users` table.

### Tasks
- [ ] Install `pg` (PostgreSQL client for Node.js)
- [ ] Add `DATABASE_URL` to `.env` using your Neon connection string
- [ ] Create `db.js` — exports a database pool/client
- [ ] Create `schema.sql` — SQL script to create the users table
- [ ] Run the SQL script against your Neon database (via Neon SQL editor or psql)
- [ ] Test: verify the `users` table exists in Neon's console

### Users Table Schema
```sql
CREATE TABLE IF NOT EXISTS users (
  id              SERIAL PRIMARY KEY,
  oauth_provider  VARCHAR(50)  NOT NULL DEFAULT 'google',
  oauth_id        VARCHAR(255) NOT NULL UNIQUE,
  email           VARCHAR(255) UNIQUE,
  name            VARCHAR(255),
  avatar_url      TEXT,
  last_login      TIMESTAMP,
  created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);
```

### Files Changed
| Action | File |
|--------|------|
| `[NEW]` | `db.js` |
| `[NEW]` | `schema.sql` |
| `[MODIFY]` | `.env` — add `DATABASE_URL` |

---

## Phase 3 — Google OAuth with Passport.js

**Goal:** Implement the full Google OAuth login flow. On first login, create a user record; on subsequent logins, update `last_login`.

### Tasks
- [ ] Install `passport`, `passport-google-oauth20`, `express-session`
- [ ] Add Google OAuth credentials to `.env`
- [ ] Create `auth.js` — Passport strategy config + serialize/deserialize logic
- [ ] Add OAuth routes to `server.js`:
  - `GET /auth/google` — redirects to Google's login page
  - `GET /auth/google/callback` — handles the redirect back, creates/updates user in DB
  - `GET /auth/logout` — destroys session and redirects to login
- [ ] Add session middleware to Express
- [ ] Test: clicking Login redirects to Google → returns to `/` with a session

### OAuth Flow Diagram
```
User visits / → login screen
    ↓
Clicks "Login with Google"
    ↓
GET /auth/google → Google login page
    ↓
Google redirects to /auth/google/callback
    ↓
Passport verifies user → upsert in Neon DB
    ↓
Session created → redirect to /dashboard
```

### Files Changed
| Action | File |
|--------|------|
| `[NEW]` | `auth.js` |
| `[MODIFY]` | `server.js` — add session + passport middleware + routes |
| `[MODIFY]` | `.env` — add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SESSION_SECRET` |

---

## Phase 4 — Login Page UI + Route Protection

**Goal:** Create a beautiful login page and lock the dashboard behind authentication.

### Tasks
- [ ] Create `public/login.html` — a premium login page with a "Login with Google" button
- [ ] Create `public/login.css` — styling for the login page
- [ ] Modify `server.js` to add route protection middleware:
  - Unauthenticated users visiting `/` are redirected to `/login`
  - Authenticated users visiting `/login` are redirected to `/`
- [ ] Add a logout button to the dashboard header in `public/index.html`
- [ ] Show user's name/avatar in the dashboard header post-login

### Files Changed
| Action | File |
|--------|------|
| `[NEW]` | `public/login.html` |
| `[NEW]` | `public/login.css` |
| `[MODIFY]` | `public/index.html` — logout button + user info display |
| `[MODIFY]` | `server.js` — auth guard middleware |

---

## Phase 5 — User API + Session Handoff

**Goal:** Expose a simple API endpoint so the frontend can read the current logged-in user's data (name, avatar) and display it in the header.

### Tasks
- [ ] Add `GET /api/me` route — returns `{ id, name, email, avatar_url }` for logged-in user, or 401
- [ ] Update `public/index.html` to call `/api/me` on load and populate the header with user info
- [ ] Final end-to-end test
- [ ] Add `GET /api/users` route (admin-only view of the users table) — optional

### Files Changed
| Action | File |
|--------|------|
| `[MODIFY]` | `server.js` — add `/api/me` route |
| `[MODIFY]` | `public/index.html` — fetch user on load, display in header |

---

## Final Project Structure

```
/Intern/kishore/Dashboard/
├── public/
│   ├── index.html      ← dashboard (protected)
│   ├── style.css       ← dashboard styles
│   ├── login.html      ← login page (public)
│   └── login.css       ← login styles
├── server.js           ← Express app entry point
├── auth.js             ← Passport Google OAuth config
├── db.js               ← Neon DB connection pool
├── schema.sql          ← SQL to create users table
├── .env                ← secrets (never commit this!)
├── .gitignore          ← ignore node_modules, .env
└── package.json
```

---

## Verification Checklist (End-to-End)

- [ ] `node server.js` starts without errors and connects to Neon DB
- [ ] Visiting `http://localhost:3000` redirects to `/login`
- [ ] Clicking "Login with Google" redirects to Google's OAuth screen
- [ ] After Google auth, you land on the dashboard
- [ ] A new row appears in the `users` table in Neon's console
- [ ] The header shows your name and profile picture
- [ ] Logging out redirects back to the login screen
- [ ] Revisiting the dashboard without a session requires login again

---

> [!TIP]
> **Ready to start?** Tell me to begin **Phase 1** and I will write all the code for you. We'll go phase by phase and verify each one before moving on.
