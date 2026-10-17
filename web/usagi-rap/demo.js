import {RapChallenge,RAP_LINE} from './challenge.js';
import {TypingInput} from './input.js';
import {RapTransport} from './transport.js';
const $=id=>document.getElementById(id);
const typing=$('typing'),start=$('start'),shorter=$('shorter'),longer=$('longer'),pause=$('pause'),reset=$('reset'),pet=$('pet'),message=$('message'),stage=$('stage');
let context,transport,loading=false,enabled=false,audioEpoch=0,seconds=.3;
const edits=new TypingInput();
const challenge=new RapChallenge();let challengeMode=false,freeText='';
function say(text){message.textContent=text;}
function wakeAudio(){return context&&context.state!=='running'?context.resume():Promise.resolve();}
function add(count=1){if(!enabled||!transport||count<=0)return;const epoch=audioEpoch,credit=seconds;wakeAudio().then(()=>{if(!enabled||epoch!==audioEpoch)return;transport.add(count,credit);if(!challengeMode)say('입력한 만큼 랩이 이어집니다.');}).catch(()=>say('소리가 멈췄어요. 일시정지 후 다시 시작해 주세요.'));}
async function enable(){
  if(loading)return;const epoch=audioEpoch;loading=true;start.disabled=true;say('소리를 준비하고 있어요…');
  try{
    const Audio=window.AudioContext||window.webkitAudioContext;
    context ||= new Audio();const resumed=context.resume();
    const unlock=context.createBufferSource();unlock.buffer=context.createBuffer(1,1,context.sampleRate);unlock.connect(context.destination);unlock.onended=()=>unlock.disconnect();unlock.start();
    typing.disabled=false;typing.focus({preventScroll:true});await resumed;
    if(!transport){const response=await fetch('rap-full.wav');if(!response.ok)throw new Error('audio fetch');transport=new RapTransport(context,await context.decodeAudioData(await response.arrayBuffer()));}
    if(epoch!==audioEpoch)return;
    enabled=true;edits.reset(typing.value);typing.disabled=false;pause.disabled=reset.disabled=false;start.textContent='체험 중';
    say(challengeMode?'첫 글자부터 시작! 가사를 보고 이어서 쳐보세요.':`입력창에 타자를 쳐보세요. 입력 1번마다 ${seconds.toFixed(1)}초씩 재생됩니다.`);typing.focus({preventScroll:true});
  }catch(error){enabled=false;typing.disabled=true;start.textContent='다시 시작';say('소리를 준비하지 못했어요. 다시 시작해 주세요.');}
  finally{loading=false;start.disabled=enabled;}
}
function paintChallenge(){
 const target=$('challenge-target');target.replaceChildren();
 for(const [i,char] of [...RAP_LINE].entries()){
  const span=document.createElement('span');span.className='lyric-cell';
  span.textContent=char==='\n'?'↵':char===' '?'·':char;
  if(char===' '||char==='\n')span.classList.add('separator');
  if(i<challenge.progress)span.classList.add('correct');else if(i===challenge.progress)span.classList.add('next');
  target.append(span);if(char==='\n')target.append(document.createElement('br'));
 }
 const next=target.querySelector('.next');if(next)target.scrollTop=Math.max(0,next.offsetTop-target.clientHeight/3);
 $('challenge-progress').textContent=`${challenge.progress} / ${RAP_LINE.length}`;
 stage.dataset.challenge=challenge.phase;
 $('challenge-success').hidden=!challengeMode||challenge.phase!=='won';
  if(challengeMode){shorter.disabled=challenge.phase==='typing'||seconds<=.1;longer.disabled=challenge.phase==='typing'||seconds>=1;}
}
function finishChallenge(){
 if(challenge.phase==='lost'){audioEpoch++;transport?.pause();enabled=false;typing.disabled=true;start.disabled=false;start.textContent='다시 도전';pause.disabled=true;say(challenge.reason);}
 else if(challenge.phase==='won'){typing.disabled=true;start.disabled=false;start.textContent='한 번 더 도전';pause.disabled=true;say('성공! 오타 없이 랩을 끝까지 이어갔어요.');}
 const finished=['lost','won'].includes(challenge.phase);shorter.disabled=finished?seconds<=.1:challenge.phase==='typing'||seconds<=.1;longer.disabled=finished?seconds>=1:challenge.phase==='typing'||seconds>=1;paintChallenge();
}
function judge(composing=false){challenge.accept(typing.value,composing);if(['lost','won'].includes(challenge.phase))finishChallenge();else paintChallenge();}
function selectTab(mode){
 if(!challengeMode)freeText=typing.value;
 audioEpoch++;transport?.reset();enabled=false;typing.disabled=true;pause.disabled=reset.disabled=true;challengeMode=mode;challenge.reset();
 typing.value=mode?'':freeText;edits.reset(typing.value);typing.placeholder=mode?'도전 시작을 누른 뒤, 위 가사를 따라 쳐보세요.':'여기에 타자를 쳐보세요.\n우라! 야하!';
 stage.classList.toggle('challenge-mode',mode);$('challenge-prompt').hidden=$('challenge-rules').hidden=!mode;$('free-note').hidden=mode;reset.hidden=mode;
 for(const [id,selected] of [['free-tab',!mode],['challenge-tab',mode]]){$(id).setAttribute('aria-selected',String(selected));$(id).tabIndex=selected?0:-1;}
 $('typing-panel').setAttribute('aria-labelledby',mode?'challenge-tab':'free-tab');
 start.disabled=false;start.textContent=mode?'도전 시작':'소리 켜고 체험 시작';shorter.disabled=seconds<=.1;longer.disabled=seconds>=1;
 say(mode?'오타 없이, 랩이 멈추기 전에 전체 가사를 완성해 보세요.':'시작 버튼을 누르면 소리가 준비됩니다.');paintChallenge();
}
start.addEventListener('click',async()=>{
 if(challengeMode){audioEpoch++;transport?.reset();challenge.reset();typing.value='';edits.reset('');paintChallenge();}
 await enable();
});
$('challenge-retry').addEventListener('click',()=>start.click());
for(const [id,mode] of [['free-tab',false],['challenge-tab',true]]){
 $(id).addEventListener('click',()=>selectTab(mode));
 $(id).addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?false:e.key==='End'?true:!challengeMode;selectTab(next);$(next?'challenge-tab':'free-tab').focus();});
}
typing.addEventListener('paste',e=>{if(challengeMode&&enabled){e.preventDefault();challenge.fail('붙여넣기 대신 직접 타이핑으로 도전해 보세요.');finishChallenge();}});
typing.addEventListener('beforeinput',e=>{if(challengeMode&&enabled&&['insertFromPaste','insertFromDrop'].includes(e.inputType)){e.preventDefault();challenge.fail('붙여넣기 대신 직접 타이핑으로 도전해 보세요.');finishChallenge();}});
typing.addEventListener('compositionend',()=>{if(challengeMode&&enabled)judge(false);});
if(location.hash==='#challenge')selectTab(true);
function changeLength(delta){
  seconds=Math.max(.1,Math.min(1,Math.round((seconds+delta)*10)/10));
  $('duration').textContent=seconds.toFixed(1)+'초';
  $('credit-hint').textContent=`입력 1번 = 원음 ${seconds.toFixed(1)}초`;
  $('single-example').textContent=seconds.toFixed(1);$('triple-example').textContent=(seconds*3).toFixed(1);
  shorter.disabled=seconds<=.1;longer.disabled=seconds>=1;
  say(`다음 입력부터 ${seconds.toFixed(1)}초씩 이어집니다.`);
}
shorter.addEventListener('click',()=>changeLength(-.1));
longer.addEventListener('click',()=>changeLength(.1));
pause.addEventListener('click',()=>{if(challengeMode){challenge.fail('잠시 쉬었어요. 다시 도전해 보세요.');finishChallenge();return;}audioEpoch++;transport?.pause();enabled=false;typing.disabled=true;pause.disabled=true;start.disabled=false;start.textContent='이어서 체험';say('멈춘 위치를 기억하고 있어요. 다시 시작한 뒤 입력해 주세요.');});
reset.addEventListener('click',()=>{audioEpoch++;transport?.reset();say('음원 처음으로 돌아왔습니다.');if(enabled)typing.focus({preventScroll:true});});
typing.addEventListener('pointerdown',()=>{if(enabled)wakeAudio().catch(()=>{});});
typing.addEventListener('input',event=>{const count=edits.accept(event,typing.value);if(enabled){if(challengeMode)judge(event.isComposing||event.inputType==='insertCompositionText');if(enabled)add(count);}});
function stopHidden(){if(challengeMode&&challenge.phase==='typing'){challenge.fail('화면을 벗어나 도전이 멈췄어요.');finishChallenge();return;}audioEpoch++;transport?.pause();enabled=false;typing.disabled=true;pause.disabled=true;start.disabled=false;start.textContent='이어서 체험';say('화면을 벗어나 재생을 멈췄습니다. 다시 시작해 주세요.');}
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
  if(challengeMode&&challenge.phase==='typing'){challenge.tick(transport?.remaining||0,(transport?.count||0)>0);if(challenge.phase==='lost')finishChallenge();}
  if(playing!==wasPlaying){pet.src=playing?'dance.webp':'idle.webp';wasPlaying=playing;}
  const mode=challengeMode&&challenge.phase==='lost'?'FAILED':challengeMode&&challenge.phase==='won'?'CLEAR':playing?'RAPPING':enabled?'WAITING':'READY';if($('mode').textContent!==mode)$('mode').textContent=mode;
  if(now-lastUpdate>80){$('position').textContent=(transport?.position||0).toFixed(1);$('remaining').textContent=(transport?.remaining||0).toFixed(1);lastUpdate=now;}
  requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
