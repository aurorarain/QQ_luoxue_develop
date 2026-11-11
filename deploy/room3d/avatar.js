import * as THREE from 'three';
import {block,cylinder,group,line,oval,shadow} from './shapes.js';
import {MotionDirector} from './motion.js';
import {floorRoute} from './navigation.js';

export function makeAvatar(layer,status){
  const root=group(layer);
  const modelLayer=group(root);
  modelLayer.visible=false;
  const body=group(modelLayer);
  const book=group(body,0,1.23,.39);
  for(const sign of [-1,1]){
    const page=group(book,sign*.115,0,0);page.rotation.set(-.84,sign*-.22,0);
    block(page,.23,.31,.034,'#7997a4');
    block(page,.212,.29,.024,'#fff2df',0,0,.021);
    for(let i=0;i<4;i++)block(page,.145,.005,.004,'#a294aa',0,.087-i*.045,.035,.002);
  }
  const turningPage=group(book);
  block(turningPage,.21,.27,.004,'#fff2df',.106,0,.045,.001);
  const props={
    phone:group(body),game:group(body),pen:group(body),ladle:group(body),
    meal:group(body),can:group(body),box:group(body),smallBook:group(body),wash:group(body),
  };
  block(props.phone,.124,.217,.032,'#69608b');
  block(props.phone,.105,.184,.006,'#aacde2',0,0,.019,.01);
  block(props.game,.281,.115,.085,'#9880b8');
  for(const x of [-.073,.073])oval(props.game,.026,.018,.029,'#f5dce4',x,.053,.019);
  cylinder(props.pen,.011,.013,.18,'#7d779c',0,0,0).rotation.z=.55;
  line(props.ladle,[[0,-.18,0],[0,.12,0]],.018,'#ad806e');
  oval(props.ladle,.077,.03,.088,'#c39780',0,-.17,0);
  cylinder(props.meal,.13,.088,.083,'#dca4a4',0,0,0);
  oval(props.meal,.12,.034,.107,'#fff1d9',0,.049,0);
  cylinder(props.can,.116,.137,.15,'#8dafac',0,-.042,0);
  line(props.can,[[.08,0,0],[.24,-.014,0],[.33,.083,0]],.023,'#8dafac');
  block(props.box,.315,.195,.23,'#bf9b86');
  block(props.box,.035,.201,.237,'#edd2aa');
  const flaps=[-1,1].map(sign=>{
    const flap=group(props.box,sign*.156,.10,0);
    block(flap,.156,.012,.23,'#d3b29b',-sign*.078,0,0,.003);return flap;
  });
  const spoon=group(body);line(spoon,[[0,-.08,0],[0,.08,0]],.008,'#c6a397');
  oval(spoon,.025,.036,.008,'#d9b6a5',0,.101,0);
  const gift=group(body);block(gift,.15,.17,.05,'#a8c6c7',0,0,0,.015);
  block(props.smallBook,.172,.234,.055,'#7fa0ae');
  block(props.wash,.12,.065,.10,'#d6be9d',0,0,0,.02);
  for(const prop of Object.values(props))prop.visible=false;
  line(props.can,[[-.06,.02,0],[-.18,.09,0],[-.16,.18,0],[-.03,.20,0]],.017,'#8dafac');
  const held={
    phone:['phone',-.155,1.35,.34],game:['game',0,1.08,.27],write:['pen',-.16,1.105,.45],
    draw:['pen',-.16,1.105,.45],cook:['ladle',-.02,1.37,.64],eat:['meal',.17,1.15,.38],
    water:['can',-.10,1.14,.27],unpack:['box',0,1.12,.41],
    shelve:['smallBook',-.31,.855,.49],wash:['wash',.06,1.14,.57],
  };
  const shade=shadow(modelLayer,0,0,1.17,.85,.58);
  let room='living';
  const director=new MotionDirector([.53,0,.62],(a,b)=>floorRoute(room,a,b));
  root.position.fromArray(director.position);
  let pose='idle',vrm=null,bones={},directions={},blinkAt=2.7,frame=director.update(0),stride=0,hipHeight=1.25,lastProp=null;
  const waterDrops=group(layer),steam=group(layer);
  for(let i=0;i<12;i++)oval(waterDrops,.009,.022,.009,new THREE.MeshBasicMaterial({color:'#b5e2e8',transparent:true,opacity:.72}));
  for(let i=0;i<7;i++)oval(steam,.028,.038,.028,new THREE.MeshBasicMaterial({color:'#fff1e4',transparent:true,opacity:.16,depthWrite:false}));
  let loading=false;
  let feeling='relaxed',expression=0,wanderOrigin=null,wanderStep=0;
  function load(){
    if(loading||vrm)return;
    loading=true;status('loading');
    Promise.all([import('/room3d/vendor/GLTFLoader.js'),import('/room3d/vendor/three-vrm.module.js')])
    .then(async ([gltfLib,vrmLib])=>{
      const loader=new gltfLib.GLTFLoader();
      loader.register(parser=>new vrmLib.VRMLoaderPlugin(parser));
      const gltf=await loader.loadAsync('/room3d/assets/vita.vrm');
      const avatar=gltf.userData.vrm;
      if(!avatar?.humanoid)throw new Error('VRM humanoid rig unavailable');
      vrmLib.VRMUtils.rotateVRM0(avatar);
      vrmLib.VRMUtils.removeUnnecessaryVertices(avatar.scene);
      if(vrmLib.VRMUtils.combineSkeletons)vrmLib.VRMUtils.combineSkeletons(avatar.scene);
      avatar.scene.updateMatrixWorld(true);
      const bounds=new THREE.Box3().setFromObject(avatar.scene);
      const height=bounds.max.y-bounds.min.y;
      if(!Number.isFinite(height)||height<.35||height>4)throw new Error('Invalid avatar bounds');
      const scale=2.19/height;
      avatar.scene.scale.setScalar(scale);
      avatar.scene.position.y=-bounds.min.y*scale;
      const materials=new Set();
      avatar.scene.traverse(obj=>{
        if(!obj.isMesh)return;
        obj.frustumCulled=false;
        obj.castShadow=true;obj.receiveShadow=true;
        for(const material of [].concat(obj.material)){
          if(material?.isMToonMaterial&&!materials.has(material)){
            material.color.multiplyScalar(.88);
            if(typeof material.outlineWidthFactor==='number')material.outlineWidthFactor*=.75;
            if(material.map)material.map.anisotropy=4;
            materials.add(material);
          }
        }
      });
      const names=['hips','spine','chest','neck','head','leftUpperArm','rightUpperArm','leftLowerArm','rightLowerArm',
                   'leftHand','rightHand','leftUpperLeg','rightUpperLeg','leftLowerLeg','rightLowerLeg','leftFoot','rightFoot'];
      for(const side of ['left','right'])for(const finger of ['Thumb','Index','Middle','Ring','Little']){
        for(const segment of ['Proximal','Intermediate','Distal'])names.push(side+finger+segment);
      }
      bones=Object.fromEntries(names.map(name=>[name,avatar.humanoid.getNormalizedBoneNode(name)]));
      if(!bones.head||!bones.leftUpperArm||!bones.rightUpperArm)throw new Error('Incomplete avatar rig');
      for(const side of ['left','right']){
        const shoulder=bones[side+'UpperArm'].getWorldPosition(new THREE.Vector3());
        const wrist=bones[side+'Hand']?.getWorldPosition(new THREE.Vector3());
        directions[side]=Math.sign((wrist?.x??0)-shoulder.x)||(side==='left'?1:-1);
      }
      body.add(avatar.scene);vrm=avatar;
      hipHeight=body.worldToLocal(bones.hips.getWorldPosition(new THREE.Vector3())).y;
      modelLayer.visible=true;status('vrm');
    }).catch(error=>{console.warn('Avatar asset did not load',error);status('failed');})
      .finally(()=>{loading=false;});
  }
  load();

  function rotate(name,x=0,y=0,z=0){if(bones[name])bones[name].rotation.set(x,y,z);}
  function aim(bone,child,destination){
    const from=bone.parent.worldToLocal(child.getWorldPosition(new THREE.Vector3())).sub(bone.position);
    const to=bone.parent.worldToLocal(destination.clone()).sub(bone.position);
    bone.quaternion.setFromUnitVectors(from.normalize(),to.normalize());
  }
  function aimHand(side,target){
    const shoulder=bones[side+'UpperArm'],elbow=bones[side+'LowerArm'],hand=bones[side+'Hand'];
    if(!shoulder||!elbow||!hand)return;
    shoulder.quaternion.identity();elbow.quaternion.identity();
    const start=shoulder.getWorldPosition(new THREE.Vector3());
    const mid=elbow.getWorldPosition(new THREE.Vector3());
    const tip=hand.getWorldPosition(new THREE.Vector3());
    const upper=start.distanceTo(mid),lower=mid.distanceTo(tip);
    const sign=Math.sign(body.worldToLocal(start.clone()).x);
    const wanted=body.localToWorld(new THREE.Vector3(...target(sign)));
    const axis=wanted.clone().sub(start).normalize();
    const distance=THREE.MathUtils.clamp(start.distanceTo(wanted),Math.abs(upper-lower)+.001,upper+lower-.001);
    const reach=(upper*upper-lower*lower+distance*distance)/(2*distance);
    const height=Math.sqrt(Math.max(0,upper*upper-reach*reach));
    const out=body.localToWorld(new THREE.Vector3(sign*.34,.81,.11)).sub(start);
    out.addScaledVector(axis,-out.dot(axis)).normalize();
    aim(shoulder,elbow,start.clone().addScaledVector(axis,reach).addScaledVector(out,height));
    aim(elbow,hand,start.clone().addScaledVector(axis,distance));
  }
  const previous=new Map(),targets=new Map();
  let crouchBlend=0;
  const ease=v=>{v=THREE.MathUtils.clamp(v,0,1);return v*v*(3-2*v);};
  function setPose(position,action,snap=false){wanderOrigin=action==='stroll'?[...position]:null;return director.request(position,action,snap);}
  function park(prop){if(prop&&prop.parent===body&&layer.parent)layer.parent.attach(prop);}
  function update(t,dt,reduce){
    frame=director.update(dt,reduce);pose=frame.action;
    const distance=Math.hypot(root.position.x-frame.position[0],root.position.z-frame.position[2]);
    root.position.fromArray(frame.position);root.rotation.y=frame.heading;
    const walk=frame.moving,seat=frame.seat,lie=frame.lie,perform=frame.stage==='perform'||frame.stage==='put-away';
    const e=perform?frame.engagement:0,p=frame.work;
    const wave=reduce?0:Math.sin(p*Math.PI*4),soft=reduce?0:Math.sin(t*1.55);
    const reading=['read','sit-read'].includes(pose)&&perform;
    const item=perform&&held[pose];
    const working=perform&&frame.taskPhase==='work'&&!frame.completed;
    const asleep=pose==='sleep'&&lie>.95;
    if(walk)stride+=distance*7.5;
    if(!reduce&&wanderOrigin&&wanderOrigin[0]>-3&&frame.stage==='perform'&&frame.time>2){
      const offsets=[[.6,0],[-.5,.5],[0,-.45],[0,0]],offset=offsets[wanderStep++%4];
      director.request([wanderOrigin[0]+offset[0],0,wanderOrigin[2]+offset[1]],'stroll');
    }
    waterDrops.visible=false;steam.visible=false;spoon.visible=false;gift.visible=gift.parent!==body;
    if(!vrm)return;
    for(const [name,bone] of Object.entries(bones))if(bone){
      if(!previous.has(name)){previous.set(name,new THREE.Quaternion());targets.set(name,new THREE.Quaternion());}
      previous.get(name).copy(bone.quaternion);
    }
    const desiredCrouch=frame.completed||!perform?0:pose==='unpack'?1.1:pose==='water'?1.1*(1-e):pose==='pet'?.72:pose==='wash'?.45*e:pose==='cook'?.32*e:pose==='shelve'?.85*e:0;
    crouchBlend=THREE.MathUtils.lerp(crouchBlend,desiredCrouch,reduce?1:1-Math.exp(-dt*7));
    const drop=1.04*(1-Math.cos(crouchBlend));
    const tilt=lie*(Math.PI/2-.06);
    body.rotation.set(-tilt,0,0);
    body.position.y=hipHeight*(1-lie+lie*Math.sin(.06)-Math.cos(tilt))-drop+
      (walk?Math.abs(Math.sin(stride))*.027:reduce?0:soft*.006*(1-lie));
    body.position.z=hipHeight*(-lie*Math.cos(.06)+Math.sin(tilt));
    const lift=Math.max(0,-root.position.y);
    const support=['sit-up','stand-up','sit-down','lie-down'].includes(frame.stage);
    const taskActive=perform&&!frame.completed;
    const lean=pose==='unpack'?.34*crouchBlend/1.1:taskActive?(pose==='pet'?.40*e:pose==='water'?.42*(1-e):
      ['write','draw','browse'].includes(pose)&&seat>.5?.27:pose==='cook'?.48*e:pose==='wash'?.60*e:pose==='shelve'?.45*e:seat*.06):seat*.06;
    rotate('spine',-lean*.65,0,0);
    rotate('chest',-lean*.65+(reduce?0:soft*.008),0,walk?Math.sin(stride)*.025:0);
    rotate('hips',0,0,lie>.1||seat>.1||walk||reduce?0:Math.sin(t*.71)*.008);
    rotate('head',support?-.16:reading?-.19:taskActive&&pose==='game'?.18:taskActive&&pose==='browse'?.32:
      taskActive&&['write','draw','phone','pet','eat','water','wash','unpack'].includes(pose)?-.23:0,
      reduce?0:pose==='watch'?Math.sin(t*.4)*.14:Math.sin(t*.72)*.04,
      pose==='listen'&&perform?wave*.065:0);
    root.updateMatrixWorld(true);
    let prop=null,point=null;
    if(item){
      const [key,x,y,z]=item;prop=props[key];
      const placed=pose==='shelve'&&prop.userData.placedSequence===frame.sequence;
      if(!placed&&prop.parent!==body)body.attach(prop);
      prop.visible=true;
      const home=pose==='water'?[-.12,.78,.35]:pose==='unpack'?[0,.67,.43]:
        pose==='game'?[0,1.10+lift,.49]:['write','draw'].includes(pose)?[x,1.08+lift,.45]:
        pose==='cook'?[-.20,1.12,.34]:pose==='shelve'?[x,1.08,.18]:
        pose==='wash'?[.13,1.04,.39]:[x,.97+lift,.13];
      point=[THREE.MathUtils.lerp(home[0],x,e),THREE.MathUtils.lerp(home[1],y+lift,e),THREE.MathUtils.lerp(home[2],z,e)];
      if(['cook','wash','write','draw','game','shelve'].includes(pose))point[1]+=drop;
      if(working){
        if(pose==='write'||pose==='draw'){point[0]+=Math.sin(p*Math.PI*8)*.045;point[2]+=Math.cos(p*Math.PI*4)*.035;}
        if(pose==='cook'){point[0]+=Math.sin(p*Math.PI*4)*.095;point[2]+=Math.cos(p*Math.PI*4)*.075;}
        if(pose==='shelve'){point[1]+=.025*Math.sin(p*Math.PI);}
        if(pose==='wash'){point[0]+=wave*.032;point[2]+=.018*Math.cos(p*Math.PI*6);}
      }
      if(!placed){
        prop.position.fromArray(point);
        prop.rotation.set(pose==='water'?-.65*e:pose==='cook'?Math.PI/2*(1-e):0,
          pose==='water'?-Math.PI/2:0,pose==='cook'?wave*.18:pose==='phone'?.08:0);
      }
      if(pose==='shelve'&&working&&p>.56){
        if(!placed){prop.position.set(x,.855+drop,.49);prop.userData.placedSequence=frame.sequence;park(prop);}
        point=home.map((value,i)=>THREE.MathUtils.lerp(value,[x,.855+drop,.49][i],1-ease((p-.56)/.44)));
      }
      flaps.forEach((flap,i)=>{flap.rotation.z=(i?1:-1)*e*1.36;});
      if(lastProp&&lastProp!==prop)park(lastProp);
      lastProp=prop;
      if(frame.taskPhase==='rest'&&frame.stage==='perform'&&pose!=='phone')park(prop);
      if(pose==='phone')prop.visible=e>.025;
    }else if(lastProp){park(lastProp);lastProp=null;}
    book.visible=reading;
    book.position.set(0,THREE.MathUtils.lerp(1.0,1.27,e)+lift,THREE.MathUtils.lerp(.20,.405,e));
    turningPage.visible=reading&&working&&p>.62;
    turningPage.rotation.set(-.84,-Math.PI*ease((p-.62)/.30),0);
    const bite=pose==='eat'&&working?ease(Math.sin(Math.PI*p)**2):0;
    const rightTarget=pose==='eat'?[-.12,THREE.MathUtils.lerp(1.18,1.76,bite),THREE.MathUtils.lerp(.36,.19,bite)]:
      pose==='unpack'?[-.08,1.12+.25*Math.sin(p*Math.PI),.40]:null;
    if(pose==='eat'&&perform){
      spoon.visible=e>.1;spoon.position.fromArray(rightTarget);spoon.rotation.set(Math.PI*.45-bite*.70,0,-.18);
    }
    if(pose==='unpack'&&working&&p>.30&&gift.userData.placedSequence!==frame.sequence){
      if(gift.parent!==body)body.attach(gift);
      const put=ease((p-.65)/.25);
      rightTarget[0]=THREE.MathUtils.lerp(rightTarget[0],-.28,put);
      rightTarget[1]=THREE.MathUtils.lerp(rightTarget[1],.67,put);
      rightTarget[2]=THREE.MathUtils.lerp(rightTarget[2],.52,put);
      gift.visible=true;gift.position.fromArray(rightTarget);gift.position.y-=.025;
      if(p>.90){gift.userData.placedSequence=frame.sequence;park(gift);}
    }
    for(const [index,side] of ['left','right'].entries()){
      const sign=directions[side],step=walk?Math.sin(stride+index*Math.PI):0;
      if(support)aimHand(side,sign=>[sign*.24,1.03,.13]);
      else if(reading)aimHand(side,sign=>[sign*.178,book.position.y+.03,book.position.z]);
      else if(item&&e>.03){
        aimHand(side,sign=>{
          if(side==='right'&&rightTarget)return rightTarget;
          if(pose==='cook')return side==='right'?[point[0],point[1]+.08,point[2]]:[-.25,1.17+drop,.64];
          if(pose==='wash')return [sign*.04+wave*.014,point[1],.57];
          if(['write','draw'].includes(pose))return side==='right'?[point[0],point[1]+.055,point[2]-.015]:[.18,1.03+lift,.43];
          if(pose==='water'&&side==='right')return body.worldToLocal(prop.localToWorld(new THREE.Vector3(-.12,.13,0))).toArray();
          if(['phone','water','shelve'].includes(pose))return side==='right'?point:[Math.abs(point[0])*.7,point[1]-.12,point[2]-.04];
          if(pose==='eat')return point;
          return [item[1]===0?sign*.125:sign>0?point[0]:-Math.abs(point[0])-.04,point[1],point[2]-(item[1]&&sign<0?.10:0)];
        });
      }else if(perform&&pose==='stretch'){
        const liftArms=frame.completed?0:Math.sin(Math.PI*frame.cycle)**2;
        aimHand(side,sign=>[sign*(.27+.11*liftArms),1.08+.84*liftArms,.10]);
      }else if(perform&&pose==='pet')aimHand(side,sign=>[sign*.17,.86,.48+wave*.06]);
      else if(perform&&pose==='browse')aimHand(side,sign=>[sign*.18,1.10+lift+wave*.009,.46]);
      else if(perform&&pose==='dress')aimHand(side,sign=>[sign*.22,1.10+.38*Math.sin(frame.cycle*Math.PI),.20]);
      else if(perform&&pose==='window')aimHand(side,sign=>[sign*.22,1.20,.43]);
      else{
        rotate(side+'UpperArm',-step*.31,0,sign*1.25);
        rotate(side+'LowerArm',seat*.19+.07,0,sign*.025);
      }
      rotate(side+'UpperLeg',seat*1.45+(1-seat)*(step*.42+crouchBlend),0,0);
      rotate(side+'LowerLeg',seat*-1.28+(1-seat)*(-Math.max(0,-step*.45)-2*crouchBlend),0,0);
      rotate(side+'Foot',seat*-.17+(walk?-step*.12:0)+crouchBlend,0,0);
      rotate(side+'Hand',0,0,sign*(item?-.04:.025));
      const middle=bones[side+'MiddleProximal'],hand=bones[side+'Hand'];
      let fingertips=null;
      if(middle&&hand){
        if(reading)fingertips=[sign*.11,book.position.y-.035,book.position.z+.035];
        else if(item&&e>.05){
          if(side==='right'&&['write','draw'].includes(pose))fingertips=[point[0],point[1]-.045,point[2]];
          else if(side==='right'&&rightTarget)fingertips=[rightTarget[0],rightTarget[1]-.05,rightTarget[2]+.03];
          else fingertips=[point[0]+sign*.025,point[1]-.035,point[2]+.025];
        }else if(perform&&pose==='browse')fingertips=[sign*.18,1.04+lift,.49];
        if(fingertips)aim(hand,middle,body.localToWorld(new THREE.Vector3(...fingertips)));
      }
      for(const finger of ['Index','Middle','Ring','Little']){
        const curl=item&&e>.1?.29:lie>.5?.12:.17;
        const axis=Math.sign(bones[side+finger+'Intermediate']?.position.x)||sign;
        rotate(side+finger+'Proximal',0,axis*curl,0);
        rotate(side+finger+'Intermediate',0,axis*curl*.65,0);
        rotate(side+finger+'Distal',0,axis*curl*.35,0);
      }
      rotate(side+'ThumbProximal',0,0,-sign*(pose==='game'&&working?.18+.10*Math.sin(p*Math.PI*10):.10));
    }
    const blend=reduce?1:1-Math.exp(-dt*13);
    for(const [name,bone] of Object.entries(bones))if(bone){
      targets.get(name).copy(bone.quaternion);bone.quaternion.copy(previous.get(name)).slerp(targets.get(name),blend);
    }
    if(t>blinkAt+.19)blinkAt=t+3.6;
    const blink=asleep?1:reduce||t<blinkAt?0:Math.sin(Math.min(1,(t-blinkAt)/.19)*Math.PI);
    vrm.expressionManager?.setValue('blink',blink);
    vrm.expressionManager?.setValue('aa',pose==='eat'?bite*.18:0);
    expression=THREE.MathUtils.lerp(expression,asleep?0:feeling==='relaxed'?.13:.34,1-Math.exp(-dt*3));
    for(const name of ['happy','sad','angry','surprised','relaxed'])vrm.expressionManager?.setValue(name,name===feeling?expression:0);
    shade.visible=lie<.05&&seat<.05;
    vrm.update(dt);root.updateMatrixWorld(true);
    waterDrops.visible=working&&!reduce&&['water','wash'].includes(pose);
    if(waterDrops.visible){
      const tip=pose==='water'?props.can.localToWorld(new THREE.Vector3(.33,.083,0)):new THREE.Vector3(.52,1.26,-2.618);
      waterDrops.children.forEach((drop,i)=>{const progress=(t*1.7+i/12)%1;
        drop.position.set(tip.x+Math.sin(i*2)*.012,tip.y-progress*(pose==='water'?.66:.22),tip.z+progress*.035);});
    }
    steam.visible=pose==='cook'&&working&&!reduce;
    steam.children.forEach((puff,i)=>{const progress=(t*.35+i/7)%1;puff.position.set(2.46+Math.sin(i+t)*.04,1.28+progress*.40,-2.77);puff.scale.setScalar(.5+progress);puff.material.opacity=(1-progress)*.14;});
  }
  return {root,poseAt:setPose,update,retry:load,setRoom(id){room=id;},get motion(){return frame;},setMood(state){
    const mood=String(state.mood||'');
    feeling=/难过|低落|委屈|伤心/.test(mood)?'sad':/生气|恼火|烦躁/.test(mood)?'angry':
      /惊讶|吃惊/.test(mood)?'surprised':/开心|高兴|愉快|心情很好|嘴角/.test(mood)?'happy':'relaxed';
  }};
}
