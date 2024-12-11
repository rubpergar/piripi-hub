from locust import HttpUser, task, between
from random import choice
from datetime import datetime
import json


class AdvancedFilteringUser(HttpUser):
    wait_time = between(1, 3)  # Simula tiempo entre las solicitudes (1 a 3 segundos)

    @task(1)
    def simple_explore(self):
        # Una solicitud simple GET a la página de exploración sin filtros
        self.client.get("/explore", name="GET /explore (No Filter)")

    @task(2)
    def advanced_filtering_features_ok(self):
        with self.client.post(
            "/explore",  # Ruta donde el formulario es procesado
            data=json.dumps({"number_of_features": 50}),  # Datos como JSON
            headers={
                "Content-Type": "application/json"
            },  # Especificar que estamos enviando JSON
            catch_response=True,  # Necesario para manejar la respuesta manualmente
            name="POST /explore (Advanced Filtering features OK)",
        ) as response:
            # Verificar la respuesta y manejar errores
            if response.status_code != 200:
                response.failure(
                    f"Error al enviar el formulario de filtrado: {response.status_code} - {response.text}"
                )
            else:
                response.success()
                print(f"Respuesta exitosa: {response.json()}")

    @task(3)
    def advanced_filtering_features_blank(self):
        with self.client.post(
            "/explore",  # Ruta donde el formulario es procesado
            data=json.dumps({"number_of_features": 7}),  # Datos como JSON
            headers={
                "Content-Type": "application/json"
            },  # Especificar que estamos enviando JSON
            catch_response=True,  # Necesario para manejar la respuesta manualmente
            name="POST /explore (Advanced Filtering features blank)",
        ) as response:
            # Verificar la respuesta y manejar errores
            if response.status_code != 200:
                response.failure(
                    f"Error al enviar el formulario de filtrado: {response.status_code} - {response.text}"
                )
            else:
                response.success()
                print(f"Respuesta exitosa: {response.json()}")

    @task(4)
    def advanced_filtering_models_ok(self):
        with self.client.post(
            "/explore",  # Ruta donde el formulario es procesado
            data=json.dumps({"number_of_models": 5}),  # Datos como JSON
            headers={
                "Content-Type": "application/json"
            },  # Especificar que estamos enviando JSON
            catch_response=True,  # Necesario para manejar la respuesta manualmente
            name="POST /explore (Advanced Filtering models OK)",
        ) as response:
            # Verificar la respuesta y manejar errores
            if response.status_code != 200:
                response.failure(
                    f"Error al enviar el formulario de filtrado: {response.status_code} - {response.text}"
                )
            else:
                response.success()
                print(f"Respuesta exitosa: {response.json()}")

    @task(5)
    def advanced_filtering_models_blank(self):
        with self.client.post(
            "/explore",  # Ruta donde el formulario es procesado
            data=json.dumps({"number_of_models": 7}),  # Datos como JSON
            headers={
                "Content-Type": "application/json"
            },  # Especificar que estamos enviando JSON
            catch_response=True,  # Necesario para manejar la respuesta manualmente
            name="POST /explore (Advanced Filtering models blank)",
        ) as response:
            # Verificar la respuesta y manejar errores
            if response.status_code != 200:
                response.failure(
                    f"Error al enviar el formulario de filtrado: {response.status_code} - {response.text}"
                )
            else:
                response.success()
                print(f"Respuesta exitosa: {response.json()}")
