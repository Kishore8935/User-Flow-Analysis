'use strict';

const passport        = require('passport');
const GoogleStrategy  = require('passport-google-oauth20').Strategy;
const LocalStrategy   = require('passport-local').Strategy;
const bcrypt          = require('bcrypt');
const db              = require('./db');

// ── Serialise: what gets stored in the session cookie ────────────
// We only store the user's DB id — lightweight & secure.
passport.serializeUser((user, done) => {
  done(null, user.id);
});

// ── Deserialise: on each request, load the full user from the DB ─
passport.deserializeUser(async (id, done) => {
  try {
    const user = await db.findUserById(id);
    done(null, user);
  } catch (err) {
    done(err, null);
  }
});

// ── Google OAuth 2.0 Strategy ────────────────────────────────────
passport.use(
  new GoogleStrategy(
    {
      clientID:     process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      callbackURL:  'http://localhost:8080/auth/google/callback',
    },
    async (accessToken, refreshToken, profile, done) => {
      try {
        // Upsert: create user on first login, update on subsequent logins
        const user = await db.upsertUser({
          oauth_provider: 'google',
          oauth_id:       profile.id,
          email:          profile.emails?.[0]?.value  || null,
          name:           profile.displayName          || null,
          avatar_url:     profile.photos?.[0]?.value  || null,
        });

        console.log(`🔐  OAuth login: ${user.name} (${user.email})`);
        return done(null, user);
      } catch (err) {
        console.error('❌  OAuth upsert error:', err.message);
        return done(err, null);
      }
    }
  )
);

// ── Local (email + password) Strategy ───────────────────────────
passport.use(
  new LocalStrategy(
    { usernameField: 'email' },
    async (email, password, done) => {
      try {
        const user = await db.findUserByEmail(email);
        if (!user) return done(null, false, { message: 'No account with that email.' });
        if (!user.password_hash) return done(null, false, { message: 'This account uses Google login.' });
        const match = await bcrypt.compare(password, user.password_hash);
        if (!match) return done(null, false, { message: 'Incorrect password.' });
        return done(null, user);
      } catch (err) {
        return done(err);
      }
    }
  )
);

module.exports = passport;
