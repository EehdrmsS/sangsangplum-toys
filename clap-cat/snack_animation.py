from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import math,io
import resvg_py
FEED_SECONDS=2.2
SHUSH_SECONDS=1.0
SHAKE_SECONDS=2.4

def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
class Animation:
 def __init__(self,assets):
  self.assets=Path(assets);self.frames=[Image.open(self.assets/f'{i:03}.png').convert('RGBA') for i in range(96)]
  self.feeding=[Image.open(self.assets/'feeding'/f'{i:03}.png').convert('RGBA') for i in range(21)]
  self.svg_path=self.assets/'github-mark.svg'
  self.logo=self.logo_at(320)
  try:self.font=ImageFont.truetype('consola.ttf',15)
  except OSError:self.font=ImageFont.load_default()
 def logo_at(self,size):
  width=round(size*188/320)
  svg=Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_path=str(self.svg_path),width=width*2))).convert('RGBA')
  svg=svg.resize((width,round(svg.height/2)),Image.Resampling.LANCZOS)
  backing=Image.new('RGBA',svg.size);ImageDraw.Draw(backing).ellipse((0,0,svg.width-1,svg.height-1),fill='white');backing.alpha_composite(svg)
  canvas=Image.new('RGBA',(size,round(size*346/320)));canvas.alpha_composite(backing,(round(size*112/320),round(size*56/320)));return canvas
 def render(self,state,t,size):
  if state=='idle':return self.logo_at(size)
  im=self.frame(state,t).resize((size,round(size*346/320)),Image.Resampling.LANCZOS)
  if state=='feed' and t<.25:
   bg=self.logo_at(size);k=ease(t/.25);bg.putalpha(bg.getchannel('A').point(lambda a:round(a*(1-k))));bg.alpha_composite(im);return bg
  return im
 def cookie(self,bite=0):
  im=Image.new('RGBA',(110,34));d=ImageDraw.Draw(im);d.rounded_rectangle((1,1,108,32),radius=7,fill='#e3b76e',outline='#895b2b',width=2)
  d.text((15,7),'[commit]',font=self.font,fill='#372617')
  for x,y in [(7,8),(8,24),(99,22),(94,7)]:d.ellipse((x,y,x+2,y+2),fill='#9e703a')
  if bite:
   a=im.getchannel('A');ad=ImageDraw.Draw(a)
   for k in range(min(4,bite)):ad.ellipse((70-k*18,-9,119-k*18,39),fill=0)
   im.putalpha(a)
  return im
 def frame(self,state,t):
  if state=='idle':return self.logo.copy()
  if state=='clap':return self.frames[int(t*15)%27].copy()
  if state=='shush':return self.frames[min(41,27+int(t*15))].copy()
  if state=='handshake':return self.frames[min(95,60+int(t*15))].copy()
  if state!='feed':raise ValueError(state)
  # Ordinary cat feeding is footage from the creator's full original video.
  if t<1.65:
   base=self.feeding[min(20,int(t*15))].copy()
  else:
   base=Image.blend(self.feeding[-1],self.frames[0],ease((t-1.65)/.55))
  k=ease(t/.25);im=base.copy();im.putalpha(im.getchannel('A').point(lambda a:round(a*k)))
  if .15<t<1.3:
   u=ease((t-.15)/.8);x=-35+235*u;y=155
   snack=self.cookie().resize((78,24))
   im.alpha_composite(snack,(round(x-39),round(y-12)))
   # The original muzzle covers the arriving commit, putting it behind the lips.
   # This preserves the real eating motion rather than moving a human hand.
   patch=base.crop((158,121,255,181));im.alpha_composite(patch,(158,121))
  return im
