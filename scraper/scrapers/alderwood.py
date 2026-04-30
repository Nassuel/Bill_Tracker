import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class AlderwoodScraper(BaseScraper):
    # awwd.com redirects to their payment/account portal; verify the login URL by navigating there.
    LOGIN_URL = "https://awwd.com/customers/paying-my-bill/"

    def scrape(self) -> BillData:
        bill = BillData(
            id="alderwood_wastewater",
            name="Alderwood Water & Wastewater",
            category="water",
        )
        try:
            username = os.getenv("ALDERWOOD_USERNAME")
            password = os.getenv("ALDERWOOD_PASSWORD")
            if not username or not password:
                bill.error = "Missing ALDERWOOD_USERNAME or ALDERWOOD_PASSWORD in .env"
                return bill

            self.driver.get(self.LOGIN_URL)
            wait = WebDriverWait(self.driver, 20)

            # Alderwood uses a third-party payment portal (often via Invoice Cloud or similar).
            # TODO: Click the "Pay Online" or "My Account" link on the page first if it redirects
            # to a login form, then update the selectors below to match that form.
            user_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[type='email'], input[name='username'], input[name='email'], #email, #username")
            ))
            user_field.clear()
            user_field.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], #password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

            wait.until(EC.url_changes(self.LOGIN_URL))

            # TODO: Update selectors for the balance and due date on the AWWD account page.
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".amount-due, .current-balance, .balance, [data-label='Amount Due']")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))

            due_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                ".due-date, .payment-due, [data-label='Due Date']"
            )
            bill.due_date = due_elem.text.strip()
            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
