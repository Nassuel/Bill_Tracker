import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class KingCountyScraper(BaseScraper):
    # King County capacity charge portal — payment requires account number + site number from invoice.
    # This portal may not have a persistent login; you may need account/site numbers instead of user/pass.
    PORTAL_URL = "https://payment.kingcounty.gov/Home/Index?app=CapacityCharge"

    def scrape(self) -> BillData:
        bill = BillData(id="king_county", name="King County Capacity Charge", category="water")
        try:
            username = os.getenv("KING_COUNTY_USERNAME")
            password = os.getenv("KING_COUNTY_PASSWORD")
            if not username or not password:
                bill.error = "Missing KING_COUNTY_USERNAME or KING_COUNTY_PASSWORD in .env"
                return bill

            self.driver.get(self.PORTAL_URL)
            wait = WebDriverWait(self.driver, 20)

            # NOTE: The King County capacity charge portal (payment.kingcounty.gov) uses an
            # account number + site number for lookup rather than a traditional username/password.
            # Set KING_COUNTY_USERNAME = your account number and KING_COUNTY_PASSWORD = site number.
            # TODO: Inspect the portal form and update selectors to match the account/site number fields.
            account_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[name='accountNumber'], input[name='account'], #accountNumber, #account")
            ))
            account_field.clear()
            account_field.send_keys(username)

            site_field = self.driver.find_element(
                By.CSS_SELECTOR,
                "input[name='siteNumber'], input[name='site'], #siteNumber, #site"
            )
            site_field.clear()
            site_field.send_keys(password)

            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()
            wait.until(EC.url_changes(self.PORTAL_URL))

            # TODO: Update selectors for the balance and due date on the lookup results page.
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".amount-due, .balance-due, td.amount, [data-label='Balance']")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))

            due_elem = self.driver.find_element(
                By.CSS_SELECTOR,
                ".due-date, td.due-date, [data-label='Due Date']"
            )
            bill.due_date = due_elem.text.strip()
            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
