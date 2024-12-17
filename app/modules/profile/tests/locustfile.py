from locust import HttpUser, task, between
from core.environment.host import get_host_for_locust_testing


class ProfilePublicDataAccess(HttpUser):
    wait_time = between(1, 3)
    host = get_host_for_locust_testing()

    @task
    def public_data_true_access(self):
        response = self.client.get("/profile/1")
        if response.status_code == 200:
            print("Profile with public data true loaded correctly.")
        else:
            print(f"Error loading profile: {response.status_code}")

    @task
    def public_data_false_access(self):
        response = self.client.get("/profile/2")
        if response.status_code == 200:
            print("Controlled error message of profile with public data false.")
        else:
            print(f"Unhandled error: {response.status_code}")
