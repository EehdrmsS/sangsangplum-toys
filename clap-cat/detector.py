"""Git Trace2 receiver. No command lines, credentials, or events are saved."""
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import re
import select
import socket
import subprocess
import tempfile
import threading
import time
import uuid

FLAGS = subprocess.CREATE_NO_WINDOW

def git_config(*args):
    return subprocess.run(['git','config','--global',*args],capture_output=True,
                          creationflags=FLAGS,timeout=10)

def github(value):
    return bool(re.search(r'(?:https?://(?:[^/@\s]+@)?|ssh://(?:git@)?|git@)github\.com(?=[:/]|$)', value, re.I))

class Events:
    def __init__(self, callback):
        self.callback = callback
        self.sessions = {}
        self.lock = threading.Lock()

    def feed(self, event):
        sid = event.get('sid','')
        if not sid:
            return
        with self.lock:
            kind = event.get('event')
            # Keep only booleans and timestamps; discard raw command lines immediately.
            if kind == 'start':
                args = event.get('argv',[])
                self.sessions[sid] = dict(push=False, github=any(github(str(a)) for a in args),
                    dry=any(a in ('--dry-run','-n') or (str(a).startswith('-') and not str(a).startswith('--') and 'n' in str(a)[1:]) for a in args[1:]), stamp=time.monotonic())
                if len(self.sessions)>2048:
                    now=time.monotonic()
                    self.sessions={k:v for k,v in self.sessions.items() if now-v['stamp']<600}
            elif kind == 'cmd_name' and event.get('name') == 'push':
                self.sessions.setdefault(sid,dict(push=False,github=False,dry=False,stamp=time.monotonic()))['push']=True
            elif kind == 'child_start':
                if any(github(str(a)) for a in event.get('argv',[])):
                    for parent, state in self.sessions.items():
                        if sid == parent or sid.startswith(parent+'/'):
                            state['github']=True
            elif kind == 'exit':
                state=self.sessions.pop(sid,None)
                if state and state['push'] and state['github'] and not state['dry'] and event.get('code') == 0:
                    self.callback()

class Monitor:
    def __init__(self, home, callback, status):
        self.home=Path(home)
        self.callback=callback
        self.status=status
        self.stop=threading.Event()
        self.parser=Events(callback)
        self.sock=None
        self.path=None
        self.include=self.home/'pushcat.gitconfig'
        self.installed=False

    def start(self):
        threading.Thread(target=self.run,daemon=True).start()

    def run(self):
        try:
            self.open_socket()
            self.install()
            self.status('이 PC의 GitHub push 감지 중')
            while not self.stop.is_set():
                ready,_,_=select.select([self.sock],[],[],0.4)
                if not ready:
                    continue
                handle=self.ws.accept(self.sock.fileno(),None,None)
                if handle == c.c_size_t(-1).value:
                    continue
                client=socket.socket(1,socket.SOCK_STREAM,0,fileno=handle)
                client.settimeout(1)
                threading.Thread(target=self.read,args=(client,),daemon=True).start()
        except Exception:
            self.status('감지 연결 실패 · Git 설치와 설정 쓰기 권한을 확인하세요')
        finally:
            self.cleanup()

    def open_socket(self):
        # Windows supports AF_UNIX even where Python omits the public constant.
        self.path=Path(tempfile.gettempdir())/('pc-'+uuid.uuid4().hex[:12]+'.sock')
        encoded=str(self.path).encode('utf-8')
        if len(encoded)>=108:
            raise RuntimeError('Socket path too long')
        class Address(c.Structure):
            _fields_=[('family',c.c_ushort),('path',c.c_char*108)]
        self.ws=c.WinDLL('Ws2_32')
        self.ws.bind.argtypes=[c.c_size_t,c.c_void_p,c.c_int]
        self.ws.accept.argtypes=[c.c_size_t,c.c_void_p,c.c_void_p]
        self.ws.accept.restype=c.c_size_t
        self.sock=socket.socket(1,socket.SOCK_STREAM,0)
        address=Address(1,encoded)
        if self.ws.bind(self.sock.fileno(),c.byref(address),c.sizeof(address)):
            raise OSError('Socket bind failed')
        self.sock.listen(64)
        self.sock.setblocking(False)

    def install(self):
        if os.environ.get('GIT_TRACE2_EVENT'):
            raise RuntimeError('GIT_TRACE2_EVENT override exists')
        # A dedicated include leaves existing Git keys untouched. Remove stale copies
        # from a previous interrupted run before attaching this process's socket.
        self.remove_include()
        escaped=('af_unix:stream:'+str(self.path)).replace('\\','/')
        self.include.write_text('[trace2]\n\teventTarget = "'+escaped+'"\n',encoding='utf-8')
        result=git_config('--add','include.path',self.include.as_posix())
        if result.returncode:
            raise RuntimeError('Could not enable Git events')
        self.installed=True

    def remove_include(self):
        result=git_config('--fixed-value','--unset-all','include.path',self.include.as_posix())
        if result.returncode not in (0,5):
            raise RuntimeError('Could not detach Git events')

    def read(self, client):
        buffer=b''
        with client:
            while not self.stop.is_set():
                try:
                    data=client.recv(65536)
                except socket.timeout:
                    continue
                except OSError:
                    break
                if not data:
                    break
                buffer+=data
                if len(buffer)>2*1024*1024:
                    break
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1)
                    try:
                        self.parser.feed(json.loads(line))
                    except (ValueError,TypeError,KeyError):
                        pass

    def cleanup(self):
        if self.installed:
            try:
                self.remove_include()
                self.installed=False
            except Exception:
                self.status('Git 감지 연결 해제 실패 · 사용 안내의 복구 명령 확인')
        if self.sock:
            self.sock.close()
            self.sock=None
        if self.path:
            self.path.unlink(missing_ok=True)

    def close(self):
        self.stop.set()
        # Keep Git configuration removal synchronous before closing the UI.
        if self.installed:
            self.remove_include()
            self.installed=False
