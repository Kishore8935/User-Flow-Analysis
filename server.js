'use strict';

require('dotenv').config();

const express  = require('express');
const path     = require('path');
const session  = require('express-session');
const bcrypt   = require('bcrypt');
const passport = require('./auth');
const db       = require('./db');

const app  = express();
const PORT = process.env.PORT || 3000;

// ── Serve static files from /public ──────────────────────────────
// index:false prevents auto-serving index.html for /, so the auth guard route runs instead
app.use(express.static(path.join(__dirname, 'public'), { index: false }));

// ── Parse JSON & form bodies ──────────────────────────────────────
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// ── Session middleware ────────────────────────────────────────────
app.use(session({
  secret:            process.env.SESSION_SECRET,
  resave:            false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,   // not accessible via JS (XSS protection)
    secure:   false,  // set to true in production with HTTPS
    maxAge:   1000 * 60 * 60 * 24, // 24 hours
  },
}));

// ── Passport middleware ───────────────────────────────────────────
app.use(passport.initialize());
app.use(passport.session());

// ── Auth guard middleware ─────────────────────────────────────────
// Redirects unauthenticated users to /login
function requireAuth(req, res, next) {
  if (req.isAuthenticated()) return next();
  res.redirect('/login');
}

// Requires the logged-in user to have the 'admin' role
function requireAdmin(req, res, next) {
  if (req.isAuthenticated() && req.user.role === 'admin') return next();
  res.status(403).json({ error: 'Admin access required' });
}

const VALID_ROLES = ['admin', 'radiologist', 'technician', 'frontdesk', 'manager'];

// ── Health check ──────────────────────────────────────────────────
app.get('/health', async (req, res) => {
  try {
    const version = await db.testConnection();
    res.json({ status: 'ok', database: 'connected', pg_version: version });
  } catch (err) {
    res.status(500).json({ status: 'error', database: 'disconnected', error: err.message });
  }
});

// ================================================================
//  AUTH ROUTES
// ================================================================

// Step 1 — Redirect user to Google's OAuth consent screen
app.get('/auth/google',
  passport.authenticate('google', { scope: ['profile', 'email'] })
);

// Step 2 — Google redirects back here after user consents
app.get('/auth/google/callback',
  passport.authenticate('google', {
    failureRedirect: '/login?error=auth_failed',
  }),
  (req, res) => {
    // Success — send to the protected dashboard
    res.redirect('/');
  }
);

// Logout — destroy session and redirect to login
app.get('/auth/logout', (req, res, next) => {
  req.logout((err) => {
    if (err) return next(err);
    req.session.destroy(() => {
      res.redirect('/login');
    });
  });
});

// POST /auth/login — local email+password login
app.post('/auth/login',
  passport.authenticate('local', { failureRedirect: '/login?error=login_failed' }),
  (req, res) => res.redirect('/')
);

// POST /auth/register — create a new local account
app.post('/auth/register', async (req, res, next) => {
  const { email, password } = req.body;
  if (!email || !password)      return res.redirect('/login?error=missing_fields');
  if (password.length < 8)      return res.redirect('/login?error=weak_password');

  try {
    const existing = await db.findUserByEmail(email);
    if (existing)               return res.redirect('/login?error=email_taken');

    const hash = await bcrypt.hash(password, 12);
    const user = await db.createLocalUser(email, hash);

    req.login(user, (err) => {
      if (err) return next(err);
      res.redirect('/');
    });
  } catch (err) {
    next(err);
  }
});

// ================================================================
//  API ROUTES
// ================================================================

// GET /api/me — returns current logged-in user (used by the frontend)
app.get('/api/me', requireAuth, (req, res) => {
  const { id, name, email, avatar_url, oauth_provider, role } = req.user;
  res.json({ id, name, email, avatar_url, role,
    auth_method: oauth_provider === 'local' ? 'credentials' : oauth_provider });
});

// GET /api/admin/users — list all users with roles (admin only)
app.get('/api/admin/users', requireAuth, requireAdmin, async (req, res, next) => {
  try {
    res.json(await db.getAllUsers());
  } catch (err) { next(err); }
});

// PATCH /api/admin/users/:id/role — change a user's role (admin only)
app.patch('/api/admin/users/:id/role', requireAuth, requireAdmin, async (req, res, next) => {
  const userId = parseInt(req.params.id, 10);
  const { role } = req.body;
  if (!VALID_ROLES.includes(role)) return res.status(400).json({ error: `Invalid role. Must be one of: ${VALID_ROLES.join(', ')}` });
  try {
    const updated = await db.setUserRole(userId, role);
    if (!updated) return res.status(404).json({ error: 'User not found' });
    res.json(updated);
  } catch (err) { next(err); }
});

// Analytics routes — no auth required so tracker can fire on page unload too
app.use('/api/analytics', require('./routes/analytics'));

// ================================================================
//  PAGE ROUTES
// ================================================================

// /login — serve login page (redirect to dashboard if already logged in)
app.get('/login', (req, res) => {
  if (req.isAuthenticated()) return res.redirect('/');
  res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

// / — protected dashboard (redirect to login if not authenticated)
app.get('/', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Catch-all for any other paths
app.get('/{*path}', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ================================================================
//  START SERVER
// ================================================================
async function start() {
  try {
    const version = await db.testConnection();
    console.log(`🗄️   Neon DB connected — ${version.split(',')[0]}`);
    app.listen(PORT, () => {
      console.log(`✅  RadOps server running at http://localhost:${PORT}`);
    });
  } catch (err) {
    console.error('❌  Could not connect to database:', err.message);
    process.exit(1);
  }
}

start();
