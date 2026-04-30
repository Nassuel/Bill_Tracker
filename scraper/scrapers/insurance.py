import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class InsuranceScraper(BaseScraper):
    # TODO: Set LOGIN_URL to your insurance provider's login page.
    # Common providers: Allstate, State Farm, USAA, Farmers, Liberty Mutual, etc.
    # Example: "https://account.allstate.com/anon/login/login.aspx"
    LOGIN_URL = os.environ.get("INSURANCE_LOGIN_URL", "")

    def scrape(self) -> BillData:
        bill = BillData(id="insurance", name="Car & Home Insurance (Umbrella)", category="insurance")
        try:
            if not self.LOGIN_URL:
                bill.error = (
                    "Set INSURANCE_LOGIN_URL in .env to your insurer's login page, "
                    "then update the selectors in scraper/scrapers/insurance.py"
                )
                return bill

            username = os.getenv("INSURANCE_USERNAME")
            password = os.getenv("INSURANCE_PASSWORD")
            if not username or not password:
                bill.error = "Missing INSURANCE_USERNAME or INSURANCE_PASSWORD in .env"
                return bill

            self.driver.get(self.LOGIN_URL)
            wait = WebDriverWait(self.driver, 20)

            # TODO: Inspect your insurer's login form and update these selectors.
            user_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[type='email'], input[name='email'], input[name='username'], #email, #username")
            ))
            user_field.clear()
            user_field.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], #password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

            wait.until(EC.url_changes(self.LOGIN_URL))

            # TODO: Navigate to the billing/policy page and update the selectors below.
            # Insurance portals vary widely; you may need multiple steps to reach billing info.
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".amount-due, .premium-due, .next-payment, .balance-due")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))

            try:
                due_elem = self.driver.find_element(
                    By.CSS_SELECTOR,
                    ".due-date, .payment-due, .next-payment-date"
                )
                bill.due_date = due_elem.text.strip()
            except Exception:
                bill.due_date = None

            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
