from locust import HttpUser, task, between, SequentialTaskSet
import secrets
from core.environment.host import get_host_for_locust_testing


class DatasetTasks(SequentialTaskSet):

    @task(1)
    def create_rate(self):
        """Simula la creación de una nueva calificación"""
        response = self.client.get("/login")

        response = self.client.post(
            "/login",
            data={
                "email": "user1@example.com",
                "password": "1234",
            },
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
        dataset_id = 2
        data = {
            "rate": secrets.randbelow(10)
            + 1,  # Usando secrets para un número aleatorio seguro
            "comment": f"Comentario generado por Locust {secrets.randbelow(9000) + 1000}",  # Seguro
        }
        print(f"Creando una calificación para el dataset {dataset_id}...")
        response = self.client.post(f"/ratedataset/create/{dataset_id}", json=data)
        if response.status_code == 200:
            print(f"Calificación creada correctamente para el dataset {dataset_id}.")
        else:
            print(f"Error al crear calificación: {response.status_code}")

    @task(2)
    def edit_rate(self):
        """Simula la edición de una calificación existente"""
        dataset_id = 2
        rate_id = (
            secrets.randbelow(100) + 1
        )  # Usando secrets para un número aleatorio seguro
        data = {
            "rate": secrets.randbelow(10) + 1,  # Seguro
            "comment": f"Comentario editado por Locust {secrets.randbelow(9000) + 1000}",  # Seguro
        }
        print(f"Editando la calificación {rate_id} para el dataset {dataset_id}...")
        response = self.client.post(
            f"/ratedataset/edit/{dataset_id}/{rate_id}", json=data
        )
        if response.status_code == 200:
            print(f"Calificación {rate_id} editada correctamente.")
        else:
            print(f"Error al editar la calificación: {response.status_code}")

    @task(3)
    def delete_rate(self):
        """Simula la eliminación de una calificación"""
        dataset_id = 2
        rate_id = (
            secrets.randbelow(100) + 1
        )  # Usando secrets para un número aleatorio seguro
        print(f"Eliminando la calificación {rate_id} para el dataset {dataset_id}...")
        response = self.client.post(f"/ratedataset/delete/{dataset_id}/{rate_id}")
        if response.status_code == 200:
            print(f"Calificación {rate_id} eliminada correctamente.")
        else:
            print(f"Error al eliminar la calificación: {response.status_code}")


class WebsiteTestUser(HttpUser):
    wait_time = between(1, 5)
    tasks = [DatasetTasks]
    host = get_host_for_locust_testing()
