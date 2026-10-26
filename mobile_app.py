import json
import urllib.request
import flet as ft

# استبدل هذا الرابط برابط الـ Raw للملف app_data.json على مستودعك في GitHub
DATA_URL = (
    "https://raw.githubusercontent.com/alaa1124668/RiderApp/main/app_data.json"
)


def main(page: ft.Page):
  page.title = "Rider Live Operations"
  page.theme_mode = ft.ThemeMode.DARK
  page.vertical_alignment = ft.MainAxisAlignment.START
  page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
  page.padding = 15

  riders_list = []

  def load_data():
    nonlocal riders_list
    try:
      # سحب البيانات أوتوماتيك من الرابط السحابي مباشرة
      req = urllib.request.Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
      with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
        riders_list = data.get("riders", [])
    except Exception as e:
      print("Error fetching cloud data:", e)

  load_data()

  search_field = ft.TextField(
      label="ابحث باسم المندوب أو الزون...",
      prefix_icon=ft.icons.search,
      border_radius=10,
      text_size=14,
      on_change=lambda e: filter_list(e.data),
  )

  cards_column = ft.ListView(expand=True, spacing=10, padding=5)

  def update_cards(data_to_show):
    cards_column.controls.clear()
    if not data_to_show:
      cards_column.controls.append(
          ft.Text(
              "لا توجد بيانات متاحة حالياً. تأكد من اتصال الإنترنت!",
              italic=True,
              color=ft.colors.GREY_400,
          )
      )
    else:
      for r in data_to_show:
        name = r.get("name", "Unknown")
        phone = r.get("phone_number", "N/A")
        status = r.get("status", "N/A")
        zone_info = r.get("zone", {})
        zone_name = zone_info.get("name", "General") if zone_info else "General"

        deliv = r.get("deliveries_info", {})
        completed = deliv.get("completed_deliveries_count", 0)
        accepted = deliv.get("accepted_deliveries_count", 0)

        wallet = r.get("wallet_info", {})
        balance = wallet.get("balance", 0.0)

        status_color = (
            ft.colors.GREEN_400 if status == "working" else ft.colors.ORANGE_400
        )

        card = ft.Container(
            content=ft.Column([
                ft.Row(
                    [
                        ft.Text(
                            name,
                            weight=ft.FontWeight.BOLD,
                            size=15,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Text(
                                status, size=11, color=ft.colors.WHITE
                            ),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            border_radius=5,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=5, color=ft.colors.GREY_800),
                ft.Text(
                    f"📞 {phone}  |  📍 الزون: {zone_name}",
                    size=12,
                    color=ft.colors.GREY_300,
                ),
                ft.Text(
                    f"📦 مقبولة: {accepted} | مكتملة: {completed}  |  💰 المديونية:"
                    f" {balance} ج.م",
                    size=12,
                    color=ft.colors.GREY_300,
                ),
            ]),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=12,
            border_radius=10,
        )
        cards_column.controls.append(card)
    page.update()

  def filter_list(query):
    query = query.strip().lower()
    if not query:
      update_cards(riders_list)
      return

    filtered = [
        r
        for r in riders_list
        if query in r.get("name", "").lower()
        or query in r.get("phone_number", "").lower()
        or query in r.get("zone", {}).get("name", "").lower()
    ]
    update_cards(filtered)

  def refresh_clicked(e):
    load_data()
    filter_list(search_field.value)
    page.snack_bar = ft.SnackBar(ft.Text("تم تحديث البيانات من السحابة بنجاح!"))
    page.snack_bar.open = True
    page.update()

  header = ft.Row(
      [
          ft.Text(
              "🚀 Rider Live App",
              size=20,
              weight=ft.FontWeight.BOLD,
          ),
          ft.IconButton(
              icon=ft.icons.REFRESH,
              icon_color=ft.colors.GREEN_400,
              tooltip="تحديث",
              on_click=refresh_clicked,
          ),
      ],
      alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
  )

  page.add(header, search_field, ft.Divider(height=10), cards_column)
  update_cards(riders_list)


if __name__ == "__main__":
  ft.run(main)
