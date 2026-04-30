import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class SnohomishPUDScraper(BaseScraper):
    LOGIN_URL = "https://my.snopud.com/"

    def scrape(self) -> BillData:
        bill = BillData(id="snohomish_pud", name="Snohomish PUD (Power)", category="electric")
        try:
            username = os.getenv("SNOHOMISH_PUD_USERNAME")
            password = os.getenv("SNOHOMISH_PUD_PASSWORD")
            if not username or not password:
                bill.error = "Missing SNOHOMISH_PUD_USERNAME or SNOHOMISH_PUD_PASSWORD in .env"
                return bill

            self.driver.get(self.LOGIN_URL)
            wait = WebDriverWait(self.driver, 20)

            # TODO: Inspect the MySnoPUD login page and update these selectors.
            # The portal at my.snopud.com may use account number instead of email.
            user_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[name='username'], input[name='email'], input[type='email'], #username, #email")
            ))
            user_field.clear()
            user_field.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], #password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

            wait.until(EC.url_changes(self.LOGIN_URL))

            # TODO: Navigate to the billing/account summary page if not redirected automatically,
            # then update the selectors below to match the balance and due date elements.
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".current-balance, .amount-due, .balance-due, [data-testid='balance']")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))

            due_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                ".due-date, .payment-due, [data-testid='due-date']"
            )
            bill.due_date = due_elem.text.strip()
            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
