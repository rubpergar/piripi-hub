from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing


class HubfileBehavior(TaskSet):
    def on_start(self):
        self.index()

    @task
    def index(self):
        response = self.client.get("/hubfile")

        if response.status_code != 200:
            print(f"Hubfile index failed: {response.status_code}")

    @task
    def download_selected(self):
        file_ids = "1,2,3"
        response = self.client.get(
            f"/dataset/download_selected?file_ids={file_ids}",
            name="/dataset/download_selected",
        )

        if response.status_code == 200:
            print(f"Download successful for file_ids: {file_ids}")
        else:
            print(
                f"Download failed for file_ids: {file_ids} with status code {response.status_code}"
            )


class HubfileUser(HttpUser):
    tasks = [HubfileBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
