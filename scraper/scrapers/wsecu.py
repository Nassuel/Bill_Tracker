import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class WSECUScraper(BaseScraper):
    LOGIN_URL = "https://my.wsecu.org/signin"

    def scrape(self) -> BillData:
        bill = BillData(id="wsecu_car", name="WSECU (Car Payment)", category="auto")
        try:
            username = os.getenv("CAR_PAYMENT_USERNAME")
            password = os.getenv("CAR_PAYMENT_PASSWORD")
            if not username or not password:
                bill.error = "Missing CAR_PAYMENT_USERNAME or CAR_PAYMENT_PASSWORD in .env"
                return bill

            self.driver.get(self.LOGIN_URL)
            wait = WebDriverWait(self.driver, 20)

            # TODO: Inspect the WSECU login form at my.wsecu.org/signin and update selectors.
            # WSECU may use member number instead of email for the username field.
            user_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[name='username'], input[name='userId'], #username, #userId, #memberNumber")
            ))
            user_field.clear()
            user_field.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], #password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

            wait.until(EC.url_changes(self.LOGIN_URL))

            # WSECU shows all accounts on the dashboard. We need the auto loan account.
            # TODO: Navigate to the auto loan account details page. You may need to click on the
            # loan account link from the accounts list. Update the selectors below once you've
            # confirmed the page structure.
            #
            # Example: find the auto loan row and click it
            # loan_link = wait.until(EC.element_to_be_clickable(
            #     (By.XPATH, "//a[contains(text(), 'Auto') or contains(text(), 'Loan')]")
            # ))
            # loan_link.click()

            # TODO: Update selector for the next payment amount on the loan detail page.
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".payment-amount, .next-payment, .amount-due, [data-label='Payment Amount']")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))

            # TODO: Update selector for the next payment due date.
            due_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                ".due-date, .next-due, [data-label='Due Date'], .payment-due-date"
            )
            bill.due_date = due_elem.text.strip()
            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
