// Full lyrics supplied by the user. Judge completed text, never partial Korean IME.
export const RAP_LINE="하야하 푸루루 푸루루 야하 이이야하 푸루루~\n\n이야- (야하야하) 우-라- (핫 핫 핫 얏) 우라-\n이야- (야하야하) 우-라- (푸루루 푸루루 푸루루) 우라-\n이야- (야하야하) 우-라- (핫 핫 핫 얏)\n우라- (예, 예) 야- (야) 핫 (핫) 우라- (예) 야하 (예)\n우라 (예) 하 하 (예) 하\n\n이야야야앗하-! 이야야야앗하-!\n(핫 핫 핫 핫) (핫 핫 핫 핫)\n하 야하 이기기야하";
export class RapChallenge {
 constructor(target=RAP_LINE){this.target=target;this.reset();}
 reset(){this.phase='ready';this.progress=0;this.reason='';}
 fail(reason){if(this.phase==='won'||this.phase==='lost')return;this.phase='lost';this.reason=reason;}
 accept(value,composing=false){
  if(this.phase==='lost'||this.phase==='won')return;
  if(value.length&&this.phase==='ready')this.phase='typing';
  if(composing){this.progress=Math.min(this.progress,value.length);return;}
  value=value.normalize('NFC');
  if(!this.target.startsWith(value)){this.fail('오타가 났어요. 다시 도전해 보세요.');return;}
  this.progress=value.length;
  if(value===this.target)this.phase='won';
 }
 tick(remaining,hasCredit){if(this.phase==='typing'&&hasCredit&&remaining<=0)this.fail('랩이 끊겼어요. 다음에는 조금 더 이어서 쳐보세요.');}
}
