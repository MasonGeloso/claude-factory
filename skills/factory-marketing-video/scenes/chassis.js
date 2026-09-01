
// ===========================================================================
// SCENE KIT — vertical explainer scenes for shorts.
//
// Frame contract
//   stage        1080 x 1920
//   bottom rail  bottom 15% (288px): logo cell left, speaker cell right
//   art area     everything above the rail — each scene lays out inside ART
//
// Timing contract
//   window.__render(t) is a PURE function of time. BEATS below is the only
//   thing a per-episode scene needs to change: each beat is a transcript
//   timestamp (seconds into the clip) at which a visual element lands. Bind
//   them from blocks.json / the word transcript and the art tracks the voice.
//
// Scenes are chosen with ?s=  — every scene must illustrate WHAT IS BEING SAID
// at that moment. Never reuse an archetype whose content is off-topic.
// The kit is meant to grow: one archetype per *shape of argument*, not per topic.
// ===========================================================================
const W=1080,H=1920, SC=new URLSearchParams(location.search).get('s')||'';
const RAIL_H=Math.round(H*0.15), ART={x:0,y:0,w:W,h:H-RAIL_H};

// Brand wordmark shown in the bottom rail — replace with your own.
const BRAND_NAME='YOUR BRAND', BRAND_URL='yourbrand.example';

// Default color palette — a starting point, replace with your own brand
// tokens (pull real hex values from your own design system/CSS, don't guess).
// Clean/analytical: pure black, fine white linework, near-zero fill. Colour is
// reserved for up/down semantics only — everything else is white or grey.
const C={surface:'#000000',panel:'#000000',rail:'#000000',ribbon:'#000000',
  paper:'#F4F4F4',muted:'#8C8C8C',dim:'#4F4F4F',
  accent:'#FFFFFF',accent2:'#D8B36A',signal:'#FFFFFF',
  slate:'#9AA8B4',plum:'#B9A8CC',teal:'#8FD6C4',sage:'#7FE3B0',rose:'#F08C8C'};

const stage=document.getElementById('stage');
const bg=document.createElement('canvas');bg.width=W;bg.height=H;
const fg=document.createElement('canvas');fg.width=W;fg.height=H;
stage.append(bg,fg);const g=fg.getContext('2d');

/* ---- background: a slow warm-ink field, brand-toned, never busy --------- */
let gl,uT,uRes;(function(){gl=bg.getContext('webgl');
const vs=`attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}`;
const fs=`precision highp float;uniform float t;uniform vec2 r;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){vec2 uv=gl_FragCoord.xy/r.xy;
 float v=pow(max(0.,1.-length(uv-vec2(.5,.46))*1.05),3.)*.055;   // barely-there lift
 vec3 col=vec3(.004)+vec3(v);
 col+=(h(gl_FragCoord.xy+t)-.5)*.008;
 gl_FragColor=vec4(col,1.);}`;
const mk=(ty,s)=>{const o=gl.createShader(ty);gl.shaderSource(o,s);gl.compileShader(o);return o};
const pr=gl.createProgram();gl.attachShader(pr,mk(gl.VERTEX_SHADER,vs));
gl.attachShader(pr,mk(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pr);gl.useProgram(pr);
const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);
gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
const l=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(l);
gl.vertexAttribPointer(l,2,gl.FLOAT,false,0,0);
uT=gl.getUniformLocation(pr,'t');uRes=gl.getUniformLocation(pr,'r');})();

// ---- language -------------------------------------------------------------
// One file per EPISODE, not per language: the EN and JA cuts of a week argue the
// same thing, so they share scene geometry and differ only in copy and timing.
// They are NOT the same cut — a dub is re-scripted, so each language brings its
// own sequence spans and may use scenes the other never shows.
const LANG=new URLSearchParams(location.search).get('lang')||'en';
let COPY={};
function setCopy(o){COPY=o;}
function L(k){
  const d=(COPY[LANG]||{}), en=(COPY.en||{});
  return k in d ? d[k] : (k in en ? en[k] : k);}

