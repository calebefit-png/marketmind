import unittest

from starlette.responses import Response

from services.security_headers import apply_security_headers


class SecurityHeadersTests(unittest.TestCase):
    def test_applies_non_visual_protection_headers_in_all_environments(self) -> None:
        response = apply_security_headers(Response(), production=False)

        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "strict-origin-when-cross-origin")
        self.assertEqual(response.headers["permissions-policy"], "camera=(), geolocation=(), microphone=()")
        self.assertNotIn("strict-transport-security", response.headers)

    def test_enables_hsts_only_for_production_responses(self) -> None:
        response = apply_security_headers(Response(), production=True)

        self.assertEqual(response.headers["strict-transport-security"], "max-age=31536000; includeSubDomains")
