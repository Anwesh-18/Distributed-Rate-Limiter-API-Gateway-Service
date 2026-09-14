from locust import HttpUser, task, between

TEST_JWT = "A_VALID_TEST_JWT_HERE"

class FreeTierUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def hit_proxy_endpoint(self):
        self.client.get(
            "/proxy/ping",
            headers={"Authorization": f"Bearer {TEST_JWT}"},
        )
