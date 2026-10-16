"""Typing adds 0.3 seconds to a persistent, uninterrupted PCM playback queue."""
import ctypes as c
import sys,time,json,queue,bisect
from pathlib import Path
import tkinter as tk
from PIL import Image,ImageSequence
from keyboard_hook import Hook
from pcm_credit import CreditAudio
from layered_pet import LayeredPet
from playback_settings import validate_seconds,load_seconds,save_seconds

BASE=Path(__file__).resolve().parent
DATA=Path(sys.executable).parent if getattr(sys,'frozen',False) else BASE

class App:
    def __init__(self,root):
        self.root=root;root.withdraw()
        self.events=queue.SimpleQueue();self.enabled=True;self.closed=False;self.beat=0
        self.audio=CreditAudio(BASE/'usagi-source.wav')
        self.settings_path=DATA/'playback-settings.json'
        self.seconds=load_seconds(self.settings_path)
        self.audio.pcm.set_seconds(self.seconds)
        self.hook=Hook(self.events)
        self.pet=LayeredPet(self.events,root.winfo_screenwidth()-340,root.winfo_screenheight()-460)
        self.frames=[];self.ends=[];self.last_key=None;self.dance_elapsed=0;self.previous_time=time.monotonic()
        self.load_animation(BASE/'usagi-original-dance.png')
        self.idle=Image.open(BASE/'usagi-original-idle.png').convert('RGBA');self.idle.thumbnail((220,260),Image.Resampling.LANCZOS)
        root.title('우사기 랩 설정')
        root.resizable(False,False)
        self.status=tk.StringVar()
        tk.Label(root,text='입력 1번당 재생 길이',font=('Malgun Gothic',15,'bold')).pack(padx=28,pady=(22,14))
        controls=tk.Frame(root);controls.pack(padx=28)
        self.seconds_text=tk.StringVar(value=f'{self.seconds:g}')
        self.duration_field=tk.Spinbox(controls,from_=.05,to=3,increment=.05,format='%.2f',width=7,font=('Malgun Gothic',14),textvariable=self.seconds_text)
        self.duration_field.pack(side='left');self.duration_field.bind('<Return>',lambda event:self.apply_duration())
        tk.Label(controls,text='초',font=('Malgun Gothic',12)).pack(side='left',padx=(8,15))
        tk.Button(controls,text='적용',command=self.apply_duration).pack(side='left',ipadx=8)
        self.setting_note=tk.StringVar(value='기본 0.3초 · 변경한 값은 다음 입력부터 적용됩니다.')
        tk.Label(root,textvariable=self.setting_note,font=('Malgun Gothic',9),wraplength=340).pack(padx=24,pady=(12,8))
        tk.Button(root,text='한 번 들어보기',command=self.play).pack(pady=(2,10))
        tk.Label(root,textvariable=self.status,font=('Malgun Gothic',9)).pack(padx=24,pady=(0,18))
        root.protocol('WM_DELETE_WINDOW',root.withdraw)
        self.tick()
    def load_animation(self,path):
        frames=[];ends=[];duration=0
        with Image.open(path) as source:
            for i,im in enumerate(ImageSequence.Iterator(source)):
                if i>=400:break
                duration+=max(.02,im.info.get('duration',80)/1000)
                frame=im.convert('RGBA');frame.thumbnail((220,260),Image.Resampling.LANCZOS)
                frames.append(frame.copy());ends.append(duration)
        if len(frames)<2:raise ValueError('움직이는 GIF/APNG를 선택하세요.')
        self.frames,self.ends,self.frame_duration=frames,ends,duration;self.last_key=None
    def play(self):
        self.audio.add();self.beat+=1
    def apply_duration(self,save=True):
        try:
            seconds=validate_seconds(self.seconds_text.get())
            if save:save_seconds(self.settings_path,seconds)
            self.audio.pcm.set_seconds(seconds);self.seconds=seconds
            self.seconds_text.set(f'{seconds:g}')
            self.setting_note.set(f'입력 1번에 {seconds:g}초 · 3번에 {3*seconds:g}초 재생됩니다.')
            return True
        except (ValueError,OSError) as error:
            self.setting_note.set(str(error) if isinstance(error,ValueError) else '설정을 저장하지 못했습니다. 쓰기 가능한 폴더에서 실행해 주세요.')
            return False
    def reset(self):
        self.audio.stop(restart=True);self.dance_elapsed=0
    def toggle(self):
        self.enabled=not self.enabled
        if not self.enabled:self.audio.stop()
    def tick(self):
        if self.closed:return
        try:
            while not self.events.empty():
                event=self.events.get()
                if event=='close':self.close();return
                if event=='play' and self.enabled:self.play()
                elif event=='toggle':self.toggle()
                elif event=='reset':self.reset()
                elif event=='popup':self.pet.menu(self.enabled)
                elif event=='settings':self.root.deiconify();self.root.lift()
            now=time.monotonic();dancing=self.audio.playing
            if dancing:self.dance_elapsed+=min(.1,now-self.previous_time)
            self.previous_time=now
            if dancing:
                index=min(bisect.bisect_right(self.ends,self.dance_elapsed%self.frame_duration),len(self.frames)-1)
                sprite,key=self.frames[index],('dance',index)
            else:sprite,key=self.idle,('idle',0)
            if key!=self.last_key:self.pet.render(sprite);self.last_key=key
            self.status.set(f'{"랩 켜짐" if self.enabled else "랩 꺼짐"} · F8 켜기/끄기 · F9 처음부터')
        except Exception as error:
            self.enabled=False;self.audio.stop();self.status.set('재생 오류: '+str(error))
        self.root.after(10,self.tick)
    def close(self):
        if self.closed:return
        self.closed=True;self.hook.close();self.audio.close();self.pet.close();self.root.destroy()

