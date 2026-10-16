import {ClapAudio} from './audio.js';
const elements=Object.fromEntries([...document.querySelectorAll('[id]')].map(el=>[el.id,el]));
const $=id=>elements[id],pet=$('pet'),canvas=document.querySelector('canvas'),ctx=canvas.getContext('2d');
const sheets={},counts={feed:33,clap:27,shush:15,handshake:36};
let state='idle',started=0,raf=0,ready=false,loading=null,sound=false,drag=null,moved=false;
const audio=new ClapAudio();
let floating=null,opening=false,generation=0;
const view=()=>floating&&!floating.closed?floating:window;
const nextFrame=fn=>view().requestAnimationFrame(fn);
const cancelFrame=id=>view().cancelAnimationFrame(id);
function canSound(){return sound&&state==='clap'&&!pet.hidden&&!view().document.hidden}
function startAudio(){audio.play(canSound,()=>Math.max(0,(performance.now()-started)/1000)).then(playing=>{if(playing)pet.dataset.audio='playing'}).catch(e=>{pet.dataset.audioError=e.name+': '+e.message;if(canSound()){$('pet-status').textContent='소리를 재생하지 못했어요. 소리 버튼으로 다시 시도하세요.';pet.dataset.audio='error'}})}
function stopAudio(){audio.stop();pet.dataset.audio='stopped'}
function transition(next){state=next;pet.dataset.state=next;started=performance.now();$('idle').hidden=next!=='idle';$('pet-status').textContent={idle:'간식을 기다리고 있어요',feed:'간식 냠냠…',clap:'클릭하면 박수를 멈춰요',shush:'쉿…',handshake:'수고했어요 🤝'}[next];stopAudio();if(next==='clap'&&canSound())startAudio();if(next==='idle'){$('push').disabled=false;$('try').disabled=false}}
function tick(){const now=performance.now();if(pet.hidden)return;let t=(now-started)/1000;if(state==='feed'&&t>=2.2){transition('clap');t=0}else if(state==='shush'&&t>=1){transition('handshake');t=0}else if(state==='handshake'&&t>=2.4){transition('idle');t=0}ctx.clearRect(0,0,320,346);if(state!=='idle'){let frame=state==='clap'?Math.floor(t*15)%27:Math.min(counts[state]-1,Math.floor(t*15));ctx.drawImage(sheets[state],frame%8*320,Math.floor(frame/8)*346,320,346,0,0,320,346)}raf=nextFrame(tick)}
function load(){if(loading)return loading;loading=Promise.all(Object.keys(counts).map(key=>new Promise((resolve,reject)=>{let im=new Image();im.onload=()=>{sheets[key]=im;resolve()};im.onerror=reject;im.src=key+'.webp'}))).then(()=>{ready=true}).catch(e=>{loading=null;throw e});return loading}
async function run(){const ticket=++generation;if(sound)audio.unlock().catch(()=>{});stopAudio();pet.hidden=false;$('push').disabled=true;$('try').disabled=true;$('pet-status').textContent='고양이 준비 중…';try{await load();if(ticket!==generation||pet.hidden)return;$('output').textContent='Enumerating objects: 3, done.\nWriting objects: 100% (3/3), done.\nmain → main ✓';cancelFrame(raf);transition('feed');raf=nextFrame(tick)}catch(e){$('pet-status').textContent='불러오지 못했어요. 다시 체험을 눌러주세요.';$('push').disabled=false;$('try').disabled=false}}
$('try').onclick=()=>launch();$('push').onclick=()=>pet.hidden?launch(true):run();$('reset').onclick=run;
$('close').onclick=()=>{if(floating&&!floating.closed)floating.close();else closePet()};
$('sound').onclick=()=>{sound=!sound;if(sound)audio.unlock().catch(()=>{});$('sound').textContent=sound?'소리 끄기':'소리 켜기';$('sound').setAttribute('aria-pressed',String(sound));if(canSound())startAudio();else stopAudio()};
document.addEventListener('visibilitychange',()=>{if(!floating){if(document.hidden)stopAudio();else if(canSound())startAudio()}});
window.addEventListener('pagehide',()=>{stopAudio();if(floating&&!floating.closed)floating.close()});
$('cat').addEventListener('pointerdown',e=>{if(floating)return;let r=pet.getBoundingClientRect();drag={x:e.clientX,y:e.clientY,left:r.left,top:r.top};moved=false;$('cat').setPointerCapture(e.pointerId)});
$('cat').addEventListener('pointermove',e=>{if(!drag)return;let dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>5)moved=true;if(moved){pet.style.right='auto';pet.style.bottom='auto';pet.style.left=Math.max(0,Math.min(innerWidth-pet.offsetWidth,drag.left+dx))+'px';pet.style.top=Math.max(0,Math.min(innerHeight-pet.offsetHeight,drag.top+dy))+'px'}});
$('cat').addEventListener('pointerup',()=>{drag=null;if(!moved&&state==='clap')transition('shush')});
$('cat').addEventListener('pointercancel',()=>{drag=null});$('cat').addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&state==='clap'){e.preventDefault();transition('shush')}});
window.addEventListener('resize',()=>{pet.style.left='';pet.style.top='';pet.style.right='';pet.style.bottom=''});

function closePet(){generation++;cancelFrame(raf);stopAudio();pet.hidden=true;document.body.append(pet);pet.style.cssText='';floating=null;state='idle';$('try').disabled=false;$('push').disabled=false;opening=false}
async function launch(feed=false,inline=false){
 if(opening)return;if(!pet.hidden){view().focus();if(feed)run();return}opening=true;
 if(!inline&&'documentPictureInPicture' in window){
  try{
   floating=await window.documentPictureInPicture.requestWindow({width:360,height:490});
   if(floating.document===document)throw Error('Separate window unavailable');
   const style=floating.document.createElement('link');style.rel='stylesheet';style.href=new URL('style.css',location.href).href;floating.document.head.append(style);
   const extra=floating.document.createElement('style');extra.textContent='body{margin:0;background:#fafaf8;display:grid;place-items:center;min-height:100vh}#pet{position:relative;inset:auto;width:min(100vw,320px);filter:none}#cat{cursor:pointer}';floating.document.head.append(extra);
   floating.document.title='Clap Cat · 상상자두';floating.document.body.append(pet);
   floating.addEventListener('pagehide',closePet,{once:true});
   floating.document.addEventListener('visibilitychange',()=>{if(canSound())startAudio();else stopAudio()});
   $('launch-status').textContent='고양이를 다른 창 위에 띄웠어요. 간식을 줘 보세요.';
  }catch{floating=null;$('launch-status').textContent='작은 창을 열지 못해 페이지 안에 고양이를 띄웠어요.'}
 }else $('launch-status').textContent='이 브라우저에서는 페이지 안에서 체험할 수 있어요.';
 pet.hidden=false;opening=false;$('try').disabled=false;try{await load()}catch{closePet();$('launch-status').textContent='고양이를 불러오지 못했어요. 다시 시도해 주세요.';return}if(pet.hidden)return;transition('idle');cancelFrame(raf);raf=nextFrame(tick);if(feed)run();
}

$('inline').onclick=()=>{if(floating){floating.close();closePet()}launch(false,true)};

