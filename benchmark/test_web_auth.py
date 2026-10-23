import http.client
import json
import threading
import unittest

from web_auth import COOKIE, TTL, Sessions, make_auth_server, password_record, safe_next


class WebAuthTests(unittest.TestCase):
    origin = 'https://experiment.chanlukaka.com'

    def setUp(self):
        self.server = make_auth_server(0, self.origin, password_record('tester', 'test-password'))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        values = {'Host': 'experiment.chanlukaka.com', 'Content-Type': 'application/json',
                  'Origin': self.origin, **(headers or {})}
        connection.request(method, path, json.dumps(body) if body is not None else None, values)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def login(self, **changes):
        return self.request('POST', '/auth/login', {'username': 'tester', 'password': 'test-password', **changes})

    def test_login_cookie_access_logout(self):
        status, headers, body = self.login(next='/labels/place-lab.html?map=abc')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['next'], '/labels/place-lab.html?map=abc')
        value = headers['Set-Cookie']
        for flag in ('Secure', 'HttpOnly', 'SameSite=Lax', 'Path=/', COOKIE):
            self.assertIn(flag, value)
        cookie = {'Cookie': value.split(';')[0]}
        self.assertEqual(self.request('GET', '/auth/check', headers=cookie)[0], 204)
        self.assertTrue(json.loads(self.request('GET', '/auth/session', headers=cookie)[2])['authenticated'])
        self.assertEqual(self.request('POST', '/auth/logout', {}, cookie)[0], 200)
        self.assertEqual(self.request('GET', '/auth/check', headers=cookie)[0], 401)

    def test_unauthenticated_pages_redirect_apis_do_not(self):
        status, headers, _ = self.request('GET', '/auth/check', headers={
            'Accept': 'text/html', 'X-Forwarded-Uri': '/labels/place-lab.html?map=test'})
        self.assertEqual(status, 303)
        self.assertTrue(headers['Location'].startswith('/login.html?next='))
        status, headers, _ = self.request('GET', '/auth/check')
        self.assertEqual(status, 401)
        self.assertNotIn('WWW-Authenticate', headers)
        self.assertNotIn('Location', headers)
        self.assertEqual(self.request('GET', '/login.html')[0], 200)
        for path in ('/i18n.js', '/i18n.css'):
            self.assertEqual(self.request('GET', path)[0], 200)

    def test_csrf_host_and_credentials(self):
        body = {'username': 'tester', 'password': 'test-password'}
        for headers in ({'Origin': 'https://evil.example'}, {'Host': 'evil.example'},
                        {'Content-Type': 'text/plain'}, {'Origin': ''}):
            self.assertEqual(self.request('POST', '/auth/login', body, headers)[0], 403)
        self.assertEqual(self.login(password='wrong')[0], 401)
        self.assertEqual(self.login(username='other')[0], 401)
        self.assertEqual(self.request('GET', '/auth/check', headers={'Authorization': 'Basic old-login'})[0], 401)

    def test_rate_limit(self):
        for _ in range(15):
            self.assertEqual(self.login(password='wrong')[0], 401)
        self.assertEqual(self.login()[0], 429)

    def test_safe_redirect_and_expiry(self):
        for path in ('https://evil.example', '//evil.example', '/\\evil.example',
                     '/%2fexample.com', '/%0d%0aLocation:evil', '/login.html', '/auth/login'):
            self.assertEqual(safe_next(path), '/')
        clock = [0]
        sessions = Sessions(self.server.sessions.credentials, clock=lambda: clock[0])
        value = sessions.create()
        self.assertTrue(sessions.valid(value))
        clock[0] = TTL + 1
        self.assertFalse(sessions.valid(value))
        self.assertFalse(sessions.valid('made-up'))


if __name__ == '__main__':
    unittest.main()
