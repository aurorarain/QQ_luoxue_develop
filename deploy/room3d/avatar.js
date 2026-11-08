import * as THREE from 'three';
import {block,group,shadow} from './shapes.js';
import {makeLuoxue} from './character.js';

export function makeAvatar(layer,status){
  const root=group(layer), fallbackLayer=group(root);
  const fallback=makeLuoxue(fallbackLayer);
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
  const shade=shadow(modelLayer,0,0,1.17,.85,.58);
  const goal=new THREE.Vector3(.53,0,.62);
  root.position.copy(goal);
  let pose='idle',vrm=null,bones={},directions={},blinkAt=2.7,snapNext=true;
  fallback.poseAt([0,0,0],'idle');
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
      body.add(avatar.scene);vrm=avatar;fallbackLayer.visible=false;modelLayer.visible=true;status('vrm');
    }).catch(error=>{console.warn('Avatar asset did not load',error);status('fallback');});

  function rotate(name,x=0,y=0,z=0){if(bones[name])bones[name].rotation.set(x,y,z);}
  function aim(bone,child,destination){
    const from=bone.parent.worldToLocal(child.getWorldPosition(new THREE.Vector3())).sub(bone.position);
    const to=bone.parent.worldToLocal(destination.clone()).sub(bone.position);
    bone.quaternion.setFromUnitVectors(from.normalize(),to.normalize());
  }
  function holdBook(side){
    const shoulder=bones[side+'UpperArm'],elbow=bones[side+'LowerArm'],hand=bones[side+'Hand'];
    if(!shoulder||!elbow||!hand)return;
    shoulder.quaternion.identity();elbow.quaternion.identity();
    const start=shoulder.getWorldPosition(new THREE.Vector3());
    const mid=elbow.getWorldPosition(new THREE.Vector3());
    const tip=hand.getWorldPosition(new THREE.Vector3());
    const upper=start.distanceTo(mid),lower=mid.distanceTo(tip);
    const sign=Math.sign(body.worldToLocal(start.clone()).x);
    const wanted=body.localToWorld(new THREE.Vector3(sign*.178,1.26,.405));
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
    const asleep=pose==='sleep'&&!walk;
    const seated=pose==='sit'||pose==='sit-read';
    const sitting=seated&&!walk;
    const reading=(pose==='read'||pose==='sit-read')&&!walk;
    if(!vrm){
      fallbackLayer.position.y=seated?.445:0;
      fallback.poseAt([0,0,0],pose);
      fallback.update(t,dt,reduce);
      return;
    }
    const look=asleep?.12:sitting?.43:.24;
    root.rotation.y=THREE.MathUtils.lerp(root.rotation.y,look,snap?1:.16);
    const lean=asleep?Math.PI/2:0;
    body.rotation.z=THREE.MathUtils.lerp(body.rotation.z,lean,snap?1:.18);
    body.position.y=asleep?0:walk?Math.abs(Math.sin(t*9))*.040:reduce?0:Math.sin(t*2)*.009;
    rotate('head',reading?.19:0,reduce?0:Math.sin(t*.88)*.075,reduce?0:Math.sin(t*.71)*.033);
    rotate('chest',sitting?.07:0,0,reduce?0:Math.sin(t*1.6)*.018);
    for(const [index,side] of ['left','right'].entries()){
      const sign=directions[side], step=walk?Math.sin(t*9+index*Math.PI):0;
      if(reading)holdBook(side);
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
  return {root,poseAt:setPose,update};
}
