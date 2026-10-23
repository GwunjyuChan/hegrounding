# Website Login

The deployed site uses `/login.html`, not a browser Basic Auth dialog. Existing
username/password values are retained. A dedicated loopback service on port 8880
handles authentication for both annotation workspaces through Caddy `forward_auth`.
See the [Caddy documentation](https://caddyserver.com/docs/caddyfile/directives/forward_auth).

## Security Boundary

- `/login.html`, `/login.js`, `/login.css` and login/logout/session endpoints are public.
- All workspace pages, images, uploads and APIs still require a valid session.
- Credentials are stored as a salted scrypt hash in `/etc/hegrounding-auth.json`,
  owned by root, group `hegrounding`, mode 0640. Do not commit this file.
- The opaque `__Host-he_session` cookie is Secure, HttpOnly, SameSite=Lax, Path=/,
  without a Domain attribute. Sessions expire after 12 hours and are held in memory.
- Restarting `hegrounding-auth` invalidates existing sessions. Logout revokes the
  server session, not merely the browser cookie.
- Login/logout require JSON and an exact HTTPS Origin; existing annotation CSRF and
  Host/Origin checks remain. Failed or successful login attempts share bounded rate limits.
- No password/session credential is placed in URLs, frontend storage or command arguments.
- If the auth service is down, Caddy fails closed. Backends remain loopback-only.
- HTML navigation without a session redirects to login; APIs return JSON 401 and never
  ask the browser to show a Basic Auth dialog. Re-login in a new tab preserves editor drafts.

## Operations

`deploy/hegrounding-session.caddy` is the session-based replacement for the earlier
Basic Auth snippet. The original installer remains an initial Basic Auth bootstrap;
do not rerun it over an existing deployment. Login migration requires the auth service,
credential hash, new application files and Caddy snippet together.

```bash
systemctl status hegrounding-auth hegrounding@events hegrounding@labels
/opt/hegrounding/venv/bin/python /opt/hegrounding/current/deploy/verify.py
```

The verifier uses the existing root-only access file to log in over verified HTTPS,
checks both workspaces and logout revocation, and never prints credentials.
Account management/password reset is not exposed in the UI. This is a single-account
research platform, not a multi-user identity service. Research data remain under
`/var/lib/hegrounding`; program updates must not replace that directory.
