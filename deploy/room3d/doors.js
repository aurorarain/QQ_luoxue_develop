import * as THREE from 'three';
import {block,group,mesh,oval} from './shapes.js';

export const DOOR_OPENING={wallX:-4.79,center:2.24,width:1.33,height:2.33};
export const GATE_CENTER=1.65;
export function doorApproach(garden){return [-3.65,0,garden?GATE_CENTER:DOOR_OPENING.center];}

export function makeDoor(scene,garden){
  const frame=group(scene,garden?-4.33:DOOR_OPENING.wallX,garden?.004:-.018,
    garden?GATE_CENTER:DOOR_OPENING.center);
  frame.rotation.y=Math.PI/2;
  const wood=garden?'#b9897c':'#b198b7', trim=garden?'#d8ad97':'#f2dcd7';
  const height=garden?1.55:2.20, width=1.07;
  for(const x of [-width/2-.06,width/2+.06])block(frame,.13,height+.145,.18,trim,x,(height+.145)/2,0,.025);
  block(frame,width+.23,.14,.16,trim,0,height+.075,0,.027);
  block(frame,width+.20,.036,.23,trim,0,.016,0,.015);
  const leaf=group(frame,-width/2,0,.04);
  if(garden){
    for(let i=0;i<6;i++)block(leaf,.113,height-.13,.08,wood,.085+i*.18,height/2,0,.018);
    for(const y of [.32,1.18])block(leaf,width,.12,.082,wood,width/2,y,.04,.02);
  }else{
    block(leaf,width,height,.12,wood,width/2,height/2,0,.035);
    for(const y of [.52,1.53])block(leaf,width-.18,.69,.028,'#ceb6cb',width/2,y,.073,.025);
  }
  oval(leaf,.057,.057,.055,'#ce9d75',width-.14,height*.47,.105);
  const hit=mesh(frame,new THREE.BoxGeometry(width+.23,height+.16,.30),
    new THREE.MeshBasicMaterial({transparent:true,opacity:0,depthWrite:false}),0,height/2,.06);
  let target=0;
  return {hit,open(){target=-Math.PI*.43;},close(){target=0;},update(dt,reduce){
    leaf.rotation.y=THREE.MathUtils.lerp(leaf.rotation.y,target,reduce?1:1-Math.exp(-dt*9));
  }};
}
