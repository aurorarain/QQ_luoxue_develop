import * as THREE from 'three';
import {block,cylinder,group,line,mesh,oval,texture,flat} from './shapes.js';

const brass='#c58e73',cream='#f3e4d9',ink='#68607c';

function mug(parent,x,y,z){
  const g=group(parent,x,y,z);
  cylinder(g,.071,.059,.13,'#d5b5c7',0,.065,0);
  cylinder(g,.058,.058,.006,'#7b5a53',0,.132,0);
  mesh(g,new THREE.TorusGeometry(.041,.01,8,20),'#d5b5c7',.074,.07,0);
}

function clock(scene){
  const g=group(scene,4.10,2.26,-3.54);
  oval(g,.267,.267,.025,brass);oval(g,.245,.245,.026,cream,0,0,.023);
  for(let i=0;i<12;i++){
    const a=i*Math.PI/6;
    const mark=block(g,.012,i%3===0?.039:.022,.006,ink,Math.sin(a)*.210,Math.cos(a)*.210,.051,.002);
    mark.rotation.z=-a;
  }
  const hour=group(g,0,0,.061),minute=group(g,0,0,.066);
  block(hour,.014,.115,.008,ink,0,.045,0,.003);
  block(minute,.009,.17,.008,ink,0,.071,0,.003);
  oval(g,.020,.020,.009,brass,0,0,.076);
  return ()=>{
    const d=new Date(),m=d.getUTCMinutes()+d.getUTCSeconds()/60,h=(d.getUTCHours()+8)%12+m/60;
    hour.rotation.z=-h*Math.PI/6;minute.rotation.z=-m*Math.PI/30;
  };
}

function interiorTrim(scene){
  block(scene,9.5,.022,.037,'#ecd9d3',0,2.99,-3.568,.008);
  for(const x of [-3.68,2.10,3.64]){
    for(const y of [.30,1.00])block(scene,1.07,.022,.017,'#e7d0d5',x,y,-3.587,.006);
    for(const side of [-1,1])block(scene,.022,.70,.017,'#e7d0d5',x+side*.535,.65,-3.587,.006);
  }
  for(const x of [-2.13,4.34]){
    block(scene,.127,.09,.025,'#eee0db',x,.22,-3.57,.016);
    for(const sign of [-1,1])block(scene,.008,.027,.005,'#ae97a8',x+sign*.022,.22,-3.553,.002);
  }
}

function throwBlanket(scene){
  const g=group(scene,-3.36,0,.88);g.rotation.y=.57;
  const geometry=new THREE.PlaneGeometry(.67,1.16,24,30),a=geometry.attributes.position;
  for(let i=0;i<a.count;i++){
    const u=a.getX(i),v=(a.getY(i)+.58)/1.16;
    a.setXYZ(i,.80+v*.63,.82-Math.max(0,v-.42)*.92+.015*Math.sin(u*40),u+.10);
  }
  geometry.computeVertexNormals();
  mesh(g,geometry,new THREE.MeshStandardMaterial({color:'#a0b6bd',roughness:.98,side:THREE.DoubleSide}));
  for(let i=0;i<13;i++){
    const z=-.20+i*.047;
    line(g,[[1.43,.286,z],[1.45,.25,z+.006],[1.43,.217,z+.007]],.005,'#c6d7d2');
  }
  for(const [x,y,z,angle,w,h] of [[-.71,.77,-.035,.27,.43,.36],[.62,.71,-.048,-.22,.38,.31]]){
    const cushion=group(g,x,y,z);cushion.rotation.z=angle;
    line(cushion,[[-w/2,-h/2,0],[w/2,-h/2,0],[w/2,h/2,0],[-w/2,h/2,0],[-w/2,-h/2,0]],.005,'#efdadc');
  }
}

function living(scene){
  throwBlanket(scene);
  cylinder(scene,.115,.115,.015,'#d9b9ad',-.34,.517,2.025);
  line(scene,[[-.16,.518,2.12],[-.13,.523,1.99]],.007,brass);
  oval(scene,.019,.004,.027,brass,-.132,.525,1.99);
  const photo=group(scene,1.82,.54,-2.60);photo.rotation.x=-.12;
  block(photo,.25,.31,.029,brass,0,.155,0,.023);
  block(photo,.207,.26,.008,'#c7adc6',0,.155,.021,.010);
  oval(photo,.059,.085,.005,'#e8d9d1',0,.16,.029);
  const candle=group(scene,2.09,.54,-2.60);
  cylinder(candle,.062,.062,.105,'#f0dac4',0,.052,0);
  line(candle,[[0,.104,0],[0,.119,0]],.003,ink);
}

