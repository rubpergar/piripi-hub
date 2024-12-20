# Generated by Selenium IDE
import time
import secrets
import string
from core.selenium.common import initialize_driver
from selenium.webdriver.common.by import By


def generate_random_email():
    return (
        "".join(
            secrets.choice(string.ascii_lowercase + string.digits) for i in range(10)
        )
        + "@example.com"
    )


class TestPublicdata:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.driver.maximize_window()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_publicdata(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 3").click()
        self.driver.find_element(By.LINK_TEXT, "Doe, John").click()
        self.driver.find_element(By.LINK_TEXT, "Home").click()
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        self.driver.find_element(By.LINK_TEXT, "Doe, Jane").click()
        time.sleep(2)
        alert_heading = self.driver.find_element(By.CLASS_NAME, "alert-heading")
        alert_message = self.driver.find_element(
            By.CSS_SELECTOR, "p[style='margin-bottom: 0px']"
        )
        assert "Error" in alert_heading.text
        assert alert_message.text == "User data is not public"
        time.sleep(2)


class TestPublicdatafalsesignup:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.driver.maximize_window()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_publicdatafalsesignup(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.find_element(By.LINK_TEXT, "Sign Up").click()
        self.driver.find_element(By.ID, "name").click()
        self.driver.find_element(By.ID, "name").send_keys("Javier")
        self.driver.find_element(By.ID, "surname").click()
        self.driver.find_element(By.ID, "surname").send_keys("Nunes")
        self.driver.find_element(By.ID, "email").click()
        email = generate_random_email()
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.CLASS_NAME, "text-dark").click()
        self.driver.find_element(By.LINK_TEXT, "My profile").click()
        time.sleep(2)


class TestPublicdatatruesignup:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.driver.maximize_window()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_publicdatatruesignup(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.find_element(By.LINK_TEXT, "Sign Up").click()
        self.driver.find_element(By.ID, "name").click()
        self.driver.find_element(By.ID, "name").send_keys("Javier2")
        self.driver.find_element(By.ID, "surname").click()
        self.driver.find_element(By.ID, "surname").send_keys("Nunes2")
        self.driver.find_element(By.ID, "email").click()
        email = generate_random_email()
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "public_data").click()
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.CLASS_NAME, "text-dark").click()
        self.driver.find_element(By.LINK_TEXT, "My profile").click()
        time.sleep(2)


class TestPublicdataedit:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.driver.maximize_window()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_publicdataedit(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.CLASS_NAME, "text-dark").click()
        self.driver.find_element(By.LINK_TEXT, "My profile").click()
        self.driver.find_element(By.LINK_TEXT, "Edit profile").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "public_data").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.CLASS_NAME, "text-dark").click()
        self.driver.find_element(By.LINK_TEXT, "My profile").click()
        self.driver.find_element(By.LINK_TEXT, "Edit profile").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "public_data").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "submit").click()
        time.sleep(2)
