import flet as ft
import random

APP_NAME = "واژه‌باز"
WORDS = {
    "حیوان": ["شیر", "فیل", "زرافه", "خرس", "پلنگ", "گربه", "خرگوش", "روباه", "دلفین", "پنگوئن"],
    "میوه": ["سیب", "موز", "پرتقال", "انگور", "هندوانه", "کیوی", "انار", "گیلاس"],
    "غذا": ["پیتزا", "کباب", "قرمه‌سبزی", "املت", "ماکارونی", "فلافل", "بستنی"],
    "شهر": ["تهران", "مشهد", "اصفهان", "شیراز", "تبریز", "رشت", "یزد"],
    "کشور": ["ایران", "ترکیه", "فرانسه", "آلمان", "ژاپن", "کانادا", "برزیل"],
    "ورزش": ["فوتبال", "والیبال", "بسکتبال", "شنا", "تنیس", "کشتی"],
    "طبیعت": ["جنگل", "دریا", "آبشار", "کوه", "رنگین‌کمان", "کهکشان"],
    "وسیله": ["دوچرخه", "هواپیما", "تلفن", "رایانه", "یخچال", "قایق"],
    "شغل": ["پزشک", "معلم", "خلبان", "آشپز", "برنامه‌نویس", "عکاس"],
    "گل": ["لاله", "نرگس", "رز", "آفتابگردان", "ارکیده"],
}
ALPHABET = list("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")
BG, PANEL = "#0B1020", "#151D32"
PURPLE, CYAN = "#9B7BFF", "#55D6E8"
TEXT, MUTED = "#F4F5FF", "#A5AEC5"
GREEN, RED, GOLD = "#42D392", "#FF6B82", "#FFC76A"


