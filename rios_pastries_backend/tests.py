import json
import os
import subprocess
import sys

from django.test import SimpleTestCase


class DeploymentSettingsTests(SimpleTestCase):
    def read_settings(self, render_host='', custom_host=''):
        env = os.environ.copy()
        env.update({
            'RENDER_EXTERNAL_HOSTNAME': render_host,
            'RIOS_PASTRIES_EXTERNAL_HOSTNAME': custom_host,
            'SECRET_KEY': 'test-settings-key',
        })
        result = subprocess.run(
            [
                sys.executable,
                '-c',
                (
                    'import json, django; '
                    'from django.conf import settings; '
                    'django.setup(); '
                    'from django.core.handlers.wsgi import WSGIHandler; '
                    'WSGIHandler(); '
                    'print(json.dumps({"debug": settings.DEBUG, '
                    '"hosts": settings.ALLOWED_HOSTS, '
                    '"middleware": settings.MIDDLEWARE, '
                    '"email_backend": settings.EMAIL_BACKEND}))'
                ),
            ],
            env={**env, 'DJANGO_SETTINGS_MODULE': 'rios_pastries_backend.settings'},
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    def test_local_debug_remains_enabled(self):
        config = self.read_settings()
        self.assertTrue(config['debug'])
        self.assertIn('whitenoise.middleware.WhiteNoiseMiddleware', config['middleware'])
        self.assertEqual(config['email_backend'], 'django.core.mail.backends.smtp.EmailBackend')

    def test_render_disables_debug_and_loads_middleware(self):
        for render_host, custom_host in (
            ('example.onrender.com', ''),
            ('', 'example.com'),
        ):
            with self.subTest(render_host=render_host, custom_host=custom_host):
                config = self.read_settings(render_host, custom_host)
                self.assertFalse(config['debug'])
                self.assertIn(render_host or custom_host, config['hosts'])
                self.assertIn('whitenoise.middleware.WhiteNoiseMiddleware', config['middleware'])
                self.assertEqual(config['email_backend'], 'django.core.mail.backends.smtp.EmailBackend')
