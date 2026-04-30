import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class AxiomScraper(BaseScraper):
    # Axiom Pest Control uses PestPortals.com as their customer portal.
    LOGIN_URL = "https://axiom.pestportals.com/"

    def scrape(self) -> BillData:
        bill = BillData(id="axiom_pest", name="Axiom Pest Control", category="pest")
        try:
            username = os.getenv("AXIOM_USERNAME")
            password = os.getenv("AXIOM_PASSWORD")
            if not username or not password:
                bill.error = "Missing AXIOM_USERNAME or AXIOM_PASSWORD in .env"
                return bill

            self.driver.get(self.LOGIN_URL)
            wait = WebDriverWait(self.driver, 20)

            # TODO: Inspect the PestPortals login form at axiom.pestportals.com and update selectors.
            user_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[type='email'], input[name='email'], input[name='username'], #email, #username")
            ))
            user_field.clear()
            user_field.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], #password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

            wait.until(EC.url_changes(self.LOGIN_URL))

            # TODO: Navigate to the billing section of the PestPortals portal if not shown by default,
            # then update the selectors below to match the balance and due date elements.
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".balance, .amount-due, .outstanding-balance, [data-testid='balance']")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))

            try:
                due_elem = self.driver.find_element(
                    By.CSS_SELECTOR,
                    ".due-date, .next-payment, [data-testid='due-date']"
                )
                bill.due_date = due_elem.text.strip()
            except Exception:
                bill.due_date = None

            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