def main(page: ft.Page):
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=PURPLE, use_material3=True)
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO

    state = {
        "screen": "home", "topic": "حیوان", "word": "", "guessed": set(),
        "wrong": set(), "score": 0, "best": 0, "rounds": 0, "hints": 3,
        "seconds": 60, "time_left": 60, "active": False, "history": []
    }
    timer = {"task": None}

    def card(content, padding=18):
        return ft.Container(
            content=content, padding=padding, bgcolor=PANEL,
            border=ft.border.all(1, "#29334D"), border_radius=22,
            shadow=ft.BoxShadow(blur_radius=22, color="#080B16", offset=ft.Offset(0, 8))
        )

    def label(text, size=14, color=MUTED, weight=ft.FontWeight.NORMAL):
        return ft.Text(text, size=size, color=color, weight=weight, text_align=ft.TextAlign.RIGHT)

    def button(text, icon, handler, color=PURPLE, expand=True):
        return ft.ElevatedButton(
            text, icon=icon, on_click=handler, expand=expand,
            style=ft.ButtonStyle(
                bgcolor=color, color="#FFFFFF",
                padding=ft.Padding.symmetric(horizontal=18, vertical=16),
                shape=ft.RoundedRectangleBorder(radius=15)
            )
        )

    def snack(message):
        page.snack_bar = ft.SnackBar(ft.Text(message, text_align=ft.TextAlign.RIGHT))
        page.snack_bar.open = True
        page.update()

    def stop_timer():
        state["active"] = False
        task = timer.get("task")
        if task and not task.done():
            task.cancel()
        timer["task"] = None

    def go_home(e=None):
        stop_timer()
        state["screen"] = "home"
        render()

    def start_game(e=None):
        state["word"] = random.choice(WORDS[state["topic"]])
        state["guessed"], state["wrong"] = set(), set()
        state["hints"] = 3
        state["time_left"] = state["seconds"]
        state["active"] = True
        state["screen"] = "game"
        state["rounds"] += 1
        render()
        timer["task"] = page.run_task(tick)

    async def tick():
        try:
            while state["active"] and state["screen"] == "game" and state["time_left"] > 0:
                await page.sleep(1)
                if not state["active"]:
                    break
                state["time_left"] -= 1
                if state["time_left"] <= 0:
                    finish(False)
                else:
                    render()
        except Exception:
            pass

    def finish(won):
        if state["screen"] != "game":
            return
        stop_timer()
        if won:
            gained = max(50, state["time_left"] * 5) + max(0, state["hints"]) * 10
            state["score"] += gained
            state["best"] = max(state["best"], state["score"])
        state["history"].append({"word": state["word"], "won": won})
        state["screen"] = "result"
        render()

    def guess(letter):
        if not state["active"] or letter in state["guessed"] or letter in state["wrong"]:
            return
        if letter in state["word"]:
            state["guessed"].add(letter)
            if all(ch in state["guessed"] or ch.isspace() for ch in state["word"]):
                finish(True)
            else:
                render()
        else:
            state["wrong"].add(letter)
            if len(state["wrong"]) >= 6:
                finish(False)
            else:
                render()

    def use_hint(e=None):
        if state["hints"] <= 0 or not state["active"]:
            snack("راهنمایی دیگری باقی نمانده!")
            return
        hidden = [c for c in state["word"] if c not in state["guessed"] and not c.isspace()]
        if not hidden:
            return
        state["hints"] -= 1
        state["guessed"].add(random.choice(hidden))
        if all(ch in state["guessed"] or ch.isspace() for ch in state["word"]):
            finish(True)
        else:
            render()

    def choose_topic(topic):
        state["topic"] = topic
        render()

    def home_screen():
        topic_chips = ft.Row(
            [ft.Container(
                content=ft.Text(t, size=13, weight=ft.FontWeight.W_600),
                padding=ft.Padding.symmetric(horizontal=13, vertical=10), border_radius=30,
                bgcolor=PURPLE if state["topic"] == t else "#202A43",
                border=ft.border.all(1, "#3A4562"),
                on_click=lambda e, x=t: choose_topic(x)
            ) for t in WORDS],
            wrap=True, spacing=8, run_spacing=8, alignment=ft.MainAxisAlignment.END
        )
        return ft.Column([
            ft.Container(height=10),
            ft.Row([
                ft.Container(content=ft.Text("🎯", size=30), padding=12, bgcolor="#242044", border_radius=18),
                ft.Column([ft.Text("واژه‌باز", size=27, weight=ft.FontWeight.BOLD, color=TEXT),
                           label("چالش حدس کلمه • نسخه فارسی", 12)], spacing=2),
                ft.Container(expand=True),
                ft.Icon(ft.Icons.WIFI_OFF_ROUNDED, color=GREEN, size=22)
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(height=12),
            card(ft.Column([
                label("آماده‌ای ذهنت رو به چالش بکشی؟", 15, CYAN, ft.FontWeight.BOLD),
                ft.Text("کلمه را کشف کن!", size=30, weight=ft.FontWeight.BOLD, color=TEXT),
                label("حروف درست را پیدا کن، امتیاز بگیر و رکوردت را بشکن.", 13),
                ft.Row([
                    ft.Container(content=ft.Column([label("امتیاز", 12), ft.Text(str(state["score"]), size=24, weight=ft.FontWeight.BOLD, color=GOLD)], spacing=4), expand=True),
                    ft.Container(content=ft.Column([label("بهترین", 12), ft.Text(str(state["best"]), size=24, weight=ft.FontWeight.BOLD, color=CYAN)], spacing=4), expand=True),
                    ft.Container(content=ft.Column([label("دور بازی", 12), ft.Text(str(state["rounds"]), size=24, weight=ft.FontWeight.BOLD, color=GREEN)], spacing=4), expand=True),
                ]),
            ], spacing=12), padding=22),
            ft.Container(height=6),
            card(ft.Column([
                ft.Row([ft.Text("🎨", size=20), ft.Text("موضوع بازی", size=17, weight=ft.FontWeight.BOLD, color=TEXT)], alignment=ft.MainAxisAlignment.END),
                label("یک دسته را انتخاب کن؛ هر دور کلمه تازه‌ای دارد.", 12),
                topic_chips,
                ft.Divider(color="#2B3550"),
                ft.Row([
                    ft.Text("⏱️ زمان هر دور", size=14, color=TEXT), ft.Container(expand=True),
                    ft.Dropdown(width=130, value=str(state["seconds"]),
                        options=[ft.dropdown.Option("30", "۳۰ ثانیه"), ft.dropdown.Option("60", "۶۰ ثانیه"), ft.dropdown.Option("90", "۹۰ ثانیه")],
                        on_change=lambda e: state.update(seconds=int(e.control.value)))
                ], alignment=ft.MainAxisAlignment.CENTER),
                button("شروع بازی", ft.Icons.PLAY_ARROW_ROUNDED, start_game, PURPLE),
            ], spacing=13)),
            ft.Container(height=6),
            card(ft.Column([
                ft.Row([ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color=GOLD), ft.Text("چطور بازی کنیم؟", size=16, weight=ft.FontWeight.BOLD, color=TEXT)], alignment=ft.MainAxisAlignment.END),
                label("۱. موضوع دلخواهت را انتخاب کن.", 13),
                label("۲. روی حروف بزن تا کلمه را کامل کنی.", 13),
                label("۳. شش اشتباه فرصت داری؛ از راهنمایی هوشمند استفاده کن.", 13),
                label("۴. هرچه سریع‌تر جواب بدهی، امتیاز بیشتری می‌گیری.", 13),
            ], spacing=9)),
            ft.Container(height=20),
            ft.Text("طراحی‌شده برای موبایل • بازی آفلاین", size=11, color="#77829B", text_align=ft.TextAlign.CENTER),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, scroll=ft.ScrollMode.AUTO)

    def game_screen():
        word = state["word"]
        shown = []
        for ch in word:
            if ch in state["guessed"] or ch.isspace():
                shown.append(ft.Container(ft.Text(ch, size=25, weight=ft.FontWeight.BOLD, color=GREEN),
                    width=42, height=52, alignment=ft.alignment.center, bgcolor="#1C3C3A",
                    border=ft.border.all(1, "#347A68"), border_radius=12))
            else:
                shown.append(ft.Container(ft.Text("؟", size=22, color="#8995B0"),
                    width=42, height=52, alignment=ft.alignment.center, bgcolor="#202A43",
                    border=ft.border.all(1, "#3A4562"), border_radius=12))
        alphabet = []
        for ch in ALPHABET:
            used = ch in state["guessed"] or ch in state["wrong"]
            color = GREEN if ch in state["guessed"] else RED if ch in state["wrong"] else "#202A43"
            alphabet.append(ft.Container(
                ft.Text(ch, size=17, weight=ft.FontWeight.BOLD, color="#FFFFFF" if used else TEXT),
                alignment=ft.alignment.center, width=39, height=43,
                bgcolor=color if used else "#202A43",
                border=ft.border.all(1, color if used else "#35415E"), border_radius=11,
                on_click=lambda e, x=ch: guess(x), ink=True
            ))
        remain = 6 - len(state["wrong"])
        return ft.Column([
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_FORWARD_ROUNDED, on_click=go_home, icon_color=TEXT),
                ft.Container(expand=True),
                ft.Text("مرحله حدس", size=17, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.Container(content=ft.Text("آفلاین", size=11, color=GREEN), padding=8, bgcolor="#18352F", border_radius=12)
            ]),
            card(ft.Column([
                ft.Row([
                    ft.Column([label("موضوع", 11), ft.Text(state["topic"], size=16, weight=ft.FontWeight.BOLD, color=CYAN)], spacing=3),
                    ft.Container(expand=True),
                    ft.Column([label("اشتباه باقی‌مانده", 11), ft.Text(str(remain), size=22, weight=ft.FontWeight.BOLD, color=RED if remain <= 2 else GOLD)], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.END)
                ]),
                ft.Container(height=4),
                ft.Stack([
                    ft.Container(width=76, height=76, border_radius=50, border=ft.border.all(5, "#303B55")),
                    ft.Container(width=76, height=76, border_radius=50, border=ft.border.all(5, CYAN if state["time_left"] > 10 else RED), rotate=ft.Rotate(angle=0.2)),
                    ft.Container(width=76, height=76, alignment=ft.alignment.center,
                        content=ft.Column([ft.Text(str(state["time_left"]), size=24, weight=ft.FontWeight.BOLD, color=TEXT), label("ثانیه", 9)], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
                ], alignment=ft.alignment.center),
                ft.Container(height=8),
                ft.Text("کلمه مخفی", size=13, color=MUTED, text_align=ft.TextAlign.CENTER),
                ft.Row(shown, alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=6),
                ft.Row([
                    ft.Container(content=ft.Text(f"💡 {state['hints']} راهنمایی", size=12, color=GOLD), padding=9, bgcolor="#3A2D22", border_radius=12),
                    ft.Container(expand=True),
                    ft.Container(content=ft.Text(f"❌ {len(state['wrong'])} اشتباه", size=12, color=RED), padding=9, bgcolor="#3B2435", border_radius=12)
                ], spacing=8),
            ], spacing=12), padding=18),
            card(ft.Column([
                ft.Text("حرف موردنظرت را انتخاب کن", size=15, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.Row(alphabet, wrap=True, spacing=6, run_spacing=7, alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    button("راهنمایی", ft.Icons.LIGHTBULB_OUTLINE, use_hint, GOLD),
                    button("تسلیم شدن", ft.Icons.FLAG_OUTLINED, lambda e: finish(False), "#39445E")
                ], spacing=10),
            ], spacing=14)),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, scroll=ft.ScrollMode.AUTO)

    def result_screen():
        won = bool(state["history"] and state["history"][-1]["won"])
        return ft.Column([
            ft.Container(height=35),
            ft.Container(content=ft.Text("🏆" if won else "💫", size=66), alignment=ft.alignment.center),
            ft.Text("آفرین! ترکوندی!" if won else "این دور تموم شد!", size=27, weight=ft.FontWeight.BOLD,
                    color=GREEN if won else GOLD, text_align=ft.TextAlign.CENTER),
            label("کلمه‌ای که دنبالش بودی:", 13),
            ft.Text(state["word"], size=30, weight=ft.FontWeight.BOLD, color=CYAN, text_align=ft.TextAlign.CENTER),
            card(ft.Column([
                ft.Row([label("امتیاز کل", 14), ft.Container(expand=True), ft.Text(str(state["score"]), size=24, color=GOLD, weight=ft.FontWeight.BOLD)]),
                ft.Row([label("اشتباه‌ها", 14), ft.Container(expand=True), ft.Text(str(len(state["wrong"])), size=18, color=RED)]),
                ft.Row([label("راهنمایی باقی‌مانده", 14), ft.Container(expand=True), ft.Text(str(state["hints"]), size=18, color=GREEN)]),
            ], spacing=14)),
            button("دور بعدی", ft.Icons.REPLAY_ROUNDED, start_game, PURPLE),
            button("بازگشت به خانه", ft.Icons.HOME_ROUNDED, go_home, "#293550"),
        ], spacing=18, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def render():
        page.controls.clear()
        content = home_screen() if state["screen"] == "home" else game_screen() if state["screen"] == "game" else result_screen()
        page.add(ft.Container(
            content=ft.Column([
                ft.Container(height=8),
                ft.Row([
                    ft.Container(content=ft.Text("W", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
                                 width=30, height=30, alignment=ft.alignment.center, bgcolor=PURPLE, border_radius=10),
                    ft.Text("WORD PLAY", size=11, weight=ft.FontWeight.BOLD, color="#8D98B3", font_family="Arial"),
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.AUTO_AWESOME, color=GOLD, size=17)
                ]),
                content
            ], spacing=14),
            padding=ft.Padding.only(left=16, right=16, top=12, bottom=24),
            width=560
        ))
        page.update()

    render()


if __name__ == "__main__":
    ft.app(target=main)
