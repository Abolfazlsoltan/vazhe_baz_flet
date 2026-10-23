"""واژه‌باز: بازی حدس کلمه فارسی"""
import asyncio, hashlib, os, random, sqlite3, unicodedata
from datetime import date
from pathlib import Path
import flet as ft
import httpx

APP_NAME="واژه‌باز"
WORDS={
"حیوان":["شیر","فیل","زرافه","خرس","پلنگ","گربه","خرگوش","روباه","دلفین","پنگوئن","لاک‌پشت","سنجاب"],
"میوه":["سیب","موز","پرتقال","انگور","هندوانه","کیوی","انار","گیلاس","آناناس","آلبالو"],
"غذا":["پیتزا","کباب","قرمه‌سبزی","املت","ماکارونی","فلافل","بستنی","آش‌رشته"],
"شهر":["تهران","مشهد","اصفهان","شیراز","تبریز","رشت","یزد","همدان","کرمانشاه"],
"کشور":["ایران","ترکیه","فرانسه","آلمان","ژاپن","کانادا","برزیل","ایتالیا"],
"ورزش":["فوتبال","والیبال","بسکتبال","شنا","تنیس","کشتی","کاراته"],
"طبیعت":["جنگل","دریا","آبشار","کوه","رنگین‌کمان","کهکشان","آتشفشان"],
"وسیله":["دوچرخه","هواپیما","تلفن","رایانه","یخچال","قایق","موتورسیکلت"],
"شغل":["پزشک","معلم","خلبان","آشپز","برنامه‌نویس","عکاس","معمار"],
"گل":["لاله","نرگس","رز","آفتابگردان","ارکیده","یاس"]}
ALPHABET=list("اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")
BG,PANEL="#071521","#102638"; PURPLE,CYAN="#18B7A4","#63E6D0"
TEXT,MUTED="#F2FBFF","#A4BBC9"; GREEN,RED,GOLD="#5CE0B0","#FF718B","#FFD166"
DATA_DIR = None
DB_PATH = None

def norm(c): return {"أ":"ا","إ":"ا","ٱ":"ا","ك":"ک","ي":"ی","ى":"ی"}.get(c,c)
def display_chars(word):
    return [norm(c) for c in unicodedata.normalize("NFC",word) if not c.isspace() and c not in ("\u200c","\u200d","\ufeff")]
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("CREATE TABLE IF NOT EXISTS stats(id INTEGER PRIMARY KEY CHECK(id=1),score INTEGER DEFAULT 0,best INTEGER DEFAULT 0,rounds INTEGER DEFAULT 0,wins INTEGER DEFAULT 0,losses INTEGER DEFAULT 0)")
        db.execute("INSERT OR IGNORE INTO stats(id) VALUES(1)")
def stats_load():
    init_db()
    with sqlite3.connect(DB_PATH) as db: row=db.execute("SELECT score,best,rounds,wins,losses FROM stats WHERE id=1").fetchone()
    return dict(zip(("score","best","rounds","wins","losses"),row))
def stats_save(won,gain):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("UPDATE stats SET score=score+?,best=MAX(best,?),rounds=rounds+1,wins=wins+?,losses=losses+? WHERE id=1",(gain,gain,int(won),int(not won)))

