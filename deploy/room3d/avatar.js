import * as THREE from 'three';
import {block,cylinder,group,line,oval,shadow} from './shapes.js';

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
  block(props.smallBook,.172,.234,.055,'#7fa0ae');
  block(props.wash,.12,.065,.10,'#d6be9d',0,0,0,.02);
  const held={
    phone:['phone',.155,1.31,.37],game:['game',0,1.13,.39],write:['pen',.16,1.13,.44],
    draw:['pen',.16,1.14,.46],cook:['ladle',.16,1.17,.42],eat:['meal',-.17,1.14,.38],
    water:['can',.17,1.04,.36],unpack:['box',0,1.12,.41],
    shelve:['smallBook',.17,1.37,.36],wash:['wash',.14,1.14,.43],
  };
  const shade=shadow(modelLayer,0,0,1.17,.85,.58);
  const goal=new THREE.Vector3(.53,0,.62);
  root.position.copy(goal);
  let pose='idle',vrm=null,bones={},directions={},blinkAt=2.7,snapNext=true;
  let loading=false;
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
        for(const material of [].concat(obj.material)){
          if(material?.isMToonMaterial&&!materials.has(material)){
            material.color.multiplyScalar(.88);
            materials.add(material);
          }
        }
      });
      const names=['hips','spine','chest','neck','head','leftUpperArm','rightUpperArm','leftLowerArm','rightLowerArm',
                   'leftHand','rightHand','leftUpperLeg','rightUpperLeg','leftLowerLeg','rightLowerLeg'];
      bones=Object.fromEntries(names.map(name=>[name,avatar.humanoid.getNormalizedBoneNode(name)]));
      if(!bones.head||!bones.leftUpperArm||!bones.rightUpperArm)throw new Error('Incomplete avatar rig');
      for(const side of ['left','right']){
        const shoulder=bones[side+'UpperArm'].getWorldPosition(new THREE.Vector3());
        const wrist=bones[side+'Hand']?.getWorldPosition(new THREE.Vector3());
        directions[side]=Math.sign((wrist?.x??0)-shoulder.x)||(side==='left'?1:-1);
      }
      body.add(avatar.scene);vrm=avatar;modelLayer.visible=true;status('vrm');
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
    aim(elbow,hand,wanted);
  }
  function setPose(position,action,snap=false){
    goal.fromArray(position);pose=action;snapNext||=snap;
  }
  function update(t,dt,reduce){
    const delta=root.position.distanceTo(goal);
    const snap=snapNext||reduce;
    if(snap){root.position.copy(goal);snapNext=false;}
    else root.position.lerp(goal,1-Math.exp(-dt*3.7));
    const walk=!snap&&delta>.07;
    const sway=reduce?0:Math.sin(t*3);
    const asleep=pose==='sleep'&&!walk;
    const seated=['sit','sit-read','listen','watch'].includes(pose);
    const sitting=seated&&!walk;
    const reading=(pose==='read'||pose==='sit-read')&&!walk;
    if(!vrm)return;
    const look=walk?Math.atan2(goal.x-root.position.x,goal.z-root.position.z):asleep?.12:sitting?.43:.24;
    const turn=Math.atan2(Math.sin(look-root.rotation.y),Math.cos(look-root.rotation.y));
    root.rotation.y+=turn*(snap?1:.16);
    const lean=asleep||pose==='recline'?Math.PI/2:0;
    body.rotation.z=THREE.MathUtils.lerp(body.rotation.z,lean,snap?1:.18);
    body.position.y=asleep?0:walk?Math.abs(Math.sin(t*9))*.040:reduce?0:Math.sin(t*2)*.009;
    rotate('head',reading?.19:['write','draw','phone','pet','eat','water','wash'].includes(pose)?.22:0,reduce?0:Math.sin(t*.88)*.075,pose==='listen'?sway*.12:reduce?0:Math.sin(t*.71)*.033);
    rotate('chest',pose==='pet'?.44:sitting?.07:0,0,reduce?0:Math.sin(t*1.6)*.018);
    const item=!walk&&held[pose];
    for(const prop of Object.values(props))prop.visible=false;
    if(item){
      const [key,x,y,z]=item;
      const prop=props[key];prop.visible=true;
      prop.position.set(x+(pose==='write'||pose==='draw'?sway*.07:0),y+(pose==='eat'?Math.max(0,sway)*.18:0),z);
      prop.rotation.z=pose==='water'?-.48+sway*.12:pose==='cook'?sway*.35:0;
    }
    for(const [index,side] of ['left','right'].entries()){
      const sign=directions[side], step=walk?Math.sin(t*9+index*Math.PI):0;
      if(reading)aimHand(side,sign=>[sign*.178,1.26,.405]);
      else if(item){
        aimHand(side,sign=>{
          const p=props[item[0]].position;
          return [item[1]===0?sign*.125:sign>0?p.x:-Math.abs(p.x)-.04,p.y,p.z-(item[1]&&sign<0?.12:0)];
        });
      }
      else if(!walk&&pose==='stretch')aimHand(side,sign=>[sign*.38,1.83+sway*.09,.08]);
      else if(!walk&&pose==='pet')aimHand(side,sign=>[sign*.17,.88,.52+sway*.10]);
      else if(!walk&&pose==='browse')aimHand(side,sign=>[sign*.18,1.08+sway*.026,.43]);
      else if(!walk&&pose==='dress')aimHand(side,sign=>[sign*.22,1.43,.27]);
      else if(!walk&&pose==='window')aimHand(side,sign=>[sign*.23,1.16,.31]);
      else{
        rotate(side+'UpperArm',step*.25,0,sign*1.25);
        rotate(side+'LowerArm',sitting?.19:.07,0,sign*.025);
      }
      rotate(side+'UpperLeg',sitting?1.45:step*.36,0,0);
      rotate(side+'LowerLeg',sitting?-1.28:-Math.max(0,-step*.27),0,0);
    }
    if(t>blinkAt+.19)blinkAt=t+3.6;
    const blink=asleep?1:reduce||t<blinkAt?0:Math.sin(Math.min(1,(t-blinkAt)/.19)*Math.PI);
    vrm.expressionManager?.setValue('blink',blink);
    book.visible=reading;shade.visible=!asleep&&!sitting;
    vrm.update(dt);
  }
  return {root,poseAt:setPose,update,retry:load};
}
