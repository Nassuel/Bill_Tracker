import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class RocketLoansScraper(BaseScraper):
    # Rocket Loans servicing portal — try both URLs; the servicing portal is the active one.
    LOGIN_URL = "https://servicing.rocketloans.com/"

    def scrape(self) -> BillData:
        bill = BillData(id="rocket_loans", name="Rocket Loans (Mortgage)", category="mortgage")
        try:
            username = os.getenv("MORTGAGE_USERNAME")
            password = os.getenv("MORTGAGE_PASSWORD")
            if not username or not password:
                bill.error = "Missing MORTGAGE_USERNAME or MORTGAGE_PASSWORD in .env"
                return bill

            self.driver.get(self.LOGIN_URL)
            wait = WebDriverWait(self.driver, 20)

            # TODO: Inspect the Rocket Loans / Rocket Account login form and update these selectors.
            # The servicing portal may redirect to rocketloans.com/login or accounts.rocket.com.
            user_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[type='email'], input[name='email'], input[name='username'], #email, #username")
            ))
            user_field.clear()
            user_field.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], #password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

            wait.until(EC.url_changes(self.LOGIN_URL))

            # TODO: Navigate to the payment / loan details page and update selectors below.
            # Rocket Mortgage shows "Next Payment Due" and amount on the dashboard.
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "[data-testid='next-payment-amount'], .next-payment-amount, "
                 ".payment-amount, .amount-due")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))

            due_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='next-payment-date'], .next-payment-date, .due-date, .payment-due"
            )
            bill.due_date = due_elem.text.strip()
            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
