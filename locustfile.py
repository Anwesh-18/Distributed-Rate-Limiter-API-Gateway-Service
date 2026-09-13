"""
Run with: locust -f locustfile.py --host http://localhost:8000

Then open http://localhost:8089 to configure user count and spawn rate,
and watch requests/sec + latency live. Capture a screenshot + the summary
stats for your README once your rate limiter is fully wired up.

Generate a test JWT first (see app/auth.py docstring) and paste it below.
"""
from locust import HttpUser, task, between

TEST_JWT = "PASTE_A_VALID_TEST_JWT_HERE"


class FreeTierUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def hit_proxy_endpoint(self):
        self.client.get(
            "/proxy/ping",
            headers={"Authorization": f"Bearer {TEST_JWT}"},
        )
