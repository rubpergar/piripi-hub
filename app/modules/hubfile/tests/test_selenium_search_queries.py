# Generated by Selenium IDE
import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


# Test 1: Usar maximizar ventana
class TestDownloadselected1():
    """Prueba que descarga 1 modelo seleccionado"""

    def setup_method(self, method):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()  # Maximizar ventana
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_downloadselected1(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        self.driver.find_element(By.CSS_SELECTOR, ".list-group-item:nth-child(3) .model-checkbox").click()
        self.driver.find_element(By.ID, "downloadSelectedButton").click()


# Test 2: Usar desplazamiento (scrolling)
class TestDownloadselected2():
    """Prueba que descarga 2 modelos seleccionados diferentes"""

    def setup_method(self, method):
        self.driver = webdriver.Chrome()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_downloadselected2(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.set_window_size(1214, 768)

        element = self.driver.find_element(By.LINK_TEXT, "Sample dataset 3")
        self.driver.execute_script("arguments[0].scrollIntoView();", element)  # Desplazamiento
        element.click()

        self.driver.find_element(By.CSS_SELECTOR, ".list-group-item:nth-child(2) .model-checkbox").click()
        self.driver.find_element(By.CSS_SELECTOR, ".list-group-item:nth-child(4) .model-checkbox").click()
        self.driver.find_element(By.ID, "downloadSelectedButton").click()


# Test 3: Usar un tamaño de ventana específico
class TestDownloadselected0():
    """Prueba que descarga 0 modelos seleccionados"""

    def setup_method(self, method):
        self.driver = webdriver.Chrome()
        self.driver.set_window_size(1920, 1080)  # Tamaño específico
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_downloadselected0(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 1").click()
        self.driver.find_element(By.ID, "downloadSelectedButton").click()
        alert_text = self.driver.switch_to.alert.text
        assert alert_text == "No files selected for download."