"""Vazhe-Baz online room API. Run: uvicorn server:app --host 0.0.0.0 --port 8000"""
import os, random, secrets, string, time, unicodedata
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app=FastAPI(title="Vazhe-Baz Online API",version="2.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS","*").split(",") if x.strip()],
 allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["*"])
WORDS={"حیوان":["شیر","فیل","زرافه","خرس","پلنگ","گربه","خرگوش","روباه","دلفین"],
"میوه":["سیب","موز","پرتقال","انگور","هندوانه","کیوی","انار","گیلاس"],
"غذا":["پیتزا","کباب","قرمه‌سبزی","املت","ماکارونی","فلافل","بستنی"],
"شهر":["تهران","مشهد","اصفهان","شیراز","تبریز","رشت","یزد"],
"کشور":["ایران","ترکیه","فرانسه","آلمان","ژاپن","کانادا","برزیل"],
"ورزش":["فوتبال","والیبال","بسکتبال","شنا","تنیس","کشتی"],
"طبیعت":["جنگل","دریا","آبشار","کوه","رنگین‌کمان","کهکشان"],
"وسیله":["دوچرخه","هواپیما","تلفن","رایانه","یخچال","قایق"],
"شغل":["پزشک","معلم","خلبان","آشپز","برنامه‌نویس","عکاس"],
"گل":["لاله","نرگس","رز","آفتابگردان","ارکیده"]}
ALPHABET=list("اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")
rooms={}; TTL=int(os.getenv("ROOM_TTL_SECONDS","7200"))
def chars(word):
 return [{"أ":"ا","إ":"ا","ٱ":"ا","ك":"ک","ي":"ی","ى":"ی"}.get(c,c) for c in unicodedata.normalize("NFC",word) if not c.isspace() and c not in ("\u200c","\u200d","\ufeff")]
def cleanup():
 now=time.time()
 for code in list(rooms):
  if now-rooms[code]["updated"]>TTL: del rooms[code]
def view(room,pid):
 p=room["players"].get(pid)
 if p is None: raise HTTPException(403,"شناسه بازیکن معتبر نیست.")
 return {"room_code":room["code"],"player_id":pid,"status":room["status"],
 "word_mask":"".join(c if c in p["guessed"] else "؟" for c in chars(room["word"])),
 "wrong":p["wrong"],"players":[x["nickname"] for x in room["players"].values()],
 "message":room["message"],"alphabet":ALPHABET,
 "word":room["word"] if room["status"] in ("won","lost","finished") else None,
 "scores":{x["nickname"]:x["score"] for x in room["players"].values()}}
class Create(BaseModel):
 nickname:str=Field(default="بازیکن",min_length=1,max_length=20)
 topic:str=Field(default="حیوان",max_length=30)
 seconds:int=Field(default=60,ge=15,le=180)
class Join(BaseModel): nickname:str=Field(default="بازیکن",min_length=1,max_length=20)
class Guess(BaseModel):
 player_id:str
 letter:str=Field(min_length=1,max_length=2)
@app.get("/health")
def health(): return {"ok":True,"service":"vazhe-baz","version":"2.0.0"}
@app.post("/rooms")
def create(body:Create):
 cleanup(); code="".join(random.choices(string.ascii_uppercase+string.digits,k=5)); pid=secrets.token_urlsafe(12)
 topic=body.topic if body.topic in WORDS else "حیوان"
 rooms[code]={"code":code,"topic":topic,"word":random.choice(WORDS[topic]),"seconds":body.seconds,
 "created":time.time(),"updated":time.time(),"deadline":0,"status":"waiting","message":"اتاق ساخته شد؛ منتظر بازیکن دوم...",
 "players":{pid:{"nickname":body.nickname.strip() or "بازیکن","guessed":set(),"wrong":[],"score":0}}}
 return view(rooms[code],pid)
@app.post("/rooms/{code}/join")
def join(code:str,body:Join):
 cleanup(); room=rooms.get(code.upper())
 if not room: raise HTTPException(404,"اتاق پیدا نشد یا منقضی شده است.")
 if len(room["players"])>=2: raise HTTPException(409,"این اتاق پر است.")
 if room["status"]!="waiting": raise HTTPException(409,"مسابقه شروع شده است.")
 pid=secrets.token_urlsafe(12); room["players"][pid]={"nickname":body.nickname.strip() or "بازیکن","guessed":set(),"wrong":[],"score":0}
 room["status"]="playing"; room["deadline"]=time.time()+room["seconds"]; room["updated"]=time.time()
 room["message"]="مسابقه شروع شد؛ هر بازیکن کلمه را جداگانه حدس می‌زند."
 return view(room,pid)
@app.get("/rooms/{code}")
def get_room(code:str,player_id:str=Query(...)):
 cleanup(); room=rooms.get(code.upper())
 if not room: raise HTTPException(404,"اتاق پیدا نشد.")
 if room["status"]=="playing" and time.time()>=room["deadline"]:
  room["status"]="lost"; room["message"]="زمان مسابقه تمام شد."
 room["updated"]=time.time(); return view(room,player_id)
@app.post("/rooms/{code}/guess")
def guess(code:str,body:Guess):
 cleanup(); room=rooms.get(code.upper())
 if not room: raise HTTPException(404,"اتاق پیدا نشد.")
 if room["status"]!="playing": raise HTTPException(409,"مسابقه در حال اجرا نیست.")
 if time.time()>=room["deadline"]:
  room["status"]="lost"; room["message"]="زمان مسابقه تمام شد."; return view(room,body.player_id)
 p=room["players"].get(body.player_id)
 if p is None: raise HTTPException(403,"شناسه بازیکن معتبر نیست.")
 if body.letter not in ALPHABET: raise HTTPException(422,"این حرف پشتیبانی نمی‌شود.")
 if body.letter not in p["guessed"] and body.letter not in p["wrong"]:
  if body.letter in chars(room["word"]):
   p["guessed"].add(body.letter)
   if all(c in p["guessed"] for c in chars(room["word"])):
    p["score"]+=max(50,int(max(0,room["deadline"]-time.time())*5)); room["status"]="won"; room["message"]=p["nickname"]+" برنده شد!"
  else:
   p["wrong"].append(body.letter)
   if len(p["wrong"])>=max(1,len(chars(room["word"]))):
    room["status"]="lost"; room["message"]=p["nickname"]+" همه فرصت‌های اشتباه را تمام کرد."
 room["updated"]=time.time(); return view(room,body.player_id)
