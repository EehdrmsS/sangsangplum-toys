"""Atomic Windows per-pixel alpha rendering for the floating character."""
import ctypes as c
from ctypes import wintypes as w
from PIL import Image


class LayeredPet:
    WIDTH, HEIGHT = 280, 340

    def __init__(self, events, x, y):
        self.events = events
        self.user = u = c.WinDLL('user32', use_last_error=True)
        self.gdi = g = c.WinDLL('gdi32', use_last_error=True)
        k = c.WinDLL('kernel32', use_last_error=True)
        proc_type = c.WINFUNCTYPE(c.c_ssize_t,w.HWND,w.UINT,w.WPARAM,w.LPARAM)
        class WindowClass(c.Structure):
            _fields_=[('style',w.UINT),('proc',proc_type),('ce',c.c_int),('we',c.c_int),('instance',w.HINSTANCE),('icon',w.HANDLE),('cursor',w.HANDLE),('background',w.HANDLE),('menu',w.LPCWSTR),('name',w.LPCWSTR)]
        class Header(c.Structure):
            _fields_=[('size',w.DWORD),('width',w.LONG),('height',w.LONG),('planes',w.WORD),('bits',w.WORD),('compression',w.DWORD),('image_size',w.DWORD),('xppm',w.LONG),('yppm',w.LONG),('used',w.DWORD),('important',w.DWORD)]
        class BitmapInfo(c.Structure):
            _fields_=[('header',Header),('colors',w.DWORD*3)]
        class Blend(c.Structure):
            _fields_=[('operation',c.c_ubyte),('flags',c.c_ubyte),('alpha',c.c_ubyte),('format',c.c_ubyte)]
        self.Blend=Blend
        k.GetModuleHandleW.argtypes=[w.LPCWSTR]
        k.GetModuleHandleW.restype=w.HINSTANCE
        u.DefWindowProcW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
        u.DefWindowProcW.restype=c.c_ssize_t
        u.RegisterClassW.argtypes=[c.POINTER(WindowClass)]
        u.CreateWindowExW.argtypes=[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,c.c_int,c.c_int,c.c_int,c.c_int,w.HWND,w.HMENU,w.HINSTANCE,c.c_void_p]
        u.CreateWindowExW.restype=w.HWND
        u.GetDC.argtypes=[w.HWND]
        u.GetDC.restype=w.HDC
        u.ReleaseDC.argtypes=[w.HWND,w.HDC]
        u.DestroyWindow.argtypes=[w.HWND]
        u.ShowWindow.argtypes=[w.HWND,c.c_int]
        u.SendMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
        u.SendMessageW.restype=c.c_ssize_t
        u.UpdateLayeredWindow.argtypes=[w.HWND,w.HDC,c.POINTER(w.POINT),c.POINTER(w.SIZE),w.HDC,c.POINTER(w.POINT),w.DWORD,c.POINTER(Blend),w.DWORD]
        u.UpdateLayeredWindow.restype=w.BOOL
        u.CreatePopupMenu.restype=w.HMENU
        u.AppendMenuW.argtypes=[w.HMENU,w.UINT,c.c_size_t,w.LPCWSTR]
        u.TrackPopupMenu.argtypes=[w.HMENU,w.UINT,c.c_int,c.c_int,c.c_int,w.HWND,c.c_void_p]
        u.TrackPopupMenu.restype=w.UINT
        u.DestroyMenu.argtypes=[w.HMENU]
        u.SetForegroundWindow.argtypes=[w.HWND]
        g.CreateCompatibleDC.argtypes=[w.HDC]
        g.CreateCompatibleDC.restype=w.HDC
        g.CreateDIBSection.argtypes=[w.HDC,c.POINTER(BitmapInfo),w.UINT,c.POINTER(c.c_void_p),w.HANDLE,w.DWORD]
        g.CreateDIBSection.restype=w.HANDLE
        g.SelectObject.argtypes=[w.HDC,w.HANDLE]
        g.SelectObject.restype=w.HANDLE
        g.DeleteObject.argtypes=[w.HANDLE]
        g.DeleteDC.argtypes=[w.HDC]
        self.proc=proc_type(self.dispatch)
        instance=k.GetModuleHandleW(None)
        self.window_class=WindowClass(0,self.proc,0,0,instance,None,None,None,None,'SangsangJaduUsagiAlpha')
        if not u.RegisterClassW(c.byref(self.window_class)):
            raise c.WinError(c.get_last_error())
        self.hwnd=u.CreateWindowExW(0x80000|8|0x40000,self.window_class.name,'우사기 랩',0x80000000,x,y,self.WIDTH,self.HEIGHT,None,None,instance,None)
        if not self.hwnd:
            raise c.WinError(c.get_last_error())
        self.screen_dc=u.GetDC(None)
        self.memory_dc=g.CreateCompatibleDC(self.screen_dc)
        info=BitmapInfo()
        info.header=Header(c.sizeof(Header),self.WIDTH,-self.HEIGHT,1,32,0,self.WIDTH*self.HEIGHT*4,0,0,0,0)
        self.pixels=c.c_void_p()
        self.bitmap=g.CreateDIBSection(self.screen_dc,c.byref(info),0,c.byref(self.pixels),None,0)
        if not self.bitmap:
            raise c.WinError(c.get_last_error())
        self.previous_bitmap=g.SelectObject(self.memory_dc,self.bitmap)
        self.rendered_count=0
        self.current_image=None
        u.ShowWindow(self.hwnd,4)

    def dispatch(self, hwnd, message, wp, lp):
        if message==0x0201:
            self.user.ReleaseCapture()
            self.user.SendMessageW(hwnd,0x00A1,2,0)
            return 0
        if message==0x0205:
            self.events.put('popup')
            return 0
        if message==0x0010:
            self.events.put('close')
            return 0
        return self.user.DefWindowProcW(hwnd,message,wp,lp)

    def render(self, frame):
        image=Image.new('RGBA',(self.WIDTH,self.HEIGHT))
        image.alpha_composite(frame,((self.WIDTH-frame.width)//2,(self.HEIGHT-frame.height)//2))
        raw=image.convert('RGBa').tobytes('raw','BGRa')
        c.memmove(self.pixels,raw,len(raw))
        size=w.SIZE(self.WIDTH,self.HEIGHT)
        point=w.POINT(0,0)
        blend=self.Blend(0,0,255,1)
        if not self.user.UpdateLayeredWindow(self.hwnd,self.screen_dc,None,c.byref(size),self.memory_dc,c.byref(point),0,c.byref(blend),2):
            raise c.WinError(c.get_last_error())
        self.current_image=image
        self.rendered_count+=1

    def menu(self, enabled):
        menu=self.user.CreatePopupMenu()
        items=[('설정','settings'),('랩 잠시 끄기' if enabled else '랩 다시 켜기','toggle'),('처음부터 (F9)','reset'),('종료','close')]
        for i,(label,action) in enumerate(items,1):
            self.user.AppendMenuW(menu,0,i,label)
        point=w.POINT()
        self.user.GetCursorPos(c.byref(point))
        self.user.SetForegroundWindow(self.hwnd)
        selected=self.user.TrackPopupMenu(menu,0x182,point.x,point.y,0,self.hwnd,None)
        self.user.DestroyMenu(menu)
        if selected:
            self.events.put(items[selected-1][1])

    def winfo_exists(self):
        return bool(self.hwnd)

    def close(self):
        if self.hwnd:
            self.user.DestroyWindow(self.hwnd)
            self.hwnd=None
            self.gdi.SelectObject(self.memory_dc,self.previous_bitmap)
            self.gdi.DeleteObject(self.bitmap)
            self.gdi.DeleteDC(self.memory_dc)
            self.user.ReleaseDC(None,self.screen_dc)
