"""Sample-exact 0.3-second credits on one persistent Windows PCM output queue."""
import ctypes as c
from ctypes import wintypes as w
import wave

class Format(c.Structure):
    _pack_=1
    _fields_=[('tag',w.WORD),('channels',w.WORD),('rate',w.DWORD),('bytes_second',w.DWORD),('align',w.WORD),('bits',w.WORD),('extra',w.WORD)]
class Header(c.Structure):
    _fields_=[('data',c.c_void_p),('length',w.DWORD),('recorded',w.DWORD),('user',c.c_size_t),('flags',w.DWORD),('loops',w.DWORD),('next',c.c_void_p),('reserved',c.c_size_t)]
class ClockValue(c.Union):
    _fields_=[('sample',w.DWORD),('ms',w.DWORD),('byte',w.DWORD),('padding',c.c_byte*8)]
class Clock(c.Structure):
    _fields_=[('type',w.UINT),('value',ClockValue)]

class PcmCursor:
    def __init__(self,raw,rate,align):
        self.raw,self.rate,self.align=raw,rate,align
        self.frames=len(raw)//align
        self.quantum=round(rate*.3)
        self.cursor=0
    def set_seconds(self,seconds):
        from playback_settings import validate_seconds
        self.quantum=round(self.rate*validate_seconds(seconds))
    def take(self):
        remaining=self.quantum
        chunks=[]
        while remaining:
            n=min(remaining,self.frames-self.cursor)
            chunks.append(self.raw[self.cursor*self.align:(self.cursor+n)*self.align])
            self.cursor=(self.cursor+n)%self.frames
            remaining-=n
        return b''.join(chunks)

class CreditAudio:
    def __init__(self,path):
        with wave.open(str(path),'rb') as f:
            if f.getsampwidth()!=2 or f.getcomptype()!='NONE':
                raise ValueError('16-bit PCM WAV required')
            channels,rate=f.getnchannels(),f.getframerate()
            raw=f.readframes(f.getnframes())
        self.pcm=PcmCursor(raw,rate,channels*2)
        self.mm=c.WinDLL('winmm')
        self.handle=w.HANDLE()
        self.buffers=[]
        self.submitted=0
        self.completed=0
        self.origin=0
        self.closed=False
        self.mm.waveOutOpen.argtypes=[c.POINTER(w.HANDLE),w.UINT,c.POINTER(Format),c.c_size_t,c.c_size_t,w.DWORD]
        for name in ('waveOutPrepareHeader','waveOutWrite','waveOutUnprepareHeader'):
            getattr(self.mm,name).argtypes=[w.HANDLE,c.POINTER(Header),w.UINT]
        for name in ('waveOutReset','waveOutClose'):
            getattr(self.mm,name).argtypes=[w.HANDLE]
        self.mm.waveOutGetPosition.argtypes=[w.HANDLE,c.POINTER(Clock),w.UINT]
        fmt=Format(1,channels,rate,rate*channels*2,channels*2,16,0)
        self.check(self.mm.waveOutOpen(c.byref(self.handle),0xffffffff,c.byref(fmt),0,0,0))
    @staticmethod
    def check(result):
        if result:
            raise RuntimeError(f'Windows audio error {result}')
    def add(self,count=1):
        self.sweep()
        for _ in range(count):
            old=self.pcm.cursor
            raw=self.pcm.take()
            data=c.create_string_buffer(raw,len(raw))
            header=Header(c.cast(data,c.c_void_p),len(raw),0,0,0,0,None,0)
            try:
                self.check(self.mm.waveOutPrepareHeader(self.handle,c.byref(header),c.sizeof(header)))
                self.check(self.mm.waveOutWrite(self.handle,c.byref(header),c.sizeof(header)))
            except Exception:
                self.pcm.cursor=old
                self.mm.waveOutUnprepareHeader(self.handle,c.byref(header),c.sizeof(header))
                raise
            self.buffers.append((header,data))
            self.submitted+=self.pcm.quantum
    def sweep(self):
        pending=[]
        for header,data in self.buffers:
            if header.flags & 1:  # WHDR_DONE: the device consumed this buffer.
                self.check(self.mm.waveOutUnprepareHeader(self.handle,c.byref(header),c.sizeof(header)))
                self.completed+=header.length//self.pcm.align
            else:
                pending.append((header,data))
        self.buffers=pending
    def elapsed_frames(self):
        clock=Clock();clock.type=2  # TIME_SAMPLES
        self.check(self.mm.waveOutGetPosition(self.handle,c.byref(clock),c.sizeof(clock)))
        if clock.type==2: return min(self.submitted,clock.value.sample)
        if clock.type==4: return min(self.submitted,clock.value.byte//self.pcm.align)
        return min(self.submitted,round(clock.value.ms*self.pcm.rate/1000))
    @property
    def playing(self):
        self.sweep()
        return bool(self.buffers)
    @property
    def position(self):
        return (self.origin+self.elapsed_frames())%self.pcm.frames/self.pcm.rate
    def stop(self,restart=False):
        cursor=0 if restart else (self.origin+self.elapsed_frames())%self.pcm.frames
        self.check(self.mm.waveOutReset(self.handle))
        self.sweep()
        self.pcm.cursor=self.origin=cursor
        self.submitted=self.completed=0
    def close(self):
        if not self.closed:
            self.stop()
            self.check(self.mm.waveOutClose(self.handle))
            self.closed=True
