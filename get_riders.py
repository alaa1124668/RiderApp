import csv
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

LIVE_URL = "https://eg.me.logisticsbackoffice.com/dashboard/rooster/live-3pl"

options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
profile_path = os.path.join(os.getcwd(), "my_chrome_profile")
options.add_argument(f"--user-data-dir={profile_path}")

driver = webdriver.Chrome(options=options)
driver.set_script_timeout(180)


def get_auth_header(drv):
  found = None
  for entry in drv.get_log("performance"):
    try:
      msg = json.loads(entry["message"])["message"]
      method = msg.get("method")
      params = msg.get("params", {})
      if method == "Network.requestWillBeSentExtraInfo":
        headers = params.get("headers", {})
      elif method == "Network.requestWillBeSent":
        headers = params.get("request", {}).get("headers", {})
      else:
        continue
      for k, v in headers.items():
        if k.lower() == "authorization" and v:
          found = v
    except Exception:
      pass
  return found


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


JS = """
const auth = arguments[0];
const done = arguments[arguments.length - 1];
(async () => {
  const all = [];
  let page = 0, totalPages = 1;
  try {
    while (page < totalPages) {
      const url = `/api/rider-live-operations/v1/external/city/1/riders?page=${page}&size=50`;
      const headers = { accept: "application/json" };
      if (auth) headers["authorization"] = auth;
      const r = await fetch(url, { credentials: "include", headers });
      const text = await r.text();
      if (!r.ok) { done({ error: `HTTP ${r.status}`, body: text.slice(0, 300), data: all }); return; }
      let d;
      try { d = JSON.parse(text); } catch (e) { done({ error: "not JSON", body: text.slice(0, 300), data: all }); return; }
      if (!d || !d.content) { done({ error: "no content key", keys: Object.keys(d || {}), data: all }); return; }
      all.push(...d.content);
      totalPages = d.total_pages || 1;
      page++;
    }
    done({ data: all });
  } catch (e) {
    done({ error: String(e), data: all });
  }
})();
"""

try:
  print("Opening Live 3PL page...")
  driver.get(LIVE_URL)

  print("Waiting for Live 3PL page...")
  WebDriverWait(driver, 300).until(lambda d: "/rooster/live-3pl" in d.current_url)
  WebDriverWait(driver, 60).until(
      lambda d: d.execute_script("return document.readyState") == "complete"
  )
  time.sleep(3)

  # Reload to capture auth
  driver.get_log("performance")
  driver.refresh()
  WebDriverWait(driver, 60).until(
      lambda d: d.execute_script("return document.readyState") == "complete"
  )
  time.sleep(6)

  auth = get_auth_header(driver)
  if not auth:
    auth = get_token_from_storage(driver)

  print("Fetching all riders with full details...")
  result = driver.execute_async_script(JS, auth)

  if isinstance(result, dict) and result.get("data"):
    riders = result.get("data", [])
    print(f"Fetched: {len(riders)} riders")

    path = os.path.join(os.getcwd(), "riders_report.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
      w = csv.writer(f)
      w.writerow([
          "Rider ID",
          "Name",
          "Zone",
          "Wallet",
          "Status",
          "Current Session",
          "Deliveries / Active Orders",
          "Break Time",
          "Time Worked",
          "Late Time",
      ])

      for r in riders:
        start_at = str(r.get("active_shift_started_at", ""))
        end_at = str(r.get("active_shift_ended_at", ""))
        session_str = (
            f"{start_at[11:16]} - {end_at[11:16]}"
            if len(start_at) >= 16 and len(end_at) >= 16
            else "N/A"
        )

        perf = r.get("performance", {})
        deliveries = perf.get("deliveries_count", perf.get("deliveries", 0))
        utr = perf.get("utr", 0)
        orders_info = f"Deliveries: {deliveries} (UTR: {utr})"

        time_spent = perf.get("time_spent", {})
        break_secs = time_spent.get("break_seconds", 0)
        break_mins = (
            f"{int(break_secs // 60)}m {int(break_secs % 60)}s"
            if break_secs
            else "00:00:00"
        )

        worked_secs = time_spent.get("worked_seconds", 0)
        worked_time = (
            f"{int(worked_secs // 3600):02d}:{int((worked_secs % 3600) // 60):02d}:{int(worked_secs % 60):02d}"
            if worked_secs
            else "00:00:00"
        )

        late_secs = time_spent.get("late_seconds", 0)
        late_time = (
            f"00:00:{int(late_secs):02d}" if late_secs else "00:00:00"
        )

        w.writerow([
            r.get("employee_id", ""),
            r.get("name", ""),
            (r.get("zone") or {}).get("name", "N/A"),
            (r.get("wallet_info") or {}).get("balance", 0),
            r.get("status", "unknown"),
            session_str,
            orders_info,
            break_mins,
            worked_time,
            late_time,
        ])

    print("Saved comprehensive report to:", path)
  else:
    print("Error fetching data:", result)

except Exception as e:
  print("Error:", type(e).__name__, e)

input("Press Enter to exit...")