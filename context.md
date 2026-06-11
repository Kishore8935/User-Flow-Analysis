# RadOps Dashboard - Context and Progress

This document serves as a record of the architectural changes and development progress made on the RadOps Intelligence Center dashboard.

## Initial State
- A static HTML/CSS dashboard (`index.html`, `style.css`) built using Apache ECharts via CDN.
- The UI was initially implemented in Dark Mode and then successfully transitioned to a premium Light Mode theme (updating CSS variables, ECharts configurations, and UI components).

## Goal
To evolve the static dashboard into a dynamic, secure web application with:
1. A Node.js / Express backend.
2. A PostgreSQL database hosted on Neon Tech.
3. Google OAuth 2.0 authentication.

## Implementation Phases & Progress

### Phase 1: Server Bootstrap (Completed)
- **Dependencies**: Initialized `package.json` and installed `express` (v5.x) and `dotenv`.
- **Restructuring**: Moved the static frontend assets (`index.html` and `style.css`) into a `public/` directory.
- **Server Setup**: Created `server.js` to serve static files, provide a `/health` check endpoint, and act as the main entry point. Added `start` and `dev` scripts to `package.json`.
- *Note: Updated catch-all route syntax to `/{*path}` for compatibility with Express 5.*

### Phase 2: Database Connection & Schema (Completed)
- **Dependencies**: Installed `pg` (PostgreSQL client).
- **Configuration**: Added the Neon Tech `DATABASE_URL` to `.env`.
- **Database Module**: Created `db.js` to manage the PostgreSQL connection pool (with SSL required for Neon) and helper functions (`upsertUser`, `findUserById`, `testConnection`).
- **Schema**: Created `schema.sql` defining the `users` table and necessary indexes (designed to be run manually in the Neon SQL Editor).
- **Integration**: Updated `server.js` to test the database connection during application startup.

### Phase 3: Google OAuth Integration (Completed)
- **Dependencies**: Installed `passport`, `passport-google-oauth20`, and `express-session`.
- **Configuration**: Added `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `SESSION_SECRET` to `.env`.
- **Auth Strategy**: Created `auth.js` to configure the Passport Google Strategy. It handles serializing/deserializing users and upserting user data into the database upon successful login.
- **Server Integration**: Updated `server.js` to include:
  - Session middleware (`express-session`).
  - Passport initialization.
  - Auth routes: `/auth/google` (initiate login), `/auth/google/callback` (handle redirect), and `/auth/logout`.
  - An auth guard middleware (`requireAuth`) to protect the dashboard routes and redirect unauthenticated users to `/login`.
  - An API route `/api/me` to expose the logged-in user's details.

### Phase 4: Login UI & Route Protection (In Progress / Partially Completed)
- **Login UI**: Created `public/login.html` and `public/login.css`. This features a premium, responsive two-panel design with the RadOps branding on the left and a "Continue with Google" OAuth button on the right.
- **Route Protection**: The backend routes in `server.js` are fully protected. Unauthenticated traffic to `/` is redirected to `/login`.

### Phase 5: Frontend Session Handoff (Pending)
- **Task**: Update `public/index.html` to fetch the logged-in user's profile from `/api/me` on load and display their name and avatar in the header. Add a functional logout button to the header.

## Current Project Structure
```text
C:\Intern\kishore\Dashboard\
├── public/
│   ├── index.html       (Protected dashboard)
│   ├── style.css        (Dashboard styling)
│   ├── login.html       (Public login page)
│   └── login.css        (Login page styling)
├── server.js            (Express server entry point)
├── db.js                (Neon DB connection pool)
├── auth.js              (Passport Google OAuth config)
├── schema.sql           (SQL scripts for DB setup)
├── package.json         (Dependencies and scripts)
├── .env                 (Environment variables - SECRET)
├── .gitignore           (Git ignore rules)
└── context.md           (This file)
```