if __name__=='__main__':
    try:c.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError,OSError):pass
    root=tk.Tk();app=App(root)
    if '--settings-preview' in sys.argv:
        app.enabled=False;root.deiconify();root.after(45000,app.close);root.mainloop()
    elif '--check' in sys.argv:
        assert app.hook.ready.wait(3) and not app.hook.error
        app.seconds_text.set('.3');assert app.apply_duration(save=False)
        app.audio.add(3)
        for _ in range(400):
            root.update()
            if not app.audio.playing:break
            time.sleep(.01)
        assert not app.audio.playing
        assert app.audio.completed==3*app.audio.pcm.quantum
        assert abs(app.audio.position-.9)<.002,app.audio.position
        position=app.audio.position
        for _ in range(20):root.update();time.sleep(.01)
        assert app.audio.position==position
        app.audio.add()
        for _ in range(200):
            root.update()
            if not app.audio.playing:break
            time.sleep(.01)
        assert abs(app.audio.position-1.2)<.002,app.audio.position
        app.reset();assert app.audio.position==0
        app.seconds_text.set('.1');assert app.apply_duration(save=False)
        app.audio.add(3)
        for _ in range(200):
            root.update()
            if not app.audio.playing:break
            time.sleep(.01)
        assert not app.audio.playing and abs(app.audio.position-.3)<.002
        app.seconds_text.set('nan');assert not app.apply_duration(save=False)
        assert app.seconds==.1
        result={'default_three_inputs_seconds':.9,'resume_position_after_fourth_input':1.2,'custom_0_1_three_inputs_seconds':.3,'invalid_value_rejected':True,'idle_position_unchanged':True,'original_frames':len(app.frames),'hook_installed':True,'audio_listened':False}
        app.close();assert not app.hook.thread.is_alive()
        (DATA/'continuous-check.json').write_text(json.dumps(result,indent=2),'utf-8')
        if sys.stdout:print(json.dumps(result))
    else:root.mainloop()
