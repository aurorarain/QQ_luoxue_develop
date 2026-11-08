import * as THREE from 'three';
import {furnish} from './furniture.js';
import {makeLuoxue} from './character.js';

const spots={
  center:[.53,0,.62],desk:[1.84,0,-.84],sofa:[-2.96,-.035,.98],bed:[-2.05,0,-.64],
  window:[-.14,0,-2.02],shelf:[3.42,0,-1.76],wardrobe:[-3.7,0,-.86],door:[3.84,0,2.58],
};
const clamp=(v,low,high)=>Math.max(low,Math.min(high,v));
const $=id=>document.getElementById(id);

export function mount(){
  const canvas=$('scene'), renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
  renderer.setClearColor(0x000000,0);
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.22;
  const scene=new THREE.Scene();
  const camera=new THREE.OrthographicCamera(-6,6,4,-4,.1,90);
  const world=furnish(scene), louxue=makeLuoxue(scene);
  const ambient=new THREE.HemisphereLight('#fdf0f7','#745a85',2.05);scene.add(ambient);
  const sun=new THREE.DirectionalLight('#ffe0c9',2.65);sun.position.set(1.9,7,4.6);scene.add(sun);
  const rim=new THREE.DirectionalLight('#bcb3ff',1.18);rim.position.set(-4,4,-2);scene.add(rim);
  const reduce=matchMedia('(prefers-reduced-motion: reduce)');
  const view={yaw:.47,pitch:.64,zoom:1,x:.06,y:.96,z:.02};
  const target={...view};
  const panOffset=new THREE.Vector3(), point=new THREE.Vector3();
  let width=1,height=1,focus=false,near=0,override=null,hour=12,isWarm=false,away=false,sleeping=false;
  function resize(){
    width=Math.max(1,canvas.clientWidth);height=Math.max(1,canvas.clientHeight);
    renderer.setSize(width,height,false);
  }
  function cameraPose(dt){
    const smooth=reduce.matches?1:1-Math.exp(-dt*10);
    for(const key of ['yaw','pitch','zoom'])view[key]=THREE.MathUtils.lerp(view[key],target[key],smooth);
    near=THREE.MathUtils.lerp(near,focus?1:0,smooth);
    point.set(target.x,target.y,target.z);
    if(focus){
      point.copy(louxue.root.position);
      point.y+=sleeping?.30:1.22;
      if(sleeping)point.x-=1.03;
    }
    point.add(panOffset);
    for(const key of ['x','y','z'])view[key]=THREE.MathUtils.lerp(view[key],point[key],smooth);
    const {x,y,z,yaw,pitch,zoom}=view, ratio=width/height;
    const vertical=THREE.MathUtils.lerp(Math.max(10.55,13.1/ratio),Math.max(3.22,(sleeping?3.45:2.35)/ratio),near)/zoom;
    camera.left=-vertical*ratio/2;camera.right=-camera.left;camera.top=vertical/2;camera.bottom=-camera.top;
    camera.position.set(x+18*Math.sin(yaw)*Math.cos(pitch),y+18*Math.sin(pitch),z+18*Math.cos(yaw)*Math.cos(pitch));
    camera.lookAt(x,y,z);camera.updateProjectionMatrix();
  }
  function preset(close){
    focus=close&&!away;panOffset.set(0,0,0);
    Object.assign(target,{yaw:focus?.25:.47,pitch:focus?.18:.64,zoom:1,x:.06,y:.96,z:.02});
    $('louxue').setAttribute('aria-pressed',String(focus));$('room').setAttribute('aria-pressed',String(!focus));
  }
  function zoom(factor){target.zoom=clamp(target.zoom*factor,.60,3.1);}
  function rotate(dx,dy){
    target.yaw=clamp(target.yaw-dx*.007,-1.24,1.40);
    target.pitch=clamp(target.pitch+dy*.007,.065,1.37);
  }
  function pan(dx,dy){
    const unit=(camera.top-camera.bottom)/height;
    panOffset.x=clamp(panOffset.x-dx*unit*Math.cos(target.yaw),-7,7);
    panOffset.z=clamp(panOffset.z+dx*unit*Math.sin(target.yaw),-7,7);
    panOffset.y=clamp(panOffset.y+dy*unit,-3,5);
  }
  const pointers=new Map();
  let prior=null,right=false;
  function gesture(){
    const [a,b]=pointers.values();
    return b?{x:(a.x+b.x)/2,y:(a.y+b.y)/2,d:Math.hypot(a.x-b.x,a.y-b.y)}:a;
  }
  canvas.addEventListener('pointerdown',e=>{
    if(!pointers.size)right=e.button===2||e.shiftKey;
    pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    prior=gesture();canvas.setPointerCapture(e.pointerId);canvas.classList.add('dragging');
  });
  canvas.addEventListener('pointermove',e=>{
    if(!pointers.has(e.pointerId))return;
    pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    const current=gesture(),dx=current.x-prior.x,dy=current.y-prior.y;
    if(current.d&&prior.d){zoom(current.d/prior.d);pan(dx,dy);}
    else if(right)pan(dx,dy);
    else rotate(dx,dy);
    prior=current;
  });
  for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>{
    pointers.delete(e.pointerId);prior=gesture();if(!pointers.size)canvas.classList.remove('dragging');
  });
  canvas.addEventListener('wheel',e=>{
    e.preventDefault();const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?height:1);
    zoom(Math.exp(-clamp(delta,-420,420)*.0014));
  },{passive:false});
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
  canvas.addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','0'].includes(e.key))return;
    e.preventDefault();
    if(e.key==='0')preset(false);
    else if(e.key==='+'||e.key==='=')zoom(1.22);
    else if(e.key==='-')zoom(.82);
    else{
      const x=Number(e.key==='ArrowRight')-Number(e.key==='ArrowLeft');
      const y=Number(e.key==='ArrowDown')-Number(e.key==='ArrowUp');
      if(e.shiftKey)pan(x*20,y*20);else rotate(x*20,y*20);
    }
  });
  $('room').onclick=()=>preset(false);$('louxue').onclick=()=>preset(true);
  $('minus').onclick=()=>zoom(.82);$('plus').onclick=()=>zoom(1.22);
  function lighting(){
    isWarm=override??(hour>=19||hour<7);
    world.setWarm(isWarm);
    sun.color.set(isWarm?'#ffd0a8':'#ffe0c9');sun.intensity=isWarm?1.63:2.65;
    ambient.intensity=isWarm?1.37:2.05;
    $('lighting').setAttribute('aria-pressed',String(isWarm));
    $('lighting').textContent=isWarm?'日光':'暖灯';
  }
  $('lighting').onclick=()=>{override=!isWarm;lighting();};
  async function sync(){
    try{
      const res=await fetch('/roomapi/state',{cache:'no-store',signal:AbortSignal.timeout(6500)});
      if(!res.ok)throw new Error('room state unavailable');
      const {state}=await res.json();
      const energy=clamp(Number(state.stats?.体力 ?? 0),0,100);
      $('activity').textContent=state.activity||'待在房间里';
      $('mood').textContent=state.mood||'';
      $('energy').setAttribute('aria-valuenow',String(energy));
      $('energy').firstElementChild.style.width=energy+'%';
      $('connection').dataset.connected='true';
      $('connection-label').textContent=state.away?'洛雪 · 外出中':'洛雪 · 状态已同步';
      const weather=state.weather||{};
      $('weather').textContent=[state.clock,weather.kind,typeof weather.temp==='number'?weather.temp+'°C':''].filter(Boolean).join(' · ')||'洛雪的家';
      const read=/看书|读书|阅读|翻书/.test(state.activity||'')||(!state.activity&&state.action==='read');
      sleeping=['asleep','nap'].includes(state.sleepMode);
      away=Boolean(state.away);louxue.root.visible=!away;
      $('louxue').disabled=away;
      if(away&&focus)preset(false);
      const pose=sleeping?'sleep':state.spot==='sofa'?(read?'sit-read':'sit'):read?'read':'idle';
      louxue.poseAt(sleeping?[-1.90,1.025,-2.11]:(spots[state.spot]||spots.center),pose);
      const newHour=parseInt(state.clock,10);
      if(Number.isFinite(newHour)&&hour!==newHour){hour=newHour;lighting();}
    }catch{
      $('connection').dataset.connected='false';$('connection-label').textContent='房间状态暂未更新';
    }finally{
      setTimeout(sync,12000);
    }
  }
  canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();$('fallback').hidden=false;});
  canvas.addEventListener('webglcontextrestored',()=>{$('fallback').hidden=true;});
  addEventListener('resize',resize);resize();preset(false);lighting();
  let prev=performance.now();
  renderer.setAnimationLoop(now=>{
    const dt=clamp((now-prev)/1000,0,.05);prev=now;
    const t=now/1000;
    cameraPose(dt);louxue.update(t,dt,reduce.matches);
    if(!reduce.matches)world.animate(t);
    renderer.render(scene,camera);
    if(!canvas.dataset.ready)canvas.dataset.ready='true';
  });
  sync();
}