const ez=t=>t<0?0:t>1?1:1-Math.pow(1-t,3);
const eb=t=>{t=t<0?0:t>1?1:t;const c=1.70158+1;return 1+c*Math.pow(t-1,3)+1.70158*Math.pow(t-1,2)};
// CJK is in every stack, not just the Japanese episodes — a stray kana in an
// English scene must render, not draw tofu. Gothic, never Mincho: serif reads
// editorial and this register is analytical.
const FACE_SANS='"Inter Tight", Inter, "Noto Sans CJK JP", system-ui, sans-serif';
const FACE_MONO='"JetBrains Mono", ui-monospace, "Noto Sans Mono CJK JP", monospace';
const HAS_CJK=/[　-ヿ㐀-鿿＀-￯]/;
function T(s,x,y,{size=26,w=600,col=C.paper,mono=false,tr=0,al='left'}={}){
  // Letter-spacing that flatters latin small-caps mangles kana and kanji, so a
  // string containing CJK ignores tr regardless of what the caller asked for.
  if(tr && HAS_CJK.test(s)) tr=0;
  g.save();g.font=`${w} ${size}px ${mono?FACE_MONO:FACE_SANS}`;
  g.fillStyle=col;g.textBaseline='alphabetic';
  const ch=[...s],wd=ch.reduce((a,c)=>a+g.measureText(c).width+tr,0)-(tr||0);
  let cx=al==='center'?x-wd/2:al==='right'?x-wd:x;
  if(tr){for(const c of ch){g.fillText(c,cx,y);cx+=g.measureText(c).width+tr;}}
  else{g.textAlign=al;g.fillText(s,x,y);}
  g.restore();return wd;}
function panel(x,y,w,h,r,a=1,tint){
  // FUI framing: corner brackets rather than a closed box. A full outline reads
  // as a card; brackets read as an instrument registering something.
  g.save();
  g.fillStyle=`rgba(255,255,255,${.010*a})`;
  g.beginPath();g.rect(x,y,w,h);g.fill();
  const col=tint?`${tint}99`:`rgba(255,255,255,${.42*a})`;
  const L=Math.min(30,w*.16,h*.30);
  g.strokeStyle=col;g.lineWidth=1.4;g.lineCap='square';
  [[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]].forEach(([cx,cy,sx,sy])=>{
    g.beginPath();g.moveTo(cx+sx*L,cy);g.lineTo(cx,cy);g.lineTo(cx,cy+sy*L);g.stroke();});
  // faint connecting edge so the shape still reads
  g.strokeStyle=tint?`${tint}22`:`rgba(255,255,255,${.10*a})`;g.lineWidth=1;
  g.strokeRect(x+.5,y+.5,w-1,h-1);
  g.restore();}

// graticule: the instrument the diagram is drawn on. Static — see below.
function graticule(t){
  g.save();
  g.strokeStyle='rgba(255,255,255,.032)';g.lineWidth=1;
  for(let x=0;x<W;x+=60){g.beginPath();g.moveTo(x+.5,0);g.lineTo(x+.5,H-RAIL_H);g.stroke();}
  for(let y=0;y<H-RAIL_H;y+=60){g.beginPath();g.moveTo(0,y+.5);g.lineTo(W,y+.5);g.stroke();}
  g.strokeStyle='rgba(255,255,255,.07)';
  for(let x=0;x<W;x+=300){g.beginPath();g.moveTo(x+.5,0);g.lineTo(x+.5,H-RAIL_H);g.stroke();}
  // NO scan sweep. A band travelling top-to-bottom on a loop is a screensaver:
  // it never carries information, it repeats, and it pulls the eye away from
  // whatever the scene is actually building. The grid alone is the instrument.
  g.restore();}

