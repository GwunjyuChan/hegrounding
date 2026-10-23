"""Small single-account session gateway for Caddy forward_auth (loopback only)."""
import argparse
from collections import deque
import hashlib
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import quote, unquote, urlsplit

COOKIE = '__Host-he_session'
TTL = 12 * 60 * 60
STATIC = Path(__file__).with_name('gui')


def password_record(username, password):
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, maxmem=67108864)
    return {'username': username, 'salt': salt.hex(), 'hash': key.hex()}


def safe_next(value):
    if not isinstance(value, str) or len(value) > 2000:
        return '/'
    decoded = value
    for _ in range(3):
        decoded = unquote(decoded)
    if (not decoded.startswith('/') or decoded.startswith('//') or '\\' in decoded
            or any(ord(c) < 32 or ord(c) == 127 for c in decoded)
            or urlsplit(decoded).path.startswith(('/auth', '/login'))):
        return '/'
    return value


class Sessions:
    def __init__(self, credentials, clock=time.monotonic):
        self.credentials, self.clock = credentials, clock
        self.sessions, self.attempts = {}, {}
        self.lock = threading.Lock()
        self.verify_slots = threading.BoundedSemaphore(2)

    def allowed(self, ip):
        now = self.clock()
        with self.lock:
            for key in list(self.attempts):
                while self.attempts[key] and self.attempts[key][0] <= now - 300:
                    self.attempts[key].popleft()
                if not self.attempts[key]:
                    del self.attempts[key]
            for key, limit in ((ip, 15), ('*', 100)):
                if len(self.attempts.get(key, ())) >= limit:
                    return False
            for key in (ip, '*'):
                self.attempts.setdefault(key, deque()).append(now)
            return True

    def verify(self, username, password):
        c = self.credentials
        with self.verify_slots:
            key = hashlib.scrypt(password.encode(), salt=bytes.fromhex(c['salt']),
                                 n=16384, r=8, p=1, maxmem=67108864)
        return secrets.compare_digest(key.hex(), c['hash']) & secrets.compare_digest(
            username.encode(), c['username'].encode())

    def create(self):
        raw = secrets.token_urlsafe(32)
        with self.lock:
            now = self.clock()
            self.sessions = {k: v for k, v in self.sessions.items() if v > now}
            if len(self.sessions) >= 2048:
                self.sessions.pop(next(iter(self.sessions)))
            self.sessions[hashlib.sha256(raw.encode()).hexdigest()] = now + TTL
        return raw

    def valid(self, raw):
        with self.lock:
            key = hashlib.sha256(raw.encode()).hexdigest()
            expiry = self.sessions.get(key, 0)
            if expiry <= self.clock():
                self.sessions.pop(key, None)
                return False
            return True

    def revoke(self, raw):
        with self.lock:
            self.sessions.pop(hashlib.sha256(raw.encode()).hexdigest(), None)


class AuthHandler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def send(self, code, data=b'', mime='application/json; charset=utf-8', headers=()):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        for key, value in (('Content-Type', mime), ('Content-Length', str(len(data))),
                           ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'),
                           ('X-Frame-Options', 'DENY'), ('Referrer-Policy', 'no-referrer'),
                           ('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"), *headers):
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def trusted(self):
        return self.headers.get('Host') == urlsplit(self.server.origin).netloc

    def cookie(self):
        try:
            cookies = SimpleCookie(self.headers.get('Cookie', ''))
            return cookies[COOKIE].value if COOKIE in cookies else ''
        except CookieError:
            return ''

    def do_GET(self):
        if not self.trusted():
            return self.send(403, {'error': 'Invalid host'})
        path = urlsplit(self.path).path
        if path in ('/login.html', '/login.js', '/login.css', '/i18n.js', '/i18n.css'):
            mime = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8'}
            file = STATIC / path[1:]
            return self.send(200, file.read_bytes(), mime[file.suffix])
        authenticated = self.server.sessions.valid(self.cookie())
        if path == '/auth/session':
            return self.send(200, {'authenticated': authenticated})
        if path == '/auth/check':
            if authenticated:
                return self.send(204)
            target = safe_next(self.headers.get('X-Forwarded-Uri', '/'))
            if 'text/html' in self.headers.get('Accept', ''):
                return self.send(303, headers=(('Location', '/login.html?next=' + quote(target, safe='')),))
            return self.send(401, {'error': '登录已过期，请在新标签页登录后重试；当前草稿仍保留。', 'login_url': '/login.html'})
        return self.send(404, {'error': 'Not found'})

    def do_POST(self):
        if (not self.trusted() or self.headers.get('Origin') != self.server.origin
                or self.headers.get('Content-Type', '').split(';')[0] != 'application/json'):
            return self.send(403, {'error': '请求来源无效'})
        path = urlsplit(self.path).path
        if path not in ('/auth/login', '/auth/logout'):
            return self.send(404, {'error': 'Not found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 8192:
                raise ValueError()
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            return self.send(400, {'error': '登录请求格式无效'})
        suffix = '; Path=/; Secure; HttpOnly; SameSite=Lax'
        if path == '/auth/logout':
            self.server.sessions.revoke(self.cookie())
            return self.send(200, {'ok': True}, headers=(('Set-Cookie', COOKIE + '=; Max-Age=0' + suffix),))
        ip = self.headers.get('X-Real-IP', self.client_address[0])[:100]
        if not self.server.sessions.allowed(ip):
            return self.send(429, {'error': '登录尝试过于频繁，请五分钟后重试。'}, headers=(('Retry-After', '300'),))
        username, password = body.get('username'), body.get('password')
        if (not isinstance(username, str) or not isinstance(password, str)
                or len(username) > 200 or len(password) > 1024):
            return self.send(400, {'error': '用户名或密码格式无效'})
        if not self.server.sessions.verify(username, password):
            return self.send(401, {'error': '用户名或密码错误'})
        self.server.sessions.revoke(self.cookie())
        cookie = self.server.sessions.create()
        return self.send(200, {'next': safe_next(body.get('next', '/'))},
                         headers=(('Set-Cookie', COOKIE + '=' + cookie + f'; Max-Age={TTL}' + suffix),))


def make_auth_server(port, origin, credentials):
    parsed = urlsplit(origin)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('Expected an HTTPS origin')
    server = ThreadingHTTPServer(('127.0.0.1', port), AuthHandler)
    server.origin, server.sessions = origin, Sessions(credentials)
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8880)
    parser.add_argument('--origin', required=True)
    parser.add_argument('--credentials', type=Path, required=True)
    args = parser.parse_args()
    server = make_auth_server(args.port, args.origin, json.loads(args.credentials.read_text()))
    try:
        server.serve_forever()
    finally:
        server.server_close()
