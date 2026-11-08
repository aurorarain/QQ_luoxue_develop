import * as THREE from 'three';
import {block,cylinder,group,line,mesh,oval,shadow} from './shapes.js';

const skin='#ffd9c5', rosy='#e89b9d', cream='#fff2e3', white='#f5ebff';
const navy='#26365d', ink='#20213e', blue='#3f5e9f', aqua='#71d1d4';

export function makeLuoxue(scene){
  const root=group(scene), body=group(root), head=group(body,0,1.85,0);
  const leftLeg=group(body,-.155,.62,0), rightLeg=group(body,.155,.62,0);
  for(const leg of [leftLeg,rightLeg]){
    oval(leg,.115,.255,.112,white,0,-.235,0);
    block(leg,.23,.15,.34,ink,0,-.53,.07,.07);
    block(leg,.225,.048,.32,'#49587b',0,-.585,.07,.025);
    oval(leg,.106,.039,.045,aqua,0,-.48,.15);
  }
  cylinder(body,.227,.463,.465,navy,0,.88,0);
  cylinder(body,.447,.486,.055,white,0,.649,0);
  oval(body,.263,.322,.183,navy,0,1.216,.006);
  cylinder(body,.09,.095,.145,skin,0,1.54,.04);
  cylinder(body,.257,.29,.06,ink,0,1.108,0);
  oval(body,.186,.228,.074,cream,0,.872,.385);
  oval(body,.137,.172,.065,white,0,1.236,.164);
  for(const sign of [-1,1]){
    const collar=oval(body,.106,.05,.045,cream,sign*.091,1.39,.16);collar.rotation.z=-sign*.32;
    const bow=oval(body,.086,.054,.035,'#73bed2',sign*.065,1.32,.226);bow.rotation.z=sign*.35;
  }
  oval(body,.035,.035,.039,aqua,0,1.32,.26);
  oval(body,.084,.048,.009,'#72a9c7',0,.85,.46);
  const badgeTail=oval(body,.038,.018,.009,'#72a9c7',.074,.872,.458);badgeTail.rotation.z=.52;
  oval(body,.009,.011,.004,ink,-.043,.854,.471);
  const arms=[-1,1].map(sign=>{
    const g=group(body,sign*.267,1.37,.007);
    oval(g,.152,.145,.135,navy,0,-.046,0);
    oval(g,.113,.064,.115,cream,0,-.154,.014);
    oval(g,.082,.156,.081,skin,0,-.264,.03);
    oval(g,.089,.088,.079,skin,0,-.4,.049);
    return g;
  });
  const tail=group(body,0,.80,-.24);
  line(tail,[[0,0,0],[.08,-.05,-.30],[.36,.015,-.60],[.66,.31,-.78]],.103,blue);
  const fluke=group(tail,.67,.31,-.8);
  for(const sign of [-1,1]){
    const part=oval(fluke,.245,.062,.112,sign>0?aqua:'#73b0cb',sign*.129,.019,-.049);
    part.rotation.y=sign*.47;part.rotation.z=sign*.42;
  }
  oval(head,.484,.51,.434,skin,0,0,.024);
  // Cap and long locks, leaving the face clear.
  mesh(head,new THREE.SphereGeometry(1,36,24,0,Math.PI*2,0,Math.PI*.414),navy).scale.set(.518,.55,.464);
  oval(head,.505,.62,.238,navy,0,-.05,-.263);
  for(const sign of [-1,1]){
    const locks=[
      [.41,-.21,-.074,.14,.47,.168,navy],
      [.465,-.40,-.032,.125,.415,.13,blue],
      [.495,-.65,-.035,.089,.30,.109,'#567fb6'],
      [.448,-.48,-.194,.105,.39,.14,'#2c4d80'],
      [.40,-.77,-.183,.087,.25,.099,aqua],
    ];
    for(const [x,y,z,w,h,d,color] of locks){
      const lock=oval(head,w,h,d,color,x*sign,y,z);lock.rotation.z=sign*.15;
    }
    const fin=oval(head,.239,.105,.096,'#6caed2',sign*.52,.024,-.02);fin.rotation.z=sign*.36;
    const stripe=oval(head,.19,.04,.064,aqua,sign*.56,.026,.021);stripe.rotation.z=sign*.36;
  }
  const fringe=[[-.308,.249,.322,.123,.237,-.61],[-.19,.291,.392,.134,.194,-.48],
    [-.035,.353,.412,.138,.19,-.64],[.104,.357,.387,.128,.145,.36],[.265,.296,.352,.152,.19,.62],
    [.387,.207,.294,.102,.221,.33]];
  for(const [x,y,z,w,h,angle] of fringe){
    const strand=oval(head,w,h,.099,x<.2?navy:'#304776',x,y,z);strand.rotation.z=angle;
  }
  const lace=[[-.414,.30,.16],[-.31,.43,.236],[-.155,.496,.263],[0,.515,.267],
              [.155,.496,.263],[.31,.43,.236],[.414,.30,.16]];
  line(head,lace,.043,cream);
  lace.forEach(([x,y,z],i)=>{
    const r=oval(head,.081,.065,.037,i%2?'#fff7f0':'#ffe0e8',x,y+.036,z);
    r.rotation.z=-x*1.4;
  });
  const eyes=[-1,1].map(sign=>{
    const g=group(head,sign*.189,-.061,.421);
    g.rotation.y=sign*.21;
    oval(g,.123,.145,.029,ink,0,0,0);
    oval(g,.108,.127,.028,'#fff5f2',0,-.008,.014);
    oval(g,.079,.115,.026,'#3b4e90',0,-.008,.036);
    oval(g,.062,.057,.017,'#69bdc8',0,-.054,.058);
    oval(g,.037,.073,.017,ink,0,.004,.059);
    oval(g,.027,.032,.009,'#ffffff',-.022,.049,.076);
    oval(g,.012,.016,.009,'#ffffff',.027,-.045,.078);
    oval(head,.089,.041,.015,rosy,sign*.302,-.219,.335).rotation.y=sign*.40;
    return g;
  });
  line(head,[[-.064,-.222,.417],[-.029,-.245,.425],[.013,-.247,.426],[.057,-.22,.419]],.011,'#aa6877');
  oval(head,.029,.024,.024,'#ffd3bf',0,-.126,.455);
  const book=group(body,0,1.11,.41);
  for(const sign of [-1,1]){
    const side=group(book,sign*.117,0,0);side.rotation.y=sign*-.24;side.rotation.x=-.61;
    block(side,.23,.28,.035,'#688a9e');
    block(side,.213,.265,.029,cream,0,.004,.023);
    for(let i=0;i<4;i++)block(side,.13,.007,.004,'#b5a7ad',0,.075-i*.037,.038,.002);
  }
  const shade=shadow(scene,0,0,1.52,1.15,.55);
  const goal=new THREE.Vector3(0,0,1.1);
  root.position.copy(goal);
  let pose='idle',blinkAt=2.3;
  return {root,poseAt(position,action){
    goal.set(position[0],position[1],position[2]);pose=action;
  },update(t,dt,reduce){
    const distance=root.position.distanceTo(goal);
    const walk=distance>.045 && !reduce;
    if(reduce)root.position.copy(goal);
    else root.position.lerp(goal,1-Math.exp(-dt*3.5));
    const asleep=pose==='sleep' && !walk;
    const reading=(pose==='read' || pose==='sit-read') && !walk;
    const sitting=(pose==='sit' || pose==='sit-read') && !walk;
    const turn=asleep?Math.PI*.04:sitting?.55:.14;
    root.rotation.y=THREE.MathUtils.lerp(root.rotation.y,turn,.11);
    body.rotation.z=THREE.MathUtils.lerp(body.rotation.z,asleep?Math.PI/2:0,.13);
    body.position.y=asleep?0:walk?Math.abs(Math.sin(t*9))*.055:reduce?0:Math.sin(t*2)*.013;
    head.rotation.x=reading?.17:0;
    head.rotation.y=reduce?0:Math.sin(t*.9)*.085;
    tail.rotation.y=reduce?0:Math.sin(t*2.1)*.19;
    for(let i=0;i<2;i++){
      const sign=i===0?-1:1;
      arms[i].rotation.z=sign*(reading?-.23:.14);
      arms[i].rotation.x=reading?-.80:walk?Math.sin(t*10+i*Math.PI)*.52:-.08;
    }
    leftLeg.rotation.x=sitting?-1.36:walk?Math.sin(t*10)*.43:0;
    rightLeg.rotation.x=sitting?-1.36:walk?-leftLeg.rotation.x:0;
    if(t>blinkAt+.18)blinkAt=t+3.8;
    const blink=asleep?.1:reduce||t<blinkAt?1:1-.92*Math.sin(Math.min(1,(t-blinkAt)/.18)*Math.PI);
    eyes.forEach(eye=>eye.scale.y=blink);
    book.visible=reading;
    shade.visible=root.visible&&!asleep;
    shade.position.x=root.position.x;shade.position.z=root.position.z;
  }};
}
