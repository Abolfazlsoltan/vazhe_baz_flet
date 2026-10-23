from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import flet as ft
import main
class Task:
 def done(self): return False
 def cancel(self): pass
class Page:
 def __init__(self): self.controls=[]; self.snack_bar=None
 def add(self,*c): self.controls.extend(c)
 def update(self): pass
 def run_task(self,fn,*args,**kwargs): return Task()
def walk(c):
 if c is None or isinstance(c,(str,int,float,bool)): return
 if isinstance(c,(list,tuple)):
  for x in c: yield from walk(x)
  return
 yield c
 content=getattr(c,"content",None)
 if content is not None and not isinstance(content,(str,int,float,bool)): yield from walk(content)
 for x in getattr(c,"controls",[]) or []: yield from walk(x)
def click(p,label):
 for c in walk(p.controls):
  if isinstance(c,ft.Button) and c.content==label:
   assert callable(c.on_click); c.on_click(None); return
 raise AssertionError("Button not found: "+label)
if __name__=="__main__":
 p=Page(); main.main(p); assert p.controls
 click(p,"شروع تک‌نفره"); click(p,"تسلیم شدن"); click(p,"بازگشت به خانه")
 click(p,"چالش روزانه • معمای یکسان برای همه"); click(p,"تسلیم شدن"); click(p,"بازگشت به خانه")
 print("Flet UI smoke test passed (solo + daily challenge)")
