// One uninterrupted source; further inputs extend its scheduled stop by 0.3 s.
export class RapTransport {
  constructor(context,buffer) { this.context=context;this.buffer=buffer;this.cursor=0;this.source=null;this.begin=0;this.end=0;this.offset=0;this.count=0; }
  settle() {
    if(this.source && this.context.currentTime>=this.end) {
      this.cursor=(this.offset+this.end-this.begin)%this.buffer.duration;
      this.source.onended=null;this.source.disconnect();this.source=null;
    }
  }
  add(count=1) {
    this.settle(); const extra=count*.3;
    if(this.source) { this.end+=extra;this.source.stop(this.end); }
    else {
      const source=this.context.createBufferSource();source.buffer=this.buffer;source.loop=true;source.connect(this.context.destination);
      this.offset=this.cursor;this.begin=this.context.currentTime+.012;this.end=this.begin+extra;this.source=source;
      source.onended=()=>{if(this.source===source)this.settle();};source.start(this.begin,this.offset);source.stop(this.end);
    }
    this.count+=count;
  }
  get playing(){this.settle();return Boolean(this.source)&&this.context.currentTime>=this.begin;}
  get remaining(){this.settle();return this.source?Math.max(0,this.end-Math.max(this.begin,this.context.currentTime)):0;}
  get position(){this.settle();return this.source?(this.offset+Math.max(0,Math.min(this.context.currentTime,this.end)-this.begin))%this.buffer.duration:this.cursor;}
  pause(){
    this.cursor=this.position;
    if(this.source){this.source.onended=null;this.source.stop();this.source.disconnect();this.source=null;}
    this.end=0;
  }
  reset(){this.pause();this.cursor=0;this.count=0;}
}
