import json
import os
import customtkinter as ctk

# إعدادات مظهر الأبلكيشن
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class RiderApp(ctk.CTk):

  def __init__(self):
    super().__init__()

    self.title("Rider Live Operations - Dashboard")
    self.geometry("1100x700")

    self.riders_data = []
    self.zones_data = []

    # تحميل البيانات لأول مرة
    self.load_data()

    # تصميم الواجهة الرئيسية
    self.create_widgets()

    # تحميل المناديب في القائمة
    self.display_riders(self.riders_data)

  def load_data(self):
    if os.path.exists("app_data.json"):
      try:
        with open("app_data.json", "r", encoding="utf-8") as f:
          data = json.load(f)
          self.riders_data = data.get("riders", [])
          self.zones_data = data.get("zones", [])
      except Exception as e:
        print("Error loading json:", e)

  def create_widgets(self):
    # --- الهيدر العلوي ---
    header_frame = ctk.CTkFrame(self, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=15)

    title_label = ctk.CTkLabel(
        header_frame,
        text="🚀 Rider Live Operations",
        font=ctk.CTkFont(size=22, weight="bold"),
    )
    title_label.pack(side="left")

    self.count_label = ctk.CTkLabel(
        header_frame,
        text=f"إجمالي المناديب: {len(self.riders_data)}",
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    self.count_label.pack(side="right")

    # --- شريط البحث والفلترة ---
    control_frame = ctk.CTkFrame(self, fg_color="transparent")
    control_frame.pack(fill="x", padx=20, pady=5)

    # خانة البحث بالاسم أو البريد
    self.search_entry = ctk.CTkEntry(
        control_frame,
        placeholder_text="🔍 ابحث باسم المندوب أو رقم الموبايل...",
        width=350,
        height=40,
    )
    self.search_entry.pack(side="left", padx=(0, 10))
    self.search_entry.bind("<KeyRelease>", self.filter_riders)

    # زرار التحديث اليدوي
    refresh_btn = ctk.CTkButton(
        control_frame,
        text="🔄 تحديث البيانات",
        command=self.refresh_app,
        height=40,
        fg_color="#2b8a3e",
        hover_color="#237b34",
    )
    refresh_btn.pack(side="right")

    # --- منطقة عرض الكروت (Scrollable Frame) ---
    self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
    self.scroll_frame.pack(
        fill="both", expand=True, padx=20, pady=(15, 20)
    )

  def display_riders(self, riders):
    for widget in self.scroll_frame.winfo_children():
      widget.destroy()

    if not riders:
      no_data_label = ctk.CTkLabel(
          self.scroll_frame,
          text="لا توجد بيانات متاحة حالياً. تأكد من تشغيل سكربت الخلفية!",
          font=ctk.CTkFont(size=14),
      )
      no_data_label.pack(pady=40)
      return

    for r in riders:
      name = r.get("name", "Unknown")
      phone = r.get("phone_number", "N/A")
      status = r.get("status", "N/A")

      zone_info = r.get("zone", {})
      zone_name = zone_info.get("name", "General") if zone_info else "General"

      start_pt = r.get("starting_point", {})
      start_name = (
          start_pt.get("name", "N/A") if start_pt else "N/A"
      )

      deliv_info = r.get("deliveries_info", {})
      completed = deliv_info.get("completed_deliveries_count", 0)
      accepted = deliv_info.get("accepted_deliveries_count", 0)

      wallet = r.get("wallet_info", {})
      balance = wallet.get("balance", 0.0)

      card = ctk.CTkFrame(self.scroll_frame, corner_radius=8)
      card.pack(fill="x", padx=5, pady=6)

      status_color = "#2b8a3e" if status == "working" else "#e67e22"

      info_text = (
          f"👤 {name}\n📞 {phone}  |  📍 الزون: {zone_name} (نقطة: {start_name})\n📦"
          f" المقبولة: {accepted} | المكتملة: {completed}  |  💰 المديونية:"
          f" {balance} ج.م"
      )

      lbl = ctk.CTkLabel(
          card,
          text=info_text,
          justify="left",
          font=ctk.CTkFont(size=13),
      )
      lbl.pack(side="left", padx=15, pady=10)

      badge = ctk.CTkLabel(
          card,
          text=f"  {status}  ",
          fg_color=status_color,
          text_color="white",
          corner_radius=6,
          font=ctk.CTkFont(size=11, weight="bold"),
      )
      badge.pack(side="right", padx=15)

  def filter_riders(self, event=None):
    query = self.search_entry.get().strip().lower()
    if not query:
      self.display_riders(self.riders_data)
      return

    filtered = [
        r
        for r in self.riders_data
        if query in r.get("name", "").lower()
        or query in r.get("phone_number", "").lower()
        or query in r.get("zone", {}).get("name", "").lower()
    ]
    self.display_riders(filtered)

  def refresh_app(self):
    self.load_data()
    self.display_riders(self.riders_data)
    self.count_label.configure(text=f"إجمالي المناديب: {len(self.riders_data)}")


if __name__ == "__main__":
  app = RiderApp()
  app.mainloop()