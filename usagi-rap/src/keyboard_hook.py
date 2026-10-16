import ctypes as c
from ctypes import wintypes as w
import threading
import os

def text_key(vk,scan=0):
    return (vk==32 or 48<=vk<=90 or 96<=vk<=111 or 186<=vk<=192 or 219<=vk<=222
            or (vk==0xe7 and scan>=32 and not 0xd800<=scan<=0xdfff))

class Hook:
    def __init__(self,events):
        self.events,self.ready,self.error,self.tid=events,threading.Event(),None,None
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
    def run(self):
        u,k=c.WinDLL('user32',use_last_error=True),c.WinDLL('kernel32',use_last_error=True)
        proc=c.WINFUNCTYPE(c.c_ssize_t,c.c_int,w.WPARAM,w.LPARAM)
        class Key(c.Structure):
            _fields_=[('vk',w.DWORD),('scan',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
        u.SetWindowsHookExW.argtypes=[c.c_int,proc,w.HINSTANCE,w.DWORD];u.SetWindowsHookExW.restype=w.HANDLE
        u.CallNextHookEx.argtypes=[w.HANDLE,c.c_int,w.WPARAM,w.LPARAM];u.CallNextHookEx.restype=c.c_ssize_t
        u.UnhookWindowsHookEx.argtypes=[w.HANDLE]
        k.GetModuleHandleW.argtypes=[w.LPCWSTR];k.GetModuleHandleW.restype=w.HMODULE
        u.GetAsyncKeyState.argtypes=[c.c_int];u.GetAsyncKeyState.restype=c.c_short
        u.GetForegroundWindow.restype=w.HWND
        u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
        own_pid=os.getpid()
        held=set()
        def callback(code,kind,data):
            if code>=0:
                event=c.cast(data,c.POINTER(Key)).contents;vk=event.vk
                if kind in (0x101,0x105): held.discard(vk)
                elif kind in (0x100,0x104):
                    if vk in (0x77,0x78):
                        if vk not in held: self.events.put('toggle' if vk==0x77 else 'reset')
                        held.add(vk)
                    elif text_key(vk,event.scan) and not any(u.GetAsyncKeyState(x)&0x8000 for x in (0x11,0x12,0x5b,0x5c)):
                        foreground_pid=w.DWORD()
                        u.GetWindowThreadProcessId(u.GetForegroundWindow(),c.byref(foreground_pid))
                        if foreground_pid.value!=own_pid:self.events.put('play')
            return u.CallNextHookEx(None,code,kind,data)
        self.callback=proc(callback);self.tid=k.GetCurrentThreadId();msg=w.MSG()
        u.PeekMessageW(c.byref(msg),None,0,0,0)
        handle=u.SetWindowsHookExW(13,self.callback,k.GetModuleHandleW(None),0)
        if not handle:self.error=str(c.get_last_error())
        self.ready.set()
        if not handle:return
        try:
            while u.GetMessageW(c.byref(msg),None,0,0)>0:
                u.TranslateMessage(c.byref(msg));u.DispatchMessageW(c.byref(msg))
        finally:u.UnhookWindowsHookEx(handle)
    def close(self):
        if self.tid:
            c.windll.user32.PostThreadMessageW(self.tid,0x12,0,0);self.thread.join(2)
