# Generated by Selenium IDE
from selenium import webdriver
from selenium.webdriver.common.by import By


class TestPublicdata():
    def setup_method(self, method):
        self.driver = webdriver.Chrome()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_publicdata(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.set_window_size(1850, 970)
        self.driver.get("http://127.0.0.1:5000/login")
        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 3").click()
        self.driver.find_element(By.CSS_SELECTOR, "Doe, John").click()
        self.driver.find_element(By.LINK_TEXT, "Home").click()
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        self.driver.find_element(By.LINK_TEXT, "Doe, Jane").click()
        self.driver.close()