/* ---- bottom rail: logo cell left, speaker cell right -------------------- */
// The compositor pastes the real webcam into SPEAKER_BOX; the placeholder here
// just proves the layout. Keeping the speaker in a fixed cell means the art
// above never has to dodge them.
const RY=H-RAIL_H, PADR=26, CELL=(W-PADR*3)/2;
const SPEAKER_BOX={x:PADR*2+CELL,y:RY+PADR/2,w:CELL,h:RAIL_H-PADR};
let LOGO=null;const li=new Image();li.onload=()=>LOGO=li;li.src='logo_dark.png';
function rail(t){
  g.save();
  g.fillStyle='#000';g.fillRect(0,RY,W,RAIL_H);
  g.strokeStyle='rgba(255,255,255,.18)';g.lineWidth=1;
  g.beginPath();g.moveTo(0,RY+.5);g.lineTo(W,RY+.5);g.stroke();
  // logo cell
  const lc={x:PADR,y:RY+PADR/2,w:CELL,h:RAIL_H-PADR};
  // logo hard-left in its cell, text starts after it — they must never touch
  const LOGO_W=124, LX=lc.x+4, TX=LX+LOGO_W+28;
  if(LOGO){const k=Math.min(LOGO_W/LOGO.width,LOGO_W/LOGO.height);
    g.globalAlpha=.95;
    g.drawImage(LOGO,LX,lc.y+lc.h/2-LOGO.height*k/2,LOGO.width*k,LOGO.height*k);
    g.globalAlpha=1;}
  T(BRAND_NAME,TX,lc.y+lc.h/2+2,{size:42,w:800,col:C.paper,tr:3.4});
  T(BRAND_URL,TX,lc.y+lc.h/2+38,{size:21,col:C.muted,mono:true,tr:2.2});
  // speaker cell
  const s=SPEAKER_BOX;
  g.save();g.beginPath();g.roundRect(s.x,s.y,s.w,s.h,18);g.clip();
  g.fillStyle='#000';g.fillRect(s.x,s.y,s.w,s.h);
  T('SPEAKER',s.x+s.w/2,s.y+s.h/2+6,{size:16,col:'rgba(255,255,255,.22)',mono:true,al:'center',tr:3});
  g.restore();
  g.save();g.beginPath();g.roundRect(s.x+.5,s.y+.5,s.w-1,s.h-1,18);
  g.strokeStyle='rgba(255,255,255,.18)';g.lineWidth=1;g.stroke();g.restore();
  g.restore();}

function head(t,kicker,title){
  const a=ez((t-.15)/.7);g.save();g.globalAlpha=a;
  T(kicker,64,120,{size:20,col:C.muted,mono:true,tr:4.5});
  T(title,64,190,{size:52,w:800});g.restore();}

/* ---- mount: every episode file calls this with its own scene table ------- */
// The chassis is the BRAND (frame, palette, rail, graticule, type). The scenes
// are the EPISODE. Never edit the chassis to make one episode work; never
// import another episode's scenes to save time.
function mount(SCENES, dflt){
  const Q=new URLSearchParams(location.search);
  const pick=SCENES[SC]||SCENES[dflt]||Object.values(SCENES)[0];
  function draw(fn,t){
    gl.uniform1f(uT,t);gl.uniform2f(uRes,W,H);gl.drawArrays(gl.TRIANGLES,0,3);
    g.clearRect(0,0,W,H);
    graticule(t);
    fn(t);
    rail(t);}
  // The render contract stays a PURE function of t — the frame grabber drives it
  // and must never see an internal clock.
  window.__render=t=>draw(pick,t);
  window.__SPEAKER_BOX=SPEAKER_BOX;   // the compositor reads this
  window.__render(0);

  // ---- preview only: a real-time clock, enabled by ?play or ?seq ----------
  // Opening a scene file directly otherwise shows frame 0, which is near-blank.
  // Neither flag is set by shoot_scene.py / shoot_sequence.py, so captures are
  // unaffected.
  if(!Q.has('play') && !Q.has('seq')) return;
  document.body.style.background='#000';
  const hud=document.createElement('div');
  hud.style.cssText='position:fixed;left:12px;bottom:10px;z-index:9;color:#8C8C8C;'
    +'font:12px ui-monospace,monospace;letter-spacing:.14em;pointer-events:none';
  document.body.append(hud);

  let plan=null, span=parseFloat(Q.get('dur')||'12');
  const start=performance.now();
  function frame(){
    let t=((performance.now()-start)/1000);
    if(plan){
      t%=plan.duration;
      const cur=plan.scenes.find(s=>t>=s.at&&t<s.until)||plan.scenes[plan.scenes.length-1];
      const fn=SCENES[cur.s]||pick;
      draw(fn,t-cur.at);
      hud.textContent=`${t.toFixed(2)}s / ${plan.duration}s   ${cur.s.toUpperCase()}`;
    }else{
      t%=span;
      draw(pick,t);
      hud.textContent=`${t.toFixed(2)}s / ${span}s   ${(SC||dflt).toUpperCase()}`;
    }
    requestAnimationFrame(frame);}

  if(Q.has('seq')){
    // needs --allow-file-access-from-files when loaded over file://
    fetch(Q.get('seq')).then(r=>r.json()).then(j=>{plan=j;})
      .catch(e=>{hud.textContent='seq load failed — '+e.message;});}
  requestAnimationFrame(frame);}

