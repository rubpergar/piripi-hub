from locust import HttpUser, TaskSet, task
from core.locust.common import get_csrf_token, fake
from core.environment.host import get_host_for_locust_testing


class SignupBehavior(TaskSet):
    def on_start(self):
        self.signup()

    @task
    def signup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)

        response = self.client.post("/signup", data={
            "email": fake.email(),
            "password": fake.password(),
            "csrf_token": csrf_token
        })
        if response.status_code != 200:
            print(f"Signup failed: {response.status_code}")


class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    @task
    def ensure_logged_out(self):
        response = self.client.get("/logout")
        if response.status_code != 200:
            print(f"Logout failed or no active session: {response.status_code}")

    @task
    def login(self):
        response = self.client.get("/login")
        if response.status_code != 200 or "Login" not in response.text:
            print("Already logged in or unexpected response, redirecting to logout")
            self.ensure_logged_out()
            response = self.client.get("/login")

        csrf_token = get_csrf_token(response)

        response = self.client.post("/login", data={
            "email": 'user1@example.com',
            "password": '1234',
            "csrf_token": csrf_token
        })
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")

class PasswordRecoveryBehavior(TaskSet):

    @task(1)
    def get_recover_password(self):
        # Obtiene el formulario de recuperación de contraseña
        response = self.client.get("/recover_password", name = "GET /recover_password")
        if response.status_code != 200:
            print(f"Failed to load password recovery page: {response.status_code}")
            return

        # Obtiene el token CSRF del formulario
        
    @task(2)
    def post_recover_password(self):
        response = self.client.get("/recover_password")

        csrf_token = get_csrf_token(response)

        # Envía la solicitud de recuperación de contraseña
        recovery_email = fake.email()
        response = self.client.post("/recover_password", data={
            "email": recovery_email,
            "csrf_token": csrf_token
        },name = "POST /recover_password" 
        )

        if response.status_code == 200:
            print(f"Password recovery initiated for {recovery_email}")
        else:
            print(f"Password recovery failed for {recovery_email}: {response.status_code}")


class AuthUser(HttpUser):
    tasks = [SignupBehavior, LoginBehavior, PasswordRecoveryBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
