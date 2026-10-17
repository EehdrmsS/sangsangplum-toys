import assert from 'node:assert/strict';
import {RapChallenge,RAP_LINE} from '../web/usagi-rap/challenge.js';
const c=new RapChallenge();
c.accept('ㅎ',true);assert.equal(c.phase,'typing');assert.equal(c.progress,0);
c.tick(0,false);assert.equal(c.phase,'typing','No failure before first audio credit');
c.accept('하',false);assert.equal(c.progress,1);assert.equal(c.phase,'typing');
c.accept('햐',true);assert.equal(c.phase,'typing','Do not fail an unfinished IME syllable');
c.accept('하야',false);assert.equal(c.progress,2);
c.tick(.2,true);assert.equal(c.phase,'typing');c.tick(0,true);assert.equal(c.phase,'lost');
c.reset();c.accept('허');assert.equal(c.phase,'lost');c.accept(RAP_LINE);assert.equal(c.phase,'lost');
c.reset();c.accept(RAP_LINE);assert.equal(c.phase,'won');c.tick(0,true);assert.equal(c.phase,'won');
c.reset();assert.equal(c.progress,0);assert.equal(c.phase,'ready');
const n=new RapChallenge('하');n.accept('\u1112\u1161');assert.equal(n.phase,'won','Normalize composed Hangul');
console.log('PASS: IME partial syllables; exact typo check; gap failure; completion; retry; NFC');

// Android/iOS keyboards may omit isComposing on intermediate input events.
for(const partial of ['ㅎ','하','항','하야','하얗','하야하']){
 const mobile=new RapChallenge();mobile.accept(partial);
 assert.equal(mobile.phase,'typing',`Keep mobile intermediate ${partial}`);
}
const mobile=new RapChallenge('하야');
for(const value of ['ㅎ','하','항','하야'])mobile.accept(value);
assert.equal(mobile.phase,'won','Final consonant moves into next syllable');
for(const invalid of ['허','하어','하야하x','하야하 ㅎ']){
 const wrong=new RapChallenge();wrong.accept(invalid);assert.equal(wrong.phase,'lost',invalid);
}
const incomplete=new RapChallenge('하');incomplete.accept('ㅎ');
assert.equal(incomplete.progress,0);assert.notEqual(incomplete.phase,'won');
incomplete.tick(0,true);assert.equal(incomplete.phase,'lost','Partial input still obeys rap timeout');
const raw=new RapChallenge('하');raw.accept('ㅎㅏ');assert.notEqual(raw.phase,'won','Only actual completed text wins');

const {TypingInput}=await import('../web/usagi-rap/input.js');
const edits=new TypingInput();
edits.beginComposition();
assert.equal(edits.isComposing({isComposing:false,inputType:'insertText'}),true);
assert.equal(edits.accept({data:'ㅎ',isComposing:false,inputType:'insertText'},'ㅎ'),1);
edits.endComposition();
assert.equal(edits.isComposing({isComposing:false,inputType:'insertText'}),false);
assert.equal(edits.accept({data:'하',inputType:'insertText'},'하'),1);
assert.equal(edits.accept({data:'하',inputType:'insertText'},'하'),0,'Duplicate commit adds no sound credit');
edits.beginComposition();edits.reset();assert.equal(edits.composing,false,'Retry clears composition');
assert.equal(edits.accept({inputType:'deleteContentBackward'},''),0);
console.log('PASS: missing IME flags, syllable carry, strict typos, composition lifecycle and audio deduplication');
