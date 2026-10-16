import {RapTransport} from './transport.js';
const $=id=>document.getElementById(id);
const typing=$('typing'),start=$('start'),tap=$('tap'),pause=$('pause'),reset=$('reset'),pet=$('pet'),message=$('message'),stage=$('stage');
let context,transport,loading=false,enabled=false,lastPhysical=-Infinity,composing=false,compositionCredit='';
const graphemes=new Intl.Segmenter('ko',{granularity:'grapheme'});
const length=text=>[...graphemes.segment(text||'')].length;
function say(text){message.textContent=text;}
function add(count=1){if(!enabled||!transport)return;transport.add(count);say('입력한 만큼 랩이 이어집니다.');}
async function enable(){
  if(loading)return;loading=true;start.disabled=true;say('소리를 준비하고 있어요…');
  try{
    context ||= new AudioContext();await context.resume();
    if(!transport){const response=await fetch('rap.wav');if(!response.ok)throw new Error('audio fetch');transport=new RapTransport(context,await context.decodeAudioData(await response.arrayBuffer()));}
    enabled=true;typing.disabled=false;tap.disabled=pause.disabled=reset.disabled=false;start.textContent='체험 중';
    say('입력창에 타자를 쳐보세요. 입력 1번마다 0.3초씩 재생됩니다.');typing.focus({preventScroll:true});
  }catch(error){enabled=false;start.textContent='다시 시작';say('소리를 준비하지 못했어요. 다시 시작해 주세요.');}
  finally{loading=false;start.disabled=enabled;}
}
start.addEventListener('click',enable);
tap.addEventListener('click',()=>add());
pause.addEventListener('click',()=>{transport?.pause();enabled=false;typing.disabled=true;tap.disabled=pause.disabled=true;start.disabled=false;start.textContent='이어서 체험';say('멈춘 위치를 기억하고 있어요. 다시 시작한 뒤 입력해 주세요.');});
reset.addEventListener('click',()=>{transport?.reset();say('음원 처음으로 돌아왔습니다.');if(enabled)typing.focus({preventScroll:true});});
typing.addEventListener('keydown',event=>{
  if(!enabled||event.ctrlKey||event.metaKey||event.altKey)return;
  const physical=/^(Key[A-Z]|Digit\d|Numpad\d|Numpad(Add|Subtract|Multiply|Divide|Decimal)|Space|Semicolon|Equal|Comma|Minus|Period|Slash|Backquote|BracketLeft|Backslash|BracketRight|Quote)$/.test(event.code);
  if(physical){lastPhysical=performance.now();add();}
});
typing.addEventListener('compositionstart',()=>{composing=true;compositionCredit='';});
typing.addEventListener('compositionend',event=>{
  composing=false;
  if(enabled&&performance.now()-lastPhysical>600&&event.data){add(length(event.data));compositionCredit=event.data;}
});
typing.addEventListener('input',event=>{
  if(!enabled||composing||event.isComposing||performance.now()-lastPhysical<600)return;
  if(compositionCredit&&event.data===compositionCredit){compositionCredit='';return;}
  compositionCredit='';
  if(event.inputType?.startsWith('insert')&&event.data)add(length(event.data));
});
function stopHidden(){transport?.pause();enabled=false;typing.disabled=true;tap.disabled=pause.disabled=true;start.disabled=false;start.textContent='이어서 체험';say('화면을 벗어나 재생을 멈췄습니다. 다시 시작해 주세요.');}
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopHidden();});
window.addEventListener('pagehide',()=>transport?.pause());
$('fullscreen').addEventListener('click',async()=>{
  try{if(!stage.requestFullscreen)throw new Error('unsupported');await stage.requestFullscreen();if(enabled)typing.focus({preventScroll:true});}
  catch{say('이 브라우저는 전체 화면을 지원하지 않습니다. 현재 화면에서 체험해 주세요.');}
});
$('exit-fullscreen').addEventListener('click',()=>document.exitFullscreen());
document.addEventListener('fullscreenchange',()=>{$('exit-fullscreen').hidden=!document.fullscreenElement;});
let wasPlaying=false,lastUpdate=0;
function draw(now){
  const playing=transport?.playing||false;
  if(playing!==wasPlaying){pet.src=playing?'dance.webp':'idle.webp';wasPlaying=playing;}
  const mode=playing?'RAPPING':enabled?'WAITING':'READY';if($('mode').textContent!==mode)$('mode').textContent=mode;
  if(now-lastUpdate>80){$('position').textContent=(transport?.position||0).toFixed(1);$('remaining').textContent=(transport?.remaining||0).toFixed(1);lastUpdate=now;}
  requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
