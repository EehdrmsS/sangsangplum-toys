// Text edits support virtual keyboards and live Korean composition.
export class TypingInput {
 constructor(value=''){this.value=value;this.segmenter=globalThis.Intl?.Segmenter?new Intl.Segmenter('ko',{granularity:'grapheme'}):null;}
 reset(value=''){this.value=value;}
 accept(event,value){
  const changed=value!==this.value;this.value=value;
  if(!changed||event.inputType?.startsWith('delete')||event.inputType?.startsWith('history'))return 0;
  if(event.isComposing||event.inputType==='insertCompositionText')return 1;
  if(event.data)return this.segmenter?[...this.segmenter.segment(event.data)].length:[...event.data].length;
  return 1;
 }
}
