"""Check exact source continuity, accumulation and wrapping independently of speakers."""
import wave
import sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[1]/"src"))
from pathlib import Path
from pcm_credit import PcmCursor
from keyboard_hook import text_key
p=Path(__file__).resolve().parents[1]/"src"
with wave.open(str(p/'usagi-source.wav'),'rb') as f:
    raw=f.readframes(f.getnframes());rate=f.getframerate();align=f.getsampwidth()*f.getnchannels()
cursor=PcmCursor(raw,rate,align)
three=b''.join(cursor.take() for _ in range(3))
assert len(three)==round(.9*rate)*align
assert three==raw[:len(three)]
saved=cursor.cursor
fourth=cursor.take()
assert fourth==raw[saved*align:(saved+cursor.quantum)*align]
cursor=PcmCursor(raw,rate,align)
many=b''.join(cursor.take() for _ in range(100))
expected=(raw*((len(many)//len(raw))+1))[:len(many)]
assert many==expected
assert cursor.cursor==(100*cursor.quantum)%cursor.frames
assert text_key(65) and text_key(32) and text_key(0xe7,ord('하'))
assert not text_key(0x10) and not text_key(0x11) and not text_key(0x08)
print('PASS: 3 inputs = 0.9 seconds; exact PCM resume; 100-input wrap without skips; text keys')
cursor=PcmCursor(raw,rate,align)
first=cursor.take();cursor.set_seconds(.1);second=cursor.take()
assert first+second==raw[:round(rate*.4)*align]
assert len(second)==round(rate*.1)*align
from playback_settings import load_seconds,save_seconds,validate_seconds
import tempfile
with tempfile.TemporaryDirectory(dir=p,prefix='.settings-check-') as directory:
    assert Path(directory).resolve().is_relative_to(p.resolve())
    settings=Path(directory)/'playback-settings.json'
    assert load_seconds(settings)==.3
    save_seconds(settings,.45);assert load_seconds(settings)==.45
    for invalid in ('nan','inf','no',0,-1,4):
        try:save_seconds(settings,invalid)
        except ValueError:pass
        else:raise AssertionError('Invalid duration accepted')
        assert load_seconds(settings)==.45
    settings.write_text('{bad','utf-8');assert load_seconds(settings)==.3
print('PASS: duration change preserves exact source cursor; saved setting reloads; invalid values preserve prior setting')
