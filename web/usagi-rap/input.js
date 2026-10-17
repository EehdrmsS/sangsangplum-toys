// Text edits support virtual keyboards and live Korean composition.
export class TypingInput {
 constructor(value=''){this.value=value;this.composing=false;this.segmenter=globalThis.Intl?.Segmenter?new Intl.Segmenter('ko',{granularity:'grapheme'}):null;}
 reset(value=''){this.value=value;this.composing=false;}
 beginComposition(){this.composing=true;}
 endComposition(){this.composing=false;}
 isComposing(event={}){return this.composing||event.isComposing||event.inputType==='insertCompositionText';}
 accept(event,value){
  const changed=value!==this.value;this.value=value;
  if(!changed||event.inputType?.startsWith('delete')||event.inputType?.startsWith('history'))return 0;
  if(this.isComposing(event))return 1;
  if(event.data)return this.segmenter?[...this.segmenter.segment(event.data)].length:[...event.data].length;
  return 1;
 }
}