def main(page:ft.Page):
    global DATA_DIR, DB_PATH
    # Flet provides an app-private writable directory on Android.
    # Path.home() may resolve to the protected /data directory in packaged apps.
    DATA_DIR = Path(os.environ.get("FLET_APP_STORAGE_DATA") or Path.home()) / "vazhe_baz"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "stats.sqlite3"
    page.title=APP_NAME; page.theme_mode=ft.ThemeMode.DARK
    page.theme=ft.Theme(color_scheme_seed=CYAN,use_material3=True)
    page.bgcolor=BG; page.padding=0; page.spacing=0; page.rtl=True; page.scroll=ft.ScrollMode.AUTO
    stats=stats_load()
    s={"screen":"home","topic":"حیوان","seconds":60,"time_left":60,"word":"","guessed":set(),"wrong":[],"hints":3,
       "active":False,"mode":"solo","turn":0,"scores":[0,0],"gain":0,"won":False,"result":"","online_url":"http://127.0.0.1:8000",
       "nickname":"بازیکن","room":"","player_id":"","online":{},"online_error":""}
    tasks={"timer":None,"poll":None}
    client=httpx.AsyncClient(timeout=5)
    def card(c,padding=18):
        return ft.Container(content=c,padding=padding,bgcolor=PANEL,border=ft.Border.all(1,"#29334D"),border_radius=22,
            shadow=ft.BoxShadow(blur_radius=18,color="#080B16",offset=ft.Offset(0,6)))
    def label(t,size=14,color=MUTED,weight=ft.FontWeight.NORMAL):
        return ft.Text(t,size=size,color=color,weight=weight,text_align=ft.TextAlign.RIGHT)
    def btn(t,icon,fn,color=PURPLE,expand=True):
        return ft.Button(content=t,icon=icon,on_click=fn,expand=expand,style=ft.ButtonStyle(bgcolor=color,color="white",
            padding=ft.Padding.symmetric(horizontal=16,vertical=13),shape=ft.RoundedRectangleBorder(radius=14)))
    def snack(t):
        page.snack_bar=ft.SnackBar(ft.Text(t)); page.snack_bar.open=True; page.update()
    def cancel(key):
        task=tasks.get(key)
        if task and not task.done(): task.cancel()
        tasks[key]=None
    def stop_timer():
        s["active"]=False; cancel("timer")
    def home(e=None):
        stop_timer(); cancel("poll"); s["screen"]="home"; render()
    def new_game(mode="solo",e=None):
        stop_timer()
        topic=s["topic"]
        if mode=="daily":
            # معمای روزانه برای همهٔ بازیکنان در همان تاریخ یکسان است.
            pool=[(name,word) for name,items in WORDS.items() for word in items]
            day_seed=hashlib.sha256(date.today().isoformat().encode("utf-8")).digest()
            topic,word=pool[int.from_bytes(day_seed[:4],"big") % len(pool)]
            seconds=90
        else:
            word=random.choice(WORDS[topic]); seconds=s["seconds"]
        s.update(word=word,topic=topic,guessed=set(),wrong=[],hints=3,time_left=seconds,
            active=True,screen="game",mode=mode,turn=0,scores=[0,0],gain=0,won=False)
        render(); tasks["timer"]=page.run_task(tick)
    async def tick():
        try:
            while s["active"] and s["screen"]=="game":
                await asyncio.sleep(1)
                if not s["active"] or s["screen"]!="game": break
                s["time_left"]=max(0,s["time_left"]-1)
                if s["time_left"]==0: finish(False,"زمان تمام شد!")
                else: render()
        except asyncio.CancelledError: raise
        except Exception as exc: print("timer error:",exc)
    def finish(won,message=None):
        if s["screen"]!="game": return
        stop_timer(); gain=(max(50,s["time_left"]*5)+s["hints"]*10) if won else 0
        s["gain"]=gain; s["won"]=won; s["result"]=message or ("آفرین! کلمه را پیدا کردی." if won else "این دور تمام شد!")
        if s["mode"]=="local":
            if won: s["scores"][s["turn"]]+=gain
        else:
            stats_save(won,gain); stats.update(stats_load())
        s["screen"]="result"; render()
    def guess(ch):
        if not s["active"] or ch in s["guessed"] or ch in s["wrong"]: return
        if ch in display_chars(s["word"]):
            s["guessed"].add(ch)
            if all(c in s["guessed"] for c in display_chars(s["word"])): finish(True)
            else: render()
        else:
            s["wrong"].append(ch)
            # با رسیدن تعداد خطاها به تعداد خانه‌های کلمه، بازیکن می‌بازد.
            if len(s["wrong"])>=max(1,len(display_chars(s["word"]))): finish(False,"همهٔ فرصت‌های اشتباه پر شدند!")
            else:
                if s["mode"]=="local": s["turn"]=1-s["turn"]
                render()
    def hint(e=None):
        hidden=[c for c in display_chars(s["word"]) if c not in s["guessed"]]
        if not s["active"]: return
        if s["hints"]<=0: snack("راهنمایی دیگری باقی نمانده!"); return
        if hidden:
            s["hints"]-=1; s["guessed"].add(random.choice(hidden))
            if all(c in s["guessed"] for c in display_chars(s["word"])): finish(True)
            else: render()
    def topic(t): s["topic"]=t; render()
    def home_screen():
        chips=ft.Row([ft.Container(content=ft.Text(t,size=13,weight=ft.FontWeight.W_600),padding=ft.Padding.symmetric(horizontal=12,vertical=9),
            border_radius=28,bgcolor=PURPLE if s["topic"]==t else "#202A43",border=ft.Border.all(1,"#3A4562"),on_click=lambda e,x=t:topic(x)) for t in WORDS],
            wrap=True,spacing=7,run_spacing=7,alignment=ft.MainAxisAlignment.END)
        return ft.Column([
          ft.Row([ft.Text("🎯",size=30),ft.Column([ft.Text("واژه‌باز",size=27,weight=ft.FontWeight.BOLD,color=TEXT),label("چالش حدس کلمه • فارسی",12)],spacing=1),
            ft.Container(expand=True),ft.Icon(ft.Icons.AUTO_AWESOME,color=GOLD)]),
          card(ft.Column([label("آماده‌ای ذهنت را به چالش بکشی؟",14,CYAN,ft.FontWeight.BOLD),ft.Text("کلمه را کشف کن!",size=29,weight=ft.FontWeight.BOLD,color=TEXT),
            label("حروف درست را پیدا کن، امتیاز بگیر و رکوردت را بشکن.",13),
            ft.Row([ft.Column([label("امتیاز کل",12),ft.Text(str(stats["score"]),size=23,color=GOLD,weight=ft.FontWeight.BOLD)],expand=True,spacing=3),
              ft.Column([label("بهترین دور",12),ft.Text(str(stats["best"]),size=23,color=CYAN,weight=ft.FontWeight.BOLD)],expand=True,spacing=3),
              ft.Column([label("بردها",12),ft.Text(str(stats["wins"]),size=23,color=GREEN,weight=ft.FontWeight.BOLD)],expand=True,spacing=3)]),
            ft.Divider(color="#263F50",height=8),
            ft.Row([ft.Column([ft.Text(f"سطح {max(1,stats['score']//500+1)}",size=15,color=CYAN,weight=ft.FontWeight.BOLD),
                label(f"{stats['score']%500} از ۵۰۰ XP تا سطح بعدی",11)],spacing=3,expand=True),
                ft.Container(content=ft.Icon(ft.Icons.AUTO_AWESOME,color=GOLD,size=22),padding=10,bgcolor="#17394A",border_radius=14)]),
            ft.ProgressBar(value=(stats["score"]%500)/500,color=CYAN,bgcolor="#263F50",height=7)],spacing=10),padding=21),
          card(ft.Column([ft.Text("موضوع بازی",size=17,weight=ft.FontWeight.BOLD,color=TEXT),chips,ft.Divider(color="#2B3550"),
            ft.Row([ft.Text("⏱ زمان هر دور",color=TEXT),ft.Container(expand=True),ft.Dropdown(width=130,value=str(s["seconds"]),
              options=[ft.DropdownOption(key="30",text="۳۰ ثانیه"),ft.DropdownOption(key="60",text="۶۰ ثانیه"),ft.DropdownOption(key="90",text="۹۰ ثانیه")],
              on_select=lambda e:s.update(seconds=int(e.control.value)))]),
            btn("شروع تک‌نفره",ft.Icons.PLAY_ARROW_ROUNDED,lambda e:new_game("solo"),PURPLE),
            btn("چالش روزانه • معمای یکسان برای همه",ft.Icons.CALENDAR_TODAY_ROUNDED,lambda e:new_game("daily"),"#176B70"),
            btn("دونفره روی یک دستگاه",ft.Icons.GROUPS_ROUNDED,lambda e:new_game("local"),"#24546B"),
            btn("بازی آنلاین",ft.Icons.PUBLIC_ROUNDED,online_screen_open,"#1D6658")],spacing=12)),
          card(ft.Column([ft.Text("قوانین بازی",size=16,weight=ft.FontWeight.BOLD,color=TEXT),
            label("• حروف اشتباه زیر خانه‌ها از چپ به راست ثبت می‌شوند.",13),
            label("• تعداد خطاهای مجاز برابر تعداد حروف کلمه است.",13),
            label("• «آ»، «ک/ك» و «ی/ي» پشتیبانی می‌شوند.",13),
            label("• امتیاز و آمار پس از بستن برنامه باقی می‌مانند.",13)],spacing=8)),
          ft.Text("واژه‌باز • Python + Flet",size=11,color="#77829B",text_align=ft.TextAlign.CENTER)
        ],spacing=12,horizontal_alignment=ft.CrossAxisAlignment.STRETCH,scroll=ft.ScrollMode.AUTO)
    def game_screen():
        chars=display_chars(s["word"])
        slots=[ft.Container(content=ft.Text(c if c in s["guessed"] else "؟",size=22,weight=ft.FontWeight.BOLD,
            color=GREEN if c in s["guessed"] else "#8995B0"),width=39,height=49,alignment=ft.Alignment.CENTER,
            bgcolor="#1C3C3A" if c in s["guessed"] else "#202A43",border=ft.Border.all(1,"#347A68" if c in s["guessed"] else "#3A4562"),border_radius=10) for c in chars]
        wrong_slots=[ft.Container(content=ft.Text(s["wrong"][i] if i<len(s["wrong"]) else "·",size=17,weight=ft.FontWeight.BOLD,
            color=RED if i<len(s["wrong"]) else "#56617A"),width=33,height=36,alignment=ft.Alignment.CENTER,
            bgcolor="#3B2435" if i<len(s["wrong"]) else "#11192A",border=ft.Border.all(1,"#7B354A" if i<len(s["wrong"]) else "#29334D"),border_radius=8)
            for i in range(len(chars))]
        keys=[]
        for ch in ALPHABET:
            used=ch in s["guessed"] or ch in s["wrong"]; col=GREEN if ch in s["guessed"] else RED if ch in s["wrong"] else "#202A43"
            keys.append(ft.Container(content=ft.Text(ch,size=16,weight=ft.FontWeight.BOLD,color="white" if used else TEXT),
                width=37,height=41,alignment=ft.Alignment.CENTER,bgcolor=col if used else "#202A43",
                border=ft.Border.all(1,col if used else "#35415E"),border_radius=9,on_click=lambda e,x=ch:guess(x),ink=True))
        remain=max(0,len(chars)-len(s["wrong"]))
        body=[ft.Row([ft.Column([label("موضوع",11),ft.Text(s["topic"],size=16,color=CYAN,weight=ft.FontWeight.BOLD)],spacing=2),
            ft.Container(expand=True),ft.Column([label("خطای باقی‌مانده",11),ft.Text(str(remain),size=22,color=RED if remain<=2 else GOLD,weight=ft.FontWeight.BOLD)],spacing=2)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
          ft.Column([ft.Text(str(s["time_left"]),size=28,color=RED if s["time_left"]<=10 else TEXT,weight=ft.FontWeight.BOLD),label("ثانیه باقی‌مانده",10)],spacing=0,horizontal_alignment=ft.CrossAxisAlignment.CENTER),
          ft.Text("کلمهٔ مخفی",size=13,color=MUTED,text_align=ft.TextAlign.CENTER),
          ft.Row(slots,wrap=True,spacing=5,alignment=ft.MainAxisAlignment.CENTER),
          ft.Text("حروف اشتباه",size=12,color=RED,text_align=ft.TextAlign.RIGHT),
          ft.Row(wrong_slots,wrap=True,spacing=5,alignment=ft.MainAxisAlignment.START,rtl=False),
          ft.Row([ft.Text(f"💡 {s['hints']} راهنمایی",color=GOLD,size=12),ft.Container(expand=True),ft.Text(f"❌ {len(s['wrong'])} اشتباه",color=RED,size=12)])]
        if s["mode"]=="local": body.insert(0,ft.Text(f"نوبت {s['turn']+1} | امتیازها: {s['scores'][0]} - {s['scores'][1]}",color=CYAN,weight=ft.FontWeight.BOLD,text_align=ft.TextAlign.CENTER))
        return ft.Column([ft.Row([ft.IconButton(ft.Icons.ARROW_FORWARD_ROUNDED,on_click=home),ft.Container(expand=True),ft.Text("حدس کلمه",size=18,color=TEXT,weight=ft.FontWeight.BOLD)]),
          card(ft.Column(body,spacing=11),padding=17),card(ft.Column([ft.Text("یک حرف انتخاب کن",size=15,color=TEXT,weight=ft.FontWeight.BOLD),
            ft.Row(keys,wrap=True,spacing=5,run_spacing=6,alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([btn("راهنمایی",ft.Icons.LIGHTBULB_OUTLINE,hint,GOLD),btn("تسلیم شدن",ft.Icons.FLAG_OUTLINED,lambda e:finish(False,"این دور را واگذار کردی."),"#39445E")],spacing=9)],spacing=12))],
          spacing=12,horizontal_alignment=ft.CrossAxisAlignment.STRETCH,scroll=ft.ScrollMode.AUTO)
    def result_screen():
        extra=[]
        if s["mode"]=="local":
            winner="بازیکن اول" if s["scores"][0]>=s["scores"][1] else "بازیکن دوم"
            extra=[ft.Text(f"امتیازها: {s['scores'][0]} - {s['scores'][1]} | {winner}",color=CYAN,text_align=ft.TextAlign.CENTER)]
        return ft.Column([ft.Container(height=16),ft.Text("🏆" if s["won"] else "💫",size=60,text_align=ft.TextAlign.CENTER),
          ft.Text("چالش روزانه" if s["mode"]=="daily" else s["result"],size=24,color=GREEN if s["won"] else GOLD,weight=ft.FontWeight.BOLD,text_align=ft.TextAlign.CENTER),
          label(s["result"] if s["mode"]=="daily" else "کلمهٔ موردنظر:",13),ft.Text(s["word"],size=30,color=CYAN,weight=ft.FontWeight.BOLD,text_align=ft.TextAlign.CENTER),*extra,
          card(ft.Column([ft.Row([label("امتیاز این دور"),ft.Container(expand=True),ft.Text(str(s["gain"]),size=22,color=GOLD)]),
            ft.Row([label("حروف اشتباه"),ft.Container(expand=True),ft.Text(str(len(s["wrong"])),color=RED)]),
            ft.Row([label("راهنمایی باقی‌مانده"),ft.Container(expand=True),ft.Text(str(s["hints"]),color=GREEN)])],spacing=12)),
          btn("دور بعدی",ft.Icons.REPLAY_ROUNDED,lambda e:new_game("solo")),btn("بازگشت به خانه",ft.Icons.HOME_ROUNDED,home,"#293550")],
          spacing=14,horizontal_alignment=ft.CrossAxisAlignment.STRETCH,scroll=ft.ScrollMode.AUTO)
    url_field=ft.TextField(label="آدرس سرور",value=s["online_url"],text_size=13,border_radius=12)
    name_field=ft.TextField(label="نام بازیکن",value=s["nickname"],text_size=13,border_radius=12)
    room_field=ft.TextField(label="کد اتاق",text_size=13,border_radius=12)
    def online_screen_open(e=None):
        stop_timer(); s["screen"]="online"; render()
    async def api(path,payload=None):
        base=(url_field.value or "").strip().rstrip("/")
        if not base: raise ValueError("آدرس سرور را وارد کن.")
        r=await client.post(base+path,json=payload or {}); r.raise_for_status(); return r.json()
    async def create_room(e=None):
        s["online_url"]=(url_field.value or "").strip().rstrip("/"); s["nickname"]=(name_field.value or "بازیکن").strip()[:20] or "بازیکن"
        try:
            d=await api("/rooms",{"nickname":s["nickname"],"topic":s["topic"],"seconds":s["seconds"]})
            s.update(room=d["room_code"],player_id=d["player_id"],online=d,screen="online_game",online_error="")
            render(); tasks["poll"]=page.run_task(poll_online)
        except Exception as ex: s["online_error"]=f"اتصال ناموفق بود: {ex}"; render()
    async def join_room(e=None):
        s["online_url"]=(url_field.value or "").strip().rstrip("/"); s["nickname"]=(name_field.value or "بازیکن").strip()[:20] or "بازیکن"
        try:
            d=await api(f"/rooms/{(room_field.value or '').strip().upper()}/join",{"nickname":s["nickname"]})
            s.update(room=d["room_code"],player_id=d["player_id"],online=d,screen="online_game",online_error="")
            render(); tasks["poll"]=page.run_task(poll_online)
        except Exception as ex: s["online_error"]=f"پیوستن انجام نشد: {ex}"; render()
    async def poll_online():
        try:
            while s["screen"]=="online_game":
                r=await client.get(f"{s['online_url']}/rooms/{s['room']}",params={"player_id":s["player_id"]}); r.raise_for_status()
                s["online"]=r.json()
                if s["online"].get("status") in ("won","lost","finished"): s["screen"]="online_result"; render(); break
                render(); await asyncio.sleep(1)
        except asyncio.CancelledError: raise
        except Exception as ex: s["online_error"]=f"ارتباط قطع شد: {ex}"; render()
    async def online_guess(ch):
        try:
            d=await api(f"/rooms/{s['room']}/guess",{"player_id":s["player_id"],"letter":ch}); s["online"]=d
            if d.get("status") in ("won","lost","finished"): cancel("poll"); s["screen"]="online_result"
            render()
        except Exception as ex: s["online_error"]=f"حرکت ثبت نشد: {ex}"; render()
    def online_screen():
        return ft.Column([ft.Row([ft.IconButton(ft.Icons.ARROW_FORWARD_ROUNDED,on_click=home),ft.Container(expand=True),ft.Text("بازی آنلاین",size=22,color=TEXT,weight=ft.FontWeight.BOLD)]),
          card(ft.Column([label("برای بازی با دوستت، سرور باید روی اینترنت در دسترس باشد.",13),url_field,name_field,
            btn("ساخت اتاق",ft.Icons.ADD_LINK,create_room),ft.Divider(color="#2B3550"),room_field,btn("پیوستن به اتاق",ft.Icons.GROUP_ADD,join_room,"#276B80"),
            label("localhost فقط روی همان دستگاه کار می‌کند. برای دوستت باید سرور عمومی و آدرس HTTPS داشته باشی.",11),
            ft.Text(s["online_error"],color=RED,size=12) if s["online_error"] else ft.Container()],spacing=12))],
          spacing=12,horizontal_alignment=ft.CrossAxisAlignment.STRETCH,scroll=ft.ScrollMode.AUTO)
    def online_game_screen():
        d=s.get("online",{}); keys=[]
        for ch in d.get("alphabet",ALPHABET):
            keys.append(ft.Container(content=ft.Text(ch,color=TEXT,size=16),width=37,height=41,alignment=ft.Alignment.CENTER,bgcolor="#202A43",border_radius=9,
                on_click=lambda e,x=ch:page.run_task(online_guess,x)))
        controls=[ft.Row([ft.IconButton(ft.Icons.ARROW_FORWARD_ROUNDED,on_click=home),ft.Container(expand=True),ft.Text("اتاق "+s["room"],size=18,color=CYAN,weight=ft.FontWeight.BOLD)]),
          card(ft.Column([ft.Text(d.get("message","منتظر بازیکن دوم..."),color=GOLD,text_align=ft.TextAlign.CENTER),
            ft.Text(d.get("word_mask","؟؟؟؟"),size=25,color=TEXT,weight=ft.FontWeight.BOLD,text_align=ft.TextAlign.CENTER),
            ft.Text("خطاها: "+" ".join(d.get("wrong",[])),color=RED,text_align=ft.TextAlign.CENTER),
            ft.Text("بازیکنان: "+" | ".join(d.get("players",[])),color=CYAN,text_align=ft.TextAlign.CENTER),
            ft.Row([ft.Text(s["room"],size=22,color=GOLD,weight=ft.FontWeight.BOLD),btn("کپی کد",ft.Icons.COPY,lambda e:page.set_clipboard(s["room"]),"#39445E")],alignment=ft.MainAxisAlignment.CENTER)],spacing=12)),
          card(ft.Column([ft.Text("حروف",color=TEXT,weight=ft.FontWeight.BOLD),ft.Row(keys,wrap=True,spacing=5,run_spacing=6,alignment=ft.MainAxisAlignment.CENTER)],spacing=10))]
        if s["online_error"]: controls.append(ft.Text(s["online_error"],color=RED))
        return ft.Column(controls,spacing=12,horizontal_alignment=ft.CrossAxisAlignment.STRETCH,scroll=ft.ScrollMode.AUTO)
    def online_result_screen():
        d=s.get("online",{})
        return ft.Column([ft.Text("پایان مسابقه",size=27,color=GOLD,weight=ft.FontWeight.BOLD,text_align=ft.TextAlign.CENTER),
          ft.Text(d.get("word",""),size=30,color=CYAN,text_align=ft.TextAlign.CENTER),ft.Text(d.get("message",""),color=TEXT,text_align=ft.TextAlign.CENTER),
          btn("بازگشت به خانه",ft.Icons.HOME_ROUNDED,home)],spacing=15,horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    def render():
        page.controls.clear()
        screens={"home":home_screen,"game":game_screen,"result":result_screen,"online":online_screen,"online_game":online_game_screen,"online_result":online_result_screen}
        content=screens.get(s["screen"],home_screen)()
        page.add(ft.Container(content=ft.Column([ft.Row([ft.Container(content=ft.Text("W",size=13,color=TEXT,weight=ft.FontWeight.BOLD),width=30,height=30,
          alignment=ft.Alignment.CENTER,bgcolor=PURPLE,border_radius=10),ft.Text("WORD PLAY",size=11,color="#8D98B3",weight=ft.FontWeight.BOLD),ft.Container(expand=True),
          ft.Icon(ft.Icons.AUTO_AWESOME,color=GOLD,size=17)]),content],spacing=12),padding=ft.Padding.only(left=15,right=15,top=12,bottom=24),width=560))
        page.update()
    render()

if __name__=="__main__": ft.app(target=main)
