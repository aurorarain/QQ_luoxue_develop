import * as THREE from 'three';
import {group,line,mesh,texture} from './shapes.js';

const smooth=(a,b,x)=>THREE.MathUtils.smoothstep(x,a,b);

function cotton(){
  return texture(768,768,(c,w,h)=>{
    c.fillStyle='#bba2cc';c.fillRect(0,0,w,h);
    for(let y=0;y<h;y+=3){
      c.strokeStyle=y%6?'#e8d4ef38':'#735d8a24';
      c.beginPath();c.moveTo(0,y);c.lineTo(w,y);c.stroke();
    }
    for(let x=0;x<w;x+=4){
      c.strokeStyle='#f7e4f31b';c.beginPath();c.moveTo(x,0);c.lineTo(x,h);c.stroke();
    }
    c.setLineDash([2,3]);c.lineWidth=1.1;c.strokeStyle='#f5e1e7a0';
    for(let k=-7;k<14;k++)for(const sign of [-1,1]){
      c.beginPath();c.moveTo(k*128,0);c.lineTo(k*128+sign*h,h);c.stroke();
    }
    c.setLineDash([]);
  });
}

function quiltPoint(u,v,occupied){
  const x=(u-.5)*2.42,z=-.49+v*2.05;
  const body=Math.exp(-Math.pow((x+.49)/.39,2));
  const loft=occupied?body*(.22+.12*Math.exp(-Math.pow((v-.22)/.19,2)))*(1-smooth(.78,.98,v)):0;
  const edge=Math.max(smooth(.99,1.21,Math.abs(x))*.32,smooth(1.26,1.56,z)*.30);
  const folds=(.012*Math.sin(u*29+v*8)+.009*Math.sin(u*13-v*19))*Math.sin(Math.PI*u);
  return [x,.79+.026*Math.sin(Math.PI*u)*Math.sin(Math.PI*v)+loft+folds-edge,z];
}

function clothGeometry(occupied,fold=false){
  const columns=64,rows=fold?8:52,positions=[],uv=[],indices=[];
  for(let j=0;j<=rows;j++)for(let i=0;i<=columns;i++){
    const u=i/columns,v=j/rows*(fold?.095:1);
    const point=quiltPoint(u,v,occupied);
    if(fold)point[1]+=.015+.022*Math.sin(Math.PI*j/rows);
    positions.push(...point);uv.push(u,v);
  }
  for(let j=0;j<rows;j++)for(let i=0;i<columns;i++){
    const a=j*(columns+1)+i,b=a+columns+1;
    indices.push(a,b,a+1,b,b+1,a+1);
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  geometry.setIndex(indices);geometry.computeVertexNormals();
  return geometry;
}

function pillow(parent,x,color){
  const root=group(parent,x,.666,-.87);root.rotation.y=x*.14;
  const geometry=new THREE.SphereGeometry(1,40,24),positions=geometry.attributes.position;
  for(let i=0;i<positions.count;i++){
    const shape=(value,power)=>Math.sign(value)*Math.pow(Math.abs(value),power);
    positions.setXYZ(i,shape(positions.getX(i),.48)*.423,
      shape(positions.getY(i),.72)*.108,shape(positions.getZ(i),.48)*.251);
  }
  geometry.computeVertexNormals();
  mesh(root,geometry,new THREE.MeshStandardMaterial({color,roughness:.96}));
  const seam=[];
  for(let i=0;i<=64;i++){
    const angle=i*Math.PI/32;
    seam.push([Math.sign(Math.cos(angle))*Math.pow(Math.abs(Math.cos(angle)),.48)*.424,
      0,Math.sign(Math.sin(angle))*Math.pow(Math.abs(Math.sin(angle)),.48)*.252]);
  }
  line(root,seam,.006,'#f8e9e3');
  return root;
}

export function makeBedding(parent){
  const pillows=[pillow(parent,-.49,'#f4e7e4'),pillow(parent,.49,'#e7d5e4')];
  const fabric=cotton();
  const material=new THREE.MeshStandardMaterial({map:fabric,roughness:.95,side:THREE.DoubleSide});
  const lining=new THREE.MeshStandardMaterial({color:'#ebd4dc',roughness:.97,side:THREE.DoubleSide});
  const variants=[false,true].map(occupied=>{
    const root=group(parent);root.visible=!occupied;
    root.name=occupied?'duvet-resting':'duvet-made';
    mesh(root,clothGeometry(occupied),material);
    mesh(root,clothGeometry(occupied,true),lining);
    for(const edge of [0,1,2,3]){
      const points=[];
      for(let i=0;i<=64;i++){
        const t=i/64;
        const point=quiltPoint(edge===0?0:edge===1?1:t,edge===2?0:edge===3?1:t,occupied);
        point[1]+=.006;points.push(point);
      }
      line(root,points,.008,'#eed8e5');
    }
    return root;
  });
  // Both meshes have matching topology, including the piping: morph the whole bedding instead of swapping it.
  const morphs=[];
  variants[1].visible=false;
  variants[0].children.forEach((item,index)=>{
    const target=variants[1].children[index].geometry;
    item.geometry.morphAttributes.position=[target.attributes.position];
    if(target.attributes.normal)item.geometry.morphAttributes.normal=[target.attributes.normal];
    item.updateMorphTargets();morphs.push(item);
  });
  let resting=0;
  return {
    setResting(value){
      resting=THREE.MathUtils.clamp(Number(value),0,1);
      variants[0].visible=true;
      for(const item of morphs)item.morphTargetInfluences[0]=resting;
      pillows[0].scale.y=1-resting*.1;
    },
    animate(t){variants[0].position.y=Math.sin(t*1.55)*.003*resting;},
  };
}
