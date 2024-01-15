# Bot for https://orteil.dashnet.org/experiments/cookie/
# Using SELENIUM
# Author: Michael Sumaya
import pathlib
import threading
import time
from datetime import datetime as dt, timedelta as td
from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec, wait

HOME_FOLDER = "."
GAME_URL = "https://orteil.dashnet.org/experiments/cookie/"

# Save options
SAVE_PROGRESS = True
SAVE_INTERVAL = 60
SAVE_DATA = pathlib.Path(HOME_FOLDER, "save_data.txt")

# Game options
CLICK_INTERVAL = 0
BUY_INTERVAL = 30
BUY_CLICK_SPEED = 0.5
CPS_INTERVAL = 15

# Store IDs
STORE_IDS = [
    "buyElder Pledge",
    "buyTime machine",
    "buyPortal",
    "buyAlchemy lab",
    "buyShipment",
    "buyMine",
    "buyFactory",
    "buyGrandma",
    "buyCursor"
]


def buy_items(browser) -> None:
    """Auto-buy upgrades using current money"""
    # Check current money
    bank = get_money(browser)
    while bank > 0:
        # bank = get_money(browser)
        old_value = bank
        store = get_store_items(browser)
        for item in store:
            if bank >= item["price"]:
                if item["entry"].is_displayed():
                    item["entry"].click()
                    bank -= item["price"]
                    print_log("Bought: %s for %s | Money left: %s" %
                              (item['description'],
                               item['price'],
                               bank),
                              )
                    # Need this to avoid stale element
                    time.sleep(BUY_CLICK_SPEED)
                    break
        if bank == old_value:
            # Nothing bought from previous cycle
            # exit buying
            break
    # Setup new thread
    print_log(f"Next buy schedule after {BUY_INTERVAL} seconds...")
    threading.Timer(
        BUY_INTERVAL,
        buy_items,
        [browser],
    ).start()


def export_save(browser) -> None:
    """Get save string directly from game function"""
    save_function = "return MakeSaveString()"
    save_data = browser.execute_script(save_function)
    print_log(f"Save Data: {save_data}")
    with open(SAVE_DATA, "wt") as savefile:
        savefile.write(save_data)
    threading.Timer(
        SAVE_INTERVAL,
        export_save,
        [browser],
    ).start()


def import_save(browser) -> None:
    """Use latest progress from save_data.txt"""
    id = "importSave"
    try:
        with open(SAVE_DATA) as savefile:
            sdata = savefile.readlines()
        import_link = browser.find_element(by=By.ID, value=id)
        import_link.click()
        waiter = wait.WebDriverWait(browser, timeout=2)
        waiter.until(ec.alert_is_present())
        import_dialog = Alert(browser)
        import_dialog.send_keys(sdata[0])
        import_dialog.accept()
    except:
        print_log("import_save: Unable to import save file")


def get_money(browser) -> int:
    """Get current money"""
    id = "money"
    try:
        element = browser.find_element(by=By.ID, value=id).text
        money = str(element).replace(",", "").strip()
        current_money = int(money)
        return current_money
    except:
        print_log("get_money: Unable to extract money value.")
        return 0


def get_store_items(browser) -> list:
    """Get store details and save in memory"""
    global STORE_IDS
    store = []
    for id in STORE_IDS:
        store_item = {}
        store_element = browser.find_element(by=By.ID, value=id)
        if store_element.is_displayed():
            store_item["entry"] = store_element
            store_text = str(store_item["entry"].text).split("-")
            store_item["description"] = store_text[0].strip()
            store_item["price"] = int(store_text[1].split(
                "\n")[0].strip().replace(",", ""))
            store.append(store_item)
    if len(store) > 0:
        sorted_store = sorted(store, key=lambda x: x["price"], reverse=True)
    if sorted_store:
        return sorted_store
    else:
        return None


def log_time() -> str:
    """Utility: Get date and time as string"""
    ts = dt.timestamp(dt.now())
    date_time = dt.fromtimestamp(ts)
    str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
    return str_date_time


def print_cps(browser):
    """Shows current CPS in log"""
    try:
        element = browser.find_element(by=By.ID, value="cps").text
        cps = element.split(":")[1].strip()
    except:
        cps = ""
    finally:
        print_log(f"Current CPS: {cps}")
        threading.Timer(
            CPS_INTERVAL,
            print_cps,
            [browser],
        ).start()


def print_log(msg: str) -> None:
    """Utility: Shows message in terminal with date and time"""
    print(f"{log_time()} {msg}")


if __name__ == "__main__":
    browser = webdriver.Chrome()
    browser.get(GAME_URL)

    print_log("Time to get cookie-ing in...")
    for i in range(5, 0, -1):
        print_log(i)
        time.sleep(1)

    # Import save file first
    if SAVE_PROGRESS:
        import_save(browser)

    # Get cookie
    cookie = browser.find_element(by=By.ID, value="cookie")

    # THREADS
    # Use threading for buying goods
    buy_items(browser)
    # Export save data to log
    if SAVE_PROGRESS:
        export_save(browser)
    # Schedule CPS display
    print_cps(browser)

    while True:
        try:
            # Click cookie to get money
            cookie.click()

            # Pause
            if CLICK_INTERVAL > 0:
                time.sleep(CLICK_INTERVAL)
        except:
            break