function bedroom(scene){
  for(const x of [-2.26,-1.92]){
    const slipper=group(scene,x,.03,-.19);slipper.rotation.y=-.15;
    oval(slipper,.115,.035,.218,'#b79abe');oval(slipper,.12,.07,.131,'#dbbccc',0,.034,-.07);
    line(slipper,[[-.09,.06,-.01],[0,.09,.013],[.09,.06,-.01]],.005,cream);
  }
  block(scene,.40,.055,.28,'#819ca6',1.04,.636,1.39,.020);
  block(scene,.35,.025,.25,'#f5e5d9',1.04,.676,1.39,.010);
  const alarm=group(scene,-4.20,.56,-2.53);
  oval(alarm,.105,.094,.038,'#c39b9c',0,.085,0);
  oval(alarm,.086,.077,.009,cream,0,.085,.035);
  line(alarm,[[0,.128,.047],[0,.085,.047],[.04,.07,.047]],.005,ink);
}

function study(scene){
  line(scene,[[1.83,.969,-.72],[1.99,.969,-.50]],.009,'#8c819c');
  cylinder(scene,.038,.038,.074,ink,2.10,.989,-.79);
  for(let i=0;i<3;i++)block(scene,.18,.005,.16,['#e8d6a5','#d7c7d9','#b8d0c7'][i],.73+i*.22,.954,-.31,.006);
  mug(scene,2.09,.949,-.40);
}

function gaming(scene){
  const stand=group(scene,.22,1.008,-2.76);
  block(stand,.23,.026,.18,'#66607d',0,.013,0,.016);
  cylinder(stand,.015,.019,.32,brass,0,.18,0);
  line(stand,[[-.126,.25,0],[-.14,.38,0],[0,.446,0],[.14,.38,0],[.126,.25,0]],.025,'#d1b2cb');
  for(const x of [-.126,.126])oval(stand,.042,.077,.054,'#9087ad',x,.257,0);
  line(scene,[[.22,1.06,-2.74],[.20,1.02,-2.49],[.39,1.02,-2.45],[.44,.92,-2.61]],.006,'#786884');
  const pad=block(scene,1.02,.009,.40,'#615d7f',.95,1.000,-2.45,.004);
  line(scene,[[.45,1.007,-2.26],[1.43,1.007,-2.26]],.007,'#bda2d1');
}

function kitchen(scene){
  for(let row=0;row<4;row++)for(let col=0;col<7;col++){
    block(scene,.393,.14,.018,(row+col)%3?'#e4d9cc':'#d4c6c6',1.65+col*.4,1.15+row*.147,-3.568,.011);
  }
  const shelf=group(scene,3.08,1.92,-3.36);
  block(shelf,1.85,.065,.33,'#bd8e77');
  for(const x of [-.65,.65])line(shelf,[[x,-.32,-.14],[x,-.03,.10],[x,-.03,-.14]],.012,brass);
  for(let i=0;i<4;i++){
    const x=-.60+i*.38;
    cylinder(shelf,.077,.077,.19,['#c8b6aa','#b4c4b0','#d8bf9a','#bda8ba'][i],x,.129,0);
    cylinder(shelf,.084,.084,.025,cream,x,.238,0);
    block(shelf,.075,.055,.006,'#f1e5d7',x,.135,.078,.006);
  }
  block(scene,.61,.36,.028,'#665d74',2.24,.45,-2.165,.028);
  block(scene,.50,.25,.008,'#37374a',2.24,.455,-2.144,.015);
  block(scene,.34,.019,.035,brass,2.24,.68,-2.12,.008);
  for(const x of [-.97,-.66]){
    cylinder(scene,.08,.08,.14,'#e2c8b5',x,.942,1.26);
    line(scene,[[x-.03,1.09,1.25],[x+.03,1.09,1.25]],.004,ink);
  }
}

function garden(scene){
  const points=[];
  for(let i=0;i<=16;i++)points.push([1.21+i*1.64/16,1.79-.19*Math.sin(i*Math.PI/16),-2.20]);
  line(scene,points,.009,'#746678');
  const bulbs=[];
  for(let i=1;i<8;i++){
    const x=1.21+i*1.64/8,y=1.79-.19*Math.sin(i*Math.PI/8);
    line(scene,[[x,y,-2.20],[x,y-.04,-2.20]],.006,'#746678');
    const material=new THREE.MeshStandardMaterial({color:'#f5d6ad',emissive:'#efb67a',emissiveIntensity:.15,roughness:.40});
    oval(scene,.035,.049,.035,material,x,y-.079,-2.20);bulbs.push(material);
  }
  for(const [x,z] of [[-2.86,-.98],[3.30,2.5],[-3.0,2.76]])for(let i=0;i<4;i++){
    const blossom=group(scene,x+i*.16,.39+(i%2)*.08,z);
    for(let j=0;j<5;j++){
      const a=j*Math.PI*2/5;
      oval(blossom,.029,.012,.042,i%2?'#e7bacb':'#efe0b6',Math.cos(a)*.031,.005,Math.sin(a)*.031);
    }
    oval(blossom,.018,.014,.018,'#d3b276',0,.014,0);
  }
  return on=>bulbs.forEach(material=>{material.emissiveIntensity=on?1.35:.12;});
}

export function refineRoom(scene,kind){
  if(kind==='garden')return {animate:()=>{},setWarm:garden(scene)};
  interiorTrim(scene);
  const animate=clock(scene);
  ({living,bedroom,study,gaming,kitchen}[kind]||(()=>{}))(scene);
  return {animate,setWarm:()=>{}};
}
