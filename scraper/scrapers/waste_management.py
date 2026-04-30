import os
import re
import uuid

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper, BillData


class WasteManagementScraper(BaseScraper):
    LOGIN_URL = "https://www.wm.com/us/en/user/login"
    API_BASE = "https://api.wm.com/v1"

    def scrape(self) -> BillData:
        bill = BillData(id="waste_management", name="Waste Management (Trash)", category="trash")
        try:
            username = os.getenv("WASTE_MANAGEMENT_USERNAME")
            password = os.getenv("WASTE_MANAGEMENT_PASSWORD")
            if not username or not password:
                bill.error = "Missing WASTE_MANAGEMENT_USERNAME or WASTE_MANAGEMENT_PASSWORD in .env"
                return bill

            self.driver.get(self.LOGIN_URL)
            wait = WebDriverWait(self.driver, 20)

            # TODO: Inspect WM login form in DevTools and update selectors if these don't match.
            email_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='email'], #email, input[name='username']")
            ))
            email_field.clear()
            email_field.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], #password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            wait.until(EC.url_changes(self.LOGIN_URL))

            # Extract the auth token and customer ID that the WM SPA stores in the browser.
            # TODO: After logging in manually, open DevTools → Application → Local Storage and
            # find the exact key names WM uses for the access token and customer ID, then update below.
            token = self.driver.execute_script("""
                return localStorage.getItem('access_token')
                    || localStorage.getItem('authToken')
                    || localStorage.getItem('id_token')
                    || sessionStorage.getItem('access_token')
                    || null;
            """)

            customer_id = self.driver.execute_script("""
                return localStorage.getItem('customerId')
                    || localStorage.getItem('customer_id')
                    || null;
            """)

            if token and customer_id:
                # Use the official WM REST API with the extracted session credentials.
                # ClientId is issued by WM; find it in DevTools → Network tab → request headers
                # after login, then set WM_CLIENT_ID in your .env file.
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Request-Tracking-Id": str(uuid.uuid4()),
                    "ClientId": os.getenv("WM_CLIENT_ID", ""),
                    "Accept": "application/json",
                }
                resp = requests.get(
                    f"{self.API_BASE}/customers/{customer_id}/balance",
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()

                # Response shape: {"balance": [{"type": "total", "amount": "45.00"}, ...]}
                for entry in data.get("balance", []):
                    if entry.get("type", "").lower() == "total":
                        bill.amount_due = float(entry.get("amount", 0))
                        break

                bill.due_date = data.get("due_date")
                bill.status = "pending" if bill.amount_due and bill.amount_due > 0 else "paid"
            else:
                # Fallback: scrape the balance directly from the WM account page.
                bill = self._scrape_from_page(bill, wait)

        except Exception as e:
            bill.error = str(e)
        return bill

    def _scrape_from_page(self, bill: BillData, wait: WebDriverWait) -> BillData:
        """Fallback path: read balance directly from the WM dashboard HTML."""
        try:
            wait.until(EC.url_contains("mywm"))
            # TODO: Inspect the WM dashboard and update this selector for the balance element.
            amount_elem = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".balance-amount, .amount-due, [data-testid='balance']")
            ))
            bill.amount_due = float(re.sub(r"[^\d.]", "", amount_elem.text))
            bill.status = "pending"
        except Exception as e:
            bill.error = str(e)
        return bill
