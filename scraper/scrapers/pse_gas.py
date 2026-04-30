import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class PSEGasScraper(BaseScraper):
    # PSE redirects to its SSO login; navigate via the account page
    LOGIN_URL = "https://www.pse.com/en/account-and-billing/my-account"

    def scrape(self) -> BillData:
        bill = BillData(id="pse_gas", name="Puget Sound Energy (Gas)", category="gas")
        try:
            username = os.getenv("PSE_USERNAME")
            password = os.getenv("PSE_PASSWORD")
            if not username or not password:
                bill.error = "Missing PSE_USERNAME or PSE_PASSWORD in .env"
                return bill

            self.driver.get(self.LOGIN_URL)
            wait = WebDriverWait(self.driver, 20)

            # TODO: After opening PSE in your browser and logging in, inspect the login form
            # with DevTools → Elements to find the correct input IDs/names and button selector.
            email_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='email'], input[name='email'], #email, input[name='username']")
            ))
            email_field.clear()
            email_field.send_keys(username)

            self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], #password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

            # Wait until we leave the login page
            wait.until(EC.url_contains("/account"))

            # TODO: Inspect the PSE account dashboard for the balance element.
            # Common patterns: data-testid="balance-amount", class containing "balance" or "amount-due".
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "[data-testid='balance-amount'], .current-balance, .amount-due, .balance-amount")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))

            # TODO: Update selector for the due date shown on the dashboard.
            due_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='due-date'], .due-date, .payment-due-date"
            )
            bill.due_date = due_elem.text.strip()
            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
