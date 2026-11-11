import * as THREE from 'three';
import {furnish} from './furniture.js?v=bedding-1';
import {makeAvatar} from './avatar.js?v=bed-axis-3';
import {doorApproach,makeDoor} from './doors.js';

const names={living:'客厅',bedroom:'卧室',study:'书房',gaming:'电竞房',garden:'后花园',kitchen:'厨房'};
const stand={living:[.60,0,.72],bedroom:[-.8,0,.31],study:[1.91,0,.71],gaming:[.56,0,-.66],
             garden:[.12,0,.39],kitchen:[1.33,0,-1.17]};
const positions={
  sleep:[-3.42,.78,-1.00],recline:[-3.42,.78,-1.00],
  sit:[-3.0,-.48,1.19],listen:[-3.0,-.48,1.19],watch:[-3.0,-.48,1.19],
  game:[.9,-.60,-2.00],browse:[.9,-.60,-2.00],
  write:[1.4,-.63,.02],draw:[1.4,-.63,.02],
  wash:[.59,0,-2.03],cook:[2.44,0,-2.02],
  eat:[-.69,0,2.03],water:[-2.6,0,-.36],pet:[-1.72,0,2.20],unpack:[-.37,0,2.57],
  window:[-.10,0,-2.95],shelve:[3.86,0,-2.28],dress:[2.64,0,-1.94],
};
function locate(state){
  if(state.away)return ['living',stand.living,'idle'];
  // Transitional fallback for room snapshots written before the server projection was introduced.
  if(!state.room && ['asleep','nap'].includes(state.sleepMode))return ['bedroom',positions.sleep,'sleep'];
  const room=names[state.room]?state.room:'living',motion=state.motion||'idle';
  if((motion==='read'&&room==='study')||motion==='sit-read'){
    return [room,room==='living'?positions.sit:positions.write,'sit-read'];
  }
  return [room,positions[motion]||stand[room],motion];
}
const clamp=(v,low,high)=>Math.max(low,Math.min(high,v));
const $=id=>document.getElementById(id);

