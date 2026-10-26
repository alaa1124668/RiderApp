import json
import os
import time
from selenium import webdriver

LIVE_URL = "https://eg.me.logisticsbackoffice.com/dashboard/rooster/live-3pl"

options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
profile_path = os.path.join(os.getcwd(), "my_chrome_profile")
options.add_argument(f"--user-data-dir={profile_path}")


def get_token_from_storage(drv):
  return drv.execute_script("""
        const stores = [window.localStorage, window.sessionStorage];
        for (const s of stores) {
          for (let i = 0; i < s.length; i++) {
            const v = s.getItem(s.key(i)) || "";
            if (/^eyJ[\\w-]+\\.[\\w-]+\\.[\\w-]+$/.test(v)) return "Bearer " + v;
            try {
              const o = JSON.parse(v);
              for (const key of ["access_token", "accessToken", "token", "id_token"]) {
                if (o && typeof o[key] === "string" && o[key].startsWith("eyJ"))
                  return "Bearer " + o[key];
              }
            } catch (e) {}
          }
        }
        return null;
        """)


JS_FETCH_ALL_PAGES = """
const auth = arguments[0];
const done = arguments[arguments.length - 1];

(async () => {
  try {
    const headers = { accept: "application/json" };
    if (auth) headers["authorization"] = auth;
    
    const baseUrl = "https://eg.me.logisticsbackoffice.com";

    const resZones = await fetch(baseUrl + '/api/rider-live-operations/v1/external/city/1/zones', { credentials: 'include', headers });
    const zonesData = resZones.ok ? await resZones.json() : [];

    const resVehicles = await fetch(baseUrl + '/api/rider-live-operations/v1/external/city/1/vehicle-types', { credentials: 'include', headers });
    const vehiclesData = resVehicles.ok ? await resVehicles.json() : [];

    let allRiders = [];
    let page = 0;
    let totalPages = 1;

    while (page < totalPages) {
      const res = await fetch(baseUrl + `/api/rider-live-operations/v1/external/city/1/riders?page=${page}&size=50`, { credentials: 'include', headers });
      if (!res.ok) break;
      const json = await res.json();
      
      let list = [];
      if (Array.isArray(json)) {
        list = json;
        totalPages = 1;
      } else if (json && json.content) {
        list = json.content;
        totalPages = json.total_pages || 1;
      } else if (json && json.data) {
        list = json.data;
        totalPages = json.total_pages || 1;
      }

      if (list.length > 0) {
        allRiders.push(...list);
      } else {
        break;
      }

      page++;
      if (page > 100) break; 
    }

    done({
      success: true,
      total_riders: allRiders.length,
      zones: zonesData,
      vehicles: vehiclesData,
      riders: allRiders
    });

  } catch (e) {
    done({ success: false, error: String(e) });
  }
})();
"""

UPDATE_INTERVAL = 300  # 5 دقائق

print("=== Background Auto-Updater Started ===")
driver = None

try:
  driver = webdriver.Chrome(options=options)
  driver.set_script_timeout(180)
  driver.get(LIVE_URL)
  time.sleep(8)

  while True:
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{current_time}] Updating rider data from server...")
    try:
      auth = get_token_from_storage(driver)
      result = driver.execute_async_script(JS_FETCH_ALL_PAGES, auth)

      if result and result.get("success"):
        with open("app_data.json", "w", encoding="utf-8") as f:
          json.dump(result, f, ensure_ascii=False, indent=4)
        print(
            "--> Success! Updated"
            f" {result.get('total_riders')} riders into app_data.json"
        )
      else:
        print("--> Fetch failed, retrying next cycle...", result)
    except Exception as inner_e:
      print("--> Error during fetch cycle:", inner_e)
      try:
        driver.get(LIVE_URL)
        time.sleep(5)
      except:
        pass

    print(
        f"Waiting {UPDATE_INTERVAL // 60} minutes for the next update..."
    )
    time.sleep(UPDATE_INTERVAL)

except Exception as e:
  print("Critical Error:", e)
finally:
  if driver:
    driver.quit()