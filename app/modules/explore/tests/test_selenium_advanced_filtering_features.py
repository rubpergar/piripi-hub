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


class TestTestseleniumadvancedfiltering2:
    def setup_method(self, method):
        self.driver = webdriver.Chrome()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_testseleniumadvancedfiltering2(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.set_window_size(1840, 1048)
        self.driver.get("http://127.0.0.1:5000/explore")
        self.driver.find_element(By.ID, "number_of_features").click()
        self.driver.find_element(By.ID, "number_of_features").send_keys("7")
        self.driver.find_element(By.ID, "number_of_features").send_keys(Keys.ENTER)
        element = self.driver.find_element(By.ID, "results_not_found")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.ID, "results_not_found")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.ID, "results_not_found")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        self.driver.find_element(By.CSS_SELECTOR, ".container > .row").click()
        self.driver.find_element(By.ID, "number_of_features").send_keys("50")
        self.driver.find_element(By.ID, "number_of_features").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "clear-filters").click()
