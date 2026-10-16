"""PushCat: GitHub push -> receive a commit biscuit -> chew -> applaud."""
from pathlib import Path
import sys,time,json,queue,tkinter as tk,winsound,ctypes
from tkinter import messagebox
from PIL import Image,ImageTk
from snack_animation import Animation,FEED_SECONDS,SHUSH_SECONDS,SHAKE_SECONDS
from detector import Monitor
ASSETS=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'assets'
HOME=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
KEY='#ff00ff'
class Cat:
 def __init__(self,root,control=None):
  self.audit_path=Path(sys.argv[sys.argv.index('--live-test')+1]) if '--live-test' in sys.argv else None;self.audit_events=[]
  self.root=root;self.control=control;self.engine=Animation(ASSETS);self.events=queue.Queue();self.history=[];self.started=time.monotonic();self.state='idle';self.monitor=None;self.closed=False;self.suspended=False
  try:self.cfg=json.loads((HOME/'settings.json').read_text(encoding='utf-8-sig'))
  except (OSError,ValueError):self.cfg={}
  self.size=self.cfg.get('size',340);self.sound=self.cfg.get('sound',True);self.status='GitHub push 감지 연결 중'
  root.title('PushCat — commit snack');root.overrideredirect('--windowed' not in sys.argv);root.attributes('-topmost',True);root.configure(bg=KEY);root.wm_attributes('-transparentcolor',KEY)
  self.canvas=tk.Canvas(root,bg=KEY,highlightthickness=0,cursor='hand2');self.canvas.pack();self.resize(self.size,False)
  x=max(0,min(self.cfg.get('x',root.winfo_screenwidth()-self.size-45),root.winfo_screenwidth()-self.size));y=max(0,min(self.cfg.get('y',root.winfo_screenheight()-self.height-80),root.winfo_screenheight()-self.height));root.geometry(f'+{x}+{y}')
  self.canvas.bind('<ButtonPress-1>',self.press);self.canvas.bind('<B1-Motion>',self.drag);self.canvas.bind('<ButtonRelease-1>',self.release);self.canvas.bind('<Button-3>',self.menu);root.bind('<Escape>',lambda e:self.quiet());root.protocol('WM_DELETE_WINDOW',self.close)
  if control:
   control.title('Clap Cat');control.geometry('360x250');control.resizable(False,False)
   try:control.iconbitmap(str(ASSETS/'icon.ico'))
   except tk.TclError:pass
   control.protocol('WM_DELETE_WINDOW',self.close)
   tk.Label(control,text='Clap Cat',font=('Segoe UI',20,'bold')).pack(pady=(16,4))
   self.status_label=tk.Label(control,text='GitHub push 감지 연결 중',wraplength=330);self.status_label.pack(pady=4)
   tk.Button(control,text='간식 → 박수 테스트',command=self.feed).pack(fill='x',padx=24,pady=4)
   self.sound_button=tk.Button(control,text='소리 끄기' if self.sound else '소리 켜기',command=self.toggle_sound);self.sound_button.pack(fill='x',padx=24,pady=4)
   tk.Button(control,text='Clap Cat 종료',command=self.close).pack(fill='x',padx=24,pady=4)
   tk.Label(control,text='이 창을 닫으면 고양이와 Git 감지도 종료됩니다.',font=('Malgun Gothic',9)).pack(pady=6)
   control.bind('<Alt-F4>',lambda e:self.close())
   control.bind('<Unmap>',self.hide_control)
   control.bind('<Map>',self.show_control)
  if '--smoke-test' not in sys.argv and '--no-monitor' not in sys.argv:
   self.monitor=Monitor(HOME,lambda:self.events.put(('push',None)),lambda s:self.events.put(('status',s)));self.monitor.start()
  root.after(10,self.tick)
  if '--demo' in sys.argv:root.after(600,self.feed)
  if '--smoke-test' in sys.argv:
   self.sound=False;root.after(200,self.feed);root.after(3700,self.test_click);root.after(7500,self.finish_test)
 def save(self):
  self.cfg.update(size=self.size,sound=self.sound,x=self.root.winfo_x(),y=self.root.winfo_y());(HOME/'settings.json').write_text(json.dumps(self.cfg,ensure_ascii=False,indent=2),encoding='utf-8')
 def resize(self,size,save=True):
  self.size=size;self.height=round(size*346/320);self.canvas.configure(width=size,height=self.height);self.cache={}
  if save:self.save()
 def transition(self,state):
  if state!='clap':winsound.PlaySound(None,0)
  self.state=state;self.started=time.monotonic();self.history.append(state);self.audit_events.append(dict(state=state,time=time.time()));self.audit()
 def audit(self):
  if self.audit_path:self.audit_path.write_text(json.dumps(dict(status=self.status,events=self.audit_events,states=self.history),ensure_ascii=False,indent=2),encoding='utf-8')
 def feed(self):
  winsound.PlaySound(None,0);self.transition('feed')
 def clap(self):
  self.transition('clap')
  if self.sound and not self.suspended:winsound.PlaySound(str(ASSETS/'clap-continuous.wav'),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_LOOP)
 def quiet(self):
  winsound.PlaySound(None,0);self.transition('shush')
 def tick(self):
  if self.closed:return
  try:
   while True:
    k,v=self.events.get_nowait()
    if k=='push':self.feed()
    else:
     self.status=v;self.audit()
     if self.control:self.status_label.configure(text=v)
  except queue.Empty:pass
  t=time.monotonic()-self.started
  if self.state=='feed' and t>=FEED_SECONDS:self.clap();t=0
  elif self.state=='shush' and t>=SHUSH_SECONDS:self.transition('handshake');t=0
  elif self.state=='handshake' and t>=SHAKE_SECONDS:self.transition('idle');t=0
  frame=int(t*15);key=(self.state,frame if self.state!='clap' else frame%27)
  if self.state=='idle':key=('idle',0)
  if key not in self.cache:
   im=self.engine.render(self.state,frame/15,self.size);bg=Image.new('RGB',im.size,KEY);bg.paste(im.convert('RGB'),mask=im.getchannel('A').point(lambda p:255 if p>127 else 0));self.cache[key]=ImageTk.PhotoImage(bg)
  self.canvas.delete('all');self.canvas.create_image(0,0,anchor='nw',image=self.cache[key]);self.root.after(67,self.tick)
 def press(self,e):self.anchor=(e.x_root,e.y_root,self.root.winfo_x(),self.root.winfo_y());self.moved=False
 def drag(self,e):
  x,y,wx,wy=self.anchor;dx=e.x_root-x;dy=e.y_root-y
  if abs(dx)+abs(dy)>5:self.moved=True;self.root.geometry(f'{wx+dx:+d}{wy+dy:+d}')
 def release(self,e):
  if self.moved:self.save()
  elif self.state in ('feed','clap'):self.quiet()
 def toggle_sound(self):
  self.sound=not self.sound
  if not self.sound:winsound.PlaySound(None,0)
  elif self.state=='clap' and not self.suspended:self.started=time.monotonic();winsound.PlaySound(str(ASSETS/'clap-continuous.wav'),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_LOOP)
  self.save()
  if self.control:self.sound_button.configure(text='소리 끄기' if self.sound else '소리 켜기')
 def hide_control(self,e):
  if e.widget==self.control:self.suspended=True;winsound.PlaySound(None,0)
 def show_control(self,e):
  if e.widget==self.control and self.suspended:
   self.suspended=False
   if self.state=='clap':
    self.started=time.monotonic()
    if self.sound:winsound.PlaySound(str(ASSETS/'clap-continuous.wav'),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_LOOP)
 def menu(self,e):
  m=tk.Menu(self.root,tearoff=False);m.add_command(label=self.status,state='disabled');m.add_separator();m.add_command(label='커밋 간식 → 박수 테스트',command=self.feed);m.add_command(label='쉿 → 악수',command=self.quiet);m.add_command(label='소리 끄기' if self.sound else '소리 켜기',command=self.toggle_sound)
  sizes=tk.Menu(m,tearoff=False)
  for s in (260,340,420):sizes.add_command(label=f'{s}px',command=lambda s=s:self.resize(s))
  m.add_cascade(label='크기',menu=sizes);m.add_command(label='종료',command=self.close)
  try:m.tk_popup(e.x_root,e.y_root)
  finally:m.grab_release()
 def test_click(self):
  assert self.state=='clap',self.history
  self.canvas.event_generate('<ButtonPress-1>',x=120,y=150);self.canvas.event_generate('<ButtonRelease-1>',x=120,y=150);assert self.state=='shush'
 def finish_test(self):
  assert self.history[:5]==['feed','clap','shush','handshake','idle'],self.history
  self.feed();self.quiet();self.started-=SHUSH_SECONDS+.1;self.tick();assert self.state=='handshake';assert self.history[-3:]==['feed','shush','handshake']
  self.control.update_idletasks()
  hwnd=ctypes.windll.user32.GetParent(self.control.winfo_id())
  exstyle=ctypes.windll.user32.GetWindowLongW(hwnd,-20)
  owner=ctypes.windll.user32.GetWindow(hwnd,4)
  assert not (exstyle&0x80) and owner==0,(exstyle,owner)
  report=Path(sys.argv[sys.argv.index('--smoke-test')+1]);report.write_text(json.dumps(dict(result='PASS',states=self.history,canvas_visible=bool(self.root.winfo_viewable()),cancel_feed='PASS',animation_frames=len(self.engine.frames),taskbar_window=True,controller_visible=bool(self.control.winfo_viewable()))),encoding='utf-8');self.close()
 def close(self):
  if self.closed:return
  self.closed=True;winsound.PlaySound(None,0)
  try:
   if self.monitor:self.monitor.close()
  except Exception:
   self.closed=False
   messagebox.showerror('Clap Cat 종료 실패','Git 감지 연결을 해제하지 못했습니다. 다시 종료를 시도하거나 동봉한 연결 해제 도구를 사용하세요.',parent=self.control or self.root)
   return
  try:
   if '--smoke-test' not in sys.argv:self.save()
  finally:
   if self.control:self.control.destroy()
   else:self.root.destroy()
if __name__=='__main__':
 ctypes.windll.shcore.SetProcessDpiAwareness(1)
 ctypes.windll.kernel32.CreateMutexW(None,False,'Local\\PushCatDesktopCompanion')
 if ctypes.windll.kernel32.GetLastError()!=183:
  control=tk.Tk();pet=tk.Toplevel(control);Cat(pet,control);control.mainloop()