export function mount(){
  const canvas=$('scene'), renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
  renderer.setClearColor(0x000000,0);
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.10;
  const camera=new THREE.OrthographicCamera(-6,6,4,-4,.1,90);
  const roomCache=new Map();
  const avatarLayer=new THREE.Group();
  const louxue=makeAvatar(avatarLayer,kind=>{
    canvas.dataset.model=kind;
    $('model-credit').hidden=kind!=='vrm';
    $('avatar-state').hidden=kind==='vrm';
    $('avatar-state').textContent=kind==='failed'?'形象加载失败，点击重试':'洛雪的形象正在载入…';
    $('avatar-state').disabled=kind!=='failed';
  });
  let currentRoom='living',actualRoom='living',avatarRoom='living',following=true,active,receivedState=false,doorBusy=false;
  let movementTicket=0,desiredMotionKey='';
  let doorTask=Promise.resolve();
  const raycaster=new THREE.Raycaster();
  function roomFor(id){
    if(roomCache.has(id))return roomCache.get(id);
    const scene=new THREE.Scene();
    const world=furnish(scene,id);
    const ambient=new THREE.HemisphereLight('#fdf0f7','#745a85',2.05);scene.add(ambient);
    const sun=new THREE.DirectionalLight('#ffe0c9',2.65);sun.position.set(1.9,7,4.6);scene.add(sun);
    const rim=new THREE.DirectionalLight('#d2c9ee',.78);rim.position.set(-4,4,-2);scene.add(rim);
    sun.castShadow=true;
    sun.shadow.mapSize.setScalar(innerWidth<700?1024:2048);
    Object.assign(sun.shadow.camera,{left:-6.4,right:6.4,top:6.4,bottom:-6.4,near:.5,far:22});
    sun.shadow.bias=-.00025;sun.shadow.normalBias=.022;sun.shadow.radius=3;
    scene.traverse(object=>{
      if(!object.isMesh)return;
      const materials=[].concat(object.material);
      if(materials.some(material=>material.transparent))return;
      object.receiveShadow=true;
      object.geometry.computeBoundingBox();
      const size=object.geometry.boundingBox.getSize(new THREE.Vector3()).multiply(object.scale);
      const largest=Math.max(size.x,size.y,size.z);
      object.castShadow=largest>.10&&largest<4.4;
    });
    const room={scene,world,ambient,sun,door:makeDoor(scene,id==='garden')};
    roomCache.set(id,room);
    return room;
  }
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
      if(sleeping)point.z-=1.03;
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
    Object.assign(target,{yaw:focus?.25:.47,pitch:focus?(sleeping?.70:.18):.64,zoom:1,x:.06,y:.96,z:.02});
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
  let prior=null,right=false,dragDistance=0;
  function gesture(){
    const [a,b]=pointers.values();
    return b?{x:(a.x+b.x)/2,y:(a.y+b.y)/2,d:Math.hypot(a.x-b.x,a.y-b.y)}:a;
  }
  canvas.addEventListener('pointerdown',e=>{
    if(!pointers.size){
      dragDistance=0;
      right=e.button===2||e.shiftKey;
    }
    pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    prior=gesture();canvas.setPointerCapture(e.pointerId);canvas.classList.add('dragging');
  });
  canvas.addEventListener('pointermove',e=>{
    if(!pointers.has(e.pointerId))return;
    pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    const current=gesture(),dx=current.x-prior.x,dy=current.y-prior.y;
    dragDistance+=Math.hypot(dx,dy);
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
  canvas.addEventListener('click',e=>{
    if(dragDistance>7 || !active)return;
    const rect=canvas.getBoundingClientRect();
    raycaster.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,
      1-(e.clientY-rect.top)/rect.height*2),camera);
    if(raycaster.intersectObject(active.door.hit,false).length)openDoor();
  });
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
  function show(id){
    const changed=currentRoom!==id || !active;
    currentRoom=id;active=roomFor(id);
    canvas.dataset.room=id;$('room-name').textContent=names[id];
    $('door').textContent=id==='living'?'房门 · 选房间':'房门 · 回客厅';
    if(changed){active.door.close();$('door-menu').hidden=true;}
    for(const item of $('rooms').querySelectorAll('[data-room]')){
      item.setAttribute('aria-current',String(item.dataset.room===id));
    }
    avatarLayer.visible=receivedState && !away && currentRoom===avatarRoom;
    if(avatarLayer.visible)active.scene.add(avatarLayer);
    if(changed)preset(false);
    lighting();
  }
  function setFollow(on){
    following=on;$('follow').setAttribute('aria-pressed',String(on));
    if(on&&!away)show(avatarRoom);
  }
  $('rooms').addEventListener('click',event=>{
    const id=event.target.closest('[data-room]')?.dataset.room;
    if(id){setFollow(false);through(id);}
  });
  async function through(id,arrive,valid=()=>true){
    while(doorBusy)await doorTask;
    if(!valid())return false;
    if(id===currentRoom){arrive?.();return true;}
    doorBusy=true;
    let done;doorTask=new Promise(resolve=>{done=resolve;});
    const previous=active;
    try{
      await previous.door.open();
      if(!valid())return false;
      arrive?.();show(id);previous.door.close();
      await active.door.open();active.door.close();return true;
    }finally{doorBusy=false;done();}
  }

  async function moveToState(id,position,pose,first){
    const ticket=++movementTicket;
    if(first||away||reduce.matches){
      avatarRoom=id;louxue.setRoom(id);louxue.poseAt(position,pose,true);
      if(following&&!away)show(id);else show(currentRoom);return;
    }
    if(avatarRoom!==id){
      const reached=await louxue.poseAt(doorApproach(avatarRoom==='garden'),'stroll');
      if(!reached||ticket!==movementTicket)return;
      const arrive=()=>{avatarRoom=id;louxue.setRoom(id);louxue.poseAt(doorApproach(id==='garden'),'idle',true);};
      if(following){
        if(currentRoom!==avatarRoom)show(avatarRoom);
        if(!await through(id,arrive,()=>ticket===movementTicket))return;
      }else{
        if(currentRoom===avatarRoom)await active.door.open();
        if(ticket!==movementTicket)return;
        arrive();show(currentRoom);
      }
    }
    if(ticket!==movementTicket)return;
    const reached=await louxue.poseAt(position,pose);
    if(ticket===movementTicket)canvas.dataset.motionFailure=reached?'':'unreachable';
  }
  function openDoor(){
    if(currentRoom!=='living'){setFollow(false);through('living');return;}
    active.door.open();
    $('door-menu').hidden=!$('door-menu').hidden;
    if($('door-menu').hidden)active.door.close();
  }
  $('door').onclick=openDoor;
  $('door-menu').addEventListener('click',event=>{
    const id=event.target.closest('[data-destination]')?.dataset.destination;
    if(id){setFollow(false);through(id);}
  });
  $('avatar-state').onclick=()=>louxue.retry();
  $('follow').onclick=()=>setFollow(!following);
  $('room').onclick=()=>preset(false);
  $('louxue').onclick=()=>{setFollow(true);preset(true);};
  $('minus').onclick=()=>zoom(.82);$('plus').onclick=()=>zoom(1.22);
  function lighting(){
    isWarm=override??(hour>=19||hour<7);
    const {world,sun,ambient}=active;
    world.setWarm(isWarm);
    sun.color.set(isWarm?'#ffddbb':'#ffe8d6');sun.intensity=isWarm?1.47:2.35;
    ambient.intensity=isWarm?1.25:1.85;
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
      const [id,position,pose]=locate(state);
      const movedRoom=actualRoom!==id, first=!receivedState;
      receivedState=true;
      actualRoom=id;away=Boolean(state.away);sleeping=['sleep','recline'].includes(pose);
      louxue.setMood(state);
      $('connection-label').textContent=away?'洛雪 · 外出中':'洛雪 · '+names[id];
      const weather=state.weather||{};
      $('weather').textContent=[state.clock,weather.kind,typeof weather.temp==='number'?weather.temp+'°C':''].filter(Boolean).join(' · ')||'洛雪的家';
      $('louxue').disabled=away;
      const newHour=parseInt(state.clock,10);
      if(Number.isFinite(newHour))hour=newHour;
      canvas.dataset.motion=pose;
      const motionKey=id+':'+pose+':'+position.join(',')+':'+away;
      if(motionKey!==desiredMotionKey){desiredMotionKey=motionKey;moveToState(id,position,pose,first).catch(()=>{canvas.dataset.motionFailure='transition';});}
      else if(!following||away)show(currentRoom);
      if(away&&focus)preset(false);
    }catch{
      $('connection').dataset.connected='false';$('connection-label').textContent='房间状态暂未更新';
    }finally{
      setTimeout(sync,12000);
    }
  }
  canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();$('fallback').hidden=false;});
  canvas.addEventListener('webglcontextrestored',()=>{$('fallback').hidden=true;});
  addEventListener('resize',resize);resize();show('living');
  let prev=performance.now();
  renderer.setAnimationLoop(now=>{
    const dt=clamp((now-prev)/1000,0,.05);prev=now;
    const t=now/1000;
    cameraPose(dt);louxue.update(t,dt,reduce.matches);
    canvas.dataset.phase=louxue.motion.stage;canvas.dataset.actionPhase=louxue.motion.taskPhase;
    canvas.dataset.completedCycles=String(louxue.motion.cycles);
    roomCache.get('bedroom')?.world.setResting(avatarRoom==='bedroom'&&!away?louxue.motion.lie:0);
    roomCache.get(avatarRoom)?.world.setAction?.(louxue.motion);
    if(!reduce.matches)active.world.animate(t);
    active.door.update(dt,reduce.matches);
    renderer.render(active.scene,camera);
    if(!canvas.dataset.ready)canvas.dataset.ready='true';
  });
  sync();
}
