from locust import HttpUser, TaskSet, task, between
from core.locust.common import get_csrf_token
from core.environment.host import get_host_for_locust_testing


class DatasetBehavior(TaskSet):
    def on_start(self):
        self.dataset()

    @task
    def dataset(self):
        response = self.client.get("/dataset/upload")
        get_csrf_token(response)


class DatasetUser(HttpUser):
    wait_time = between(1, 3)
    tasks = [DatasetBehavior]

    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

class DatasetDownloadUser(HttpUser):
    host = "http://localhost:5000"

    wait_time = between(1, 3)

    @task
    def download_all_datasets(self):
        """Simula la descarga del archivo ZIP con todos los datasets"""
        response = self.client.get("/dataset/download/all")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers["Content-Type"] == "application/zip", f"Expected content type 'application/zip', got {response.headers['Content-Type']}"