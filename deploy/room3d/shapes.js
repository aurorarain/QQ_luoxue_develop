import * as THREE from 'three';

export const palette = {
  navy:'#253554', teal:'#81bec0', plum:'#795b85', lilac:'#b697c7', mauve:'#c9a7bf',
  cream:'#f9e3cc', ivory:'#fff4e6', oak:'#bd8e77', walnut:'#6d505b', peach:'#de9e90',
};
const materials=new Map(), boxes=new Map(), sphere=new THREE.SphereGeometry(1,24,16);
const fabrics=new Set([palette.plum,palette.lilac,palette.mauve,'#c6a7c6','#b48fb9','#9d80a7','#c3a7ca','#aa8ab7']);
let woodGrain,fabricWeave;
function surfaceMap(wood){
  if(wood&&woodGrain)return woodGrain;
  if(!wood&&fabricWeave)return fabricWeave;
  const map=texture(256,256,(c,w,h)=>{
    c.fillStyle='#f4f4f4';c.fillRect(0,0,w,h);
    if(wood){
      for(let i=0;i<70;i++){
        c.strokeStyle=i%3?'#79797915':'#ffffff55';c.lineWidth=i%4===0?1.2:.5;
        c.beginPath();for(let x=0;x<=w;x+=8)c.lineTo(x,i*4+Math.sin(x/47+i*.8)*2.5);c.stroke();
      }
    }else{
      for(let i=0;i<w;i+=4){
        c.fillStyle=i%8?'#cecece70':'#ffffff88';c.fillRect(i,0,1,h);c.fillRect(0,i,w,1);
      }
    }
  });
  map.wrapS=map.wrapT=THREE.RepeatWrapping;map.repeat.set(2,2);
  if(wood)woodGrain=map;else fabricWeave=map;
  return map;
}
export function material(color){
  if(!materials.has(color)){
    const wood=color===palette.oak||color===palette.walnut,fabric=fabrics.has(color);
    const metallic=color==='#c58e73';
    const options={color,roughness:fabric?.94:wood?.68:metallic?.36:.76,metalness:metallic?.24:0};
    if(wood||fabric){options.map=options.bumpMap=surfaceMap(wood);options.bumpScale=wood?.008:.004;}
    materials.set(color,new THREE.MeshStandardMaterial(options));
  }
  return materials.get(color);
}
export function mesh(parent,geometry,color,x=0,y=0,z=0){
  const item=new THREE.Mesh(geometry,typeof color==='string'?material(color):color);
  item.position.set(x,y,z);parent.add(item);return item;
}
export function block(parent,w,h,d,color,x=0,y=0,z=0,round=.055){
  const r=Math.min(round,w*.22,h*.22,d*.22);
  const key=[w,h,d,r].join(',');
  if(!boxes.has(key)){
    const outline=new THREE.Shape();
    const a=w/2-r,b=h/2-r;
    outline.moveTo(-a,-b);outline.lineTo(a,-b);outline.lineTo(a,b);outline.lineTo(-a,b);outline.closePath();
    const geo=new THREE.ExtrudeGeometry(outline,{depth:d-2*r,steps:1,bevelEnabled:true,bevelThickness:r,bevelSize:r,bevelSegments:3});
    geo.translate(0,0,-d/2+r);
    boxes.set(key,geo);
  }
  return mesh(parent,boxes.get(key),color,x,y,z);
}
export function oval(parent,w,h,d,color,x=0,y=0,z=0){
  const item=mesh(parent,sphere,color,x,y,z);item.scale.set(w,h,d);return item;
}
export function cylinder(parent,top,bottom,height,color,x=0,y=0,z=0){
  return mesh(parent,new THREE.CylinderGeometry(top,bottom,height,20),color,x,y,z);
}
export function group(parent,x=0,y=0,z=0){
  const g=new THREE.Group();g.position.set(x,y,z);parent.add(g);return g;
}
export function line(parent,points,width,color){
  const path=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));
  return mesh(parent,new THREE.TubeGeometry(path,Math.max(9,points.length*5),width,7,false),color);
}
export function texture(w,h,draw){
  const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
  draw(canvas.getContext('2d'),w,h);
  const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;
  tex.anisotropy=4;return tex;
}
export function flat(parent,w,h,map,x,y,z){
  return mesh(parent,new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({map,transparent:true}),x,y,z);
}
export function shadow(parent,x,z,w,d,opacity=.48){
  const tex=texture(64,64,(c)=>{
    const g=c.createRadialGradient(32,32,1,32,32,32);
    g.addColorStop(0,'#382331');g.addColorStop(1,'#38233100');c.fillStyle=g;c.fillRect(0,0,64,64);
  });
  const shade=flat(parent,w,d,tex,x,.009,z);shade.material.opacity=opacity;shade.material.depthWrite=false;
  shade.rotation.x=-Math.PI/2;return shade;
}
