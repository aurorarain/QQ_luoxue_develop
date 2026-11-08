import * as THREE from 'three';
import {block,cylinder,flat,group,line,mesh,oval,palette as p,shadow,texture} from './shapes.js';

const brass='#c58e73', porcelain='#ffeadb', wall='#c7b6cd';
const glow=color=>new THREE.MeshBasicMaterial({color});

function floor(scene){
  block(scene,9.84,.43,7.51,p.walnut,0,-.28,0,.16);
  const wood=texture(1024,768,(c,w,h)=>{
    const shades=['#c59980','#cb9e85','#b98e79','#d2a58b','#d6ab8f','#c69c82'];
    for(let row=0;row<15;row++){
      const y=row*h/15;
      for(let col=-1;col<6;col++){
        const x=(col+(row%2)*.5)*w/5;
        c.fillStyle=shades[(row*11+col+18)%6];c.fillRect(x,y,w/5,h/15-1);
        c.strokeStyle='#9a6d64';c.strokeRect(x,y,w/5,h/15);
        c.fillStyle='#f3d1ad55';
        for(let i=1;i<7;i++)c.fillRect(x+8+i*3,y+i*6,30+(row*i*13)%132,1);
      }
    }
  });
  const boards=mesh(scene,new THREE.PlaneGeometry(9.72,7.39),new THREE.MeshStandardMaterial({map:wood,roughness:.9}),0,-.018,0);
  boards.rotation.x=-Math.PI/2;
  const rug=texture(512,512,(c)=>{
    c.translate(256,256);
    for(const [r,color] of [[245,'#7d6588'],[235,'#c698bc'],[220,'#ebc9ca'],[210,'#b38daf'],[199,'#ae89ad']]){
      c.fillStyle=color;c.beginPath();c.arc(0,0,r,0,Math.PI*2);c.fill();
    }
    c.strokeStyle='#ebc9ca99';c.lineWidth=2;
    for(let i=0;i<60;i++){
      c.rotate(Math.PI/30);c.beginPath();c.ellipse(0,182,5,11,.3,0,Math.PI*2);c.stroke();
    }
    c.strokeStyle='#f2d2db4c';
    for(let i=-150;i<=150;i+=13){
      c.beginPath();c.moveTo(-100,i);c.quadraticCurveTo(0,i-34,100,i);c.stroke();
    }
  });
  const carpet=flat(scene,5.18,3.95,rug,.53,.002,1.13);carpet.rotation.x=-Math.PI/2;
}

function windowScene(time){
  return texture(512,376,(c,w,h)=>{
    const g=c.createLinearGradient(0,0,0,h);
    const warm=time==='warm';
    g.addColorStop(0,warm?'#252c57':'#6d89c0');
    g.addColorStop(.7,warm?'#9d759f':'#e9acb6');g.addColorStop(1,warm?'#f5a596':'#ffd3ad');
    c.fillStyle=g;c.fillRect(0,0,w,h);
    c.fillStyle=warm?'#ffe0bd':'#ffe2ad';c.beginPath();c.arc(341,warm?89:126,42,0,Math.PI*2);c.fill();
    c.fillStyle='#fff1deaa';
    for(let i=0;i<35;i++){
      const x=(i*139+46)%w,y=(i*73+12)%180;
      if(warm)c.fillRect(x,y,i%9===0?3:1.5,i%9===0?3:1.5);
      else if(i%6===0){c.beginPath();c.ellipse(x,y,42,5,-.04,0,Math.PI*2);c.fill();}
    }
    for(const [base,color,shift] of [[245,'#696989',.2],[287,'#454e71',1.3],[329,'#344662',2.5]]){
      c.fillStyle=color;c.beginPath();c.moveTo(0,h);
      for(let x=0;x<=w;x+=8)c.lineTo(x,base+24*Math.sin(x/64+shift)+14*Math.sin(x/29+shift));
      c.lineTo(w,h);c.closePath();c.fill();
    }
    c.fillStyle='#fbd4bdc0';for(let i=0;i<20;i++)c.fillRect(12+i*28,315+Math.sin(i*4)*12,3,5);
  });
}

function picture(scene,x,y,w,h,kind){
  block(scene,w+.14,h+.14,.073,brass,x,y,-3.50,.025);
  const art=texture(196,156,(c,a,b)=>{
    c.fillStyle=kind===0?'#506586':'#e1b4ba';c.fillRect(0,0,a,b);
    c.fillStyle=kind===0?'#ffe8d5':'#fbdbc4';c.beginPath();c.arc(137,55,29,0,Math.PI*2);c.fill();
    c.fillStyle=kind===0?'#a6d4d3':'#985f81';c.beginPath();
    c.ellipse(87,98,52,23,-.22,0,Math.PI*2);c.moveTo(129,89);c.quadraticCurveTo(152,57,170,77);
    c.quadraticCurveTo(160,101,132,104);c.fill();
    c.fillStyle='#fef4e9';c.beginPath();c.arc(59,99,3,0,Math.PI*2);c.fill();
    for(let i=0;i<10;i++)c.fillRect(9+(i*37)%178,14+(i*23)%67,2,2);
  });
  flat(scene,w,h,art,x,y,-3.452);
}

function plant(parent,x,y,z,scale=1){
  const g=group(parent,x,y,z);g.scale.setScalar(scale);
  cylinder(g,.21,.15,.29,'#c68184',0,.145,0);
  cylinder(g,.177,.177,.018,'#685268',0,.293,0);
  for(let i=0;i<7;i++){
    const a=i*2.399,h=.48+(i%3)*.12,x=Math.cos(a)*.20,z=Math.sin(a)*.20;
    line(g,[[0,.29,0],[x*.3,.42,z*.3],[x,h,z]],.012,'#758d83');
    const leaf=oval(g,.104,.22,.038,['#729c8f','#8eb5a3','#9bb79e'][i%3],x,h,z);
    leaf.rotation.set(Math.sin(a)*.7,0,-Math.cos(a)*.7);
  }
}

function lamp(parent,x,y,z,large=false){
  const g=group(parent,x,y,z);
  const height=large?1.64:.51, r=large?.28:.14;
  cylinder(g,r*.62,r*.68,.065,brass,0,.034,0);
  cylinder(g,.021,.024,height,brass,0,height/2,0);
  const shade=new THREE.MeshStandardMaterial({color:'#ffe0bc',emissive:'#ffbf85',emissiveIntensity:.33,roughness:.72});
  cylinder(g,r*.67,r,.35,shade,0,height,0);
  cylinder(g,r*.91,r*.91,.014,glow('#ffe2ac'),0,height-.173,0);
  const light=new THREE.PointLight('#ffc28c',large?4.6:2.4,large?4.1:2.5,2);
  light.position.y=height-.11;g.add(light);return {shade,light};
}

function shelving(scene){
  shadow(scene,4.12,-2.52,2.25,1.52);
  const unit=group(scene,3.98,0,-2.84);
  block(unit,1.33,2.42,.14,p.walnut,0,1.22,-.24);
  for(const x of [-.65,.65])block(unit,.095,2.46,.63,p.oak,x,1.25,0);
  for(let row=0;row<5;row++){
    const y=.10+row*.59;
    block(unit,1.38,.095,.65,p.oak,0,y,0);
    if(row===4)continue;
    for(let i=0;i<7;i++){
      if(row===1 && i>3)continue;
      const colors=['#bb8187','#8a99ba','#eee0c4','#668c9f','#9f8fb4','#d7a488'];
      const height=.29+(i*11+row*5)%19/100, x=-.47+i*.143;
      const book=group(unit,x,y+.06,-.005);
      book.rotation.z=i===6?-.13:0;
      block(book,.105,height,.33,colors[(i+row)%colors.length],0,height/2,0,.016);
      block(book,.076,.014,.013,p.cream,0,height*.75,.171,.003);
    }
  }
  plant(unit,.37,.77,.06,.52);
}

function bed(scene){
  const g=group(scene,-2.93,0,-2.13);
  shadow(scene,-2.93,-2.05,3.55,3.3);
  block(g,2.22,.28,2.71,p.walnut,0,.24,0,.08);
  for(const x of [-.9,.9])for(const z of [-1.05,1.05])cylinder(g,.06,.051,.18,brass,x,.09,z);
  block(g,2.24,.91,.17,p.plum,0,.68,-1.32,.11);
  block(g,2.06,.21,2.48,p.ivory,0,.484,-.022,.10);
  block(g,2.045,.153,1.61,p.lilac,0,.626,.38,.088);
  block(g,2.067,.102,.27,'#dbbdd5',0,.696,-.40,.055);
  block(g,2.04,.083,.23,'#99789f',0,.706,.91,.04);
  for(const x of [-.49,.49]){
    const cushion=block(g,.82,.20,.48,x<0?p.ivory:'#edd4e2',x,.666,-.87,.095);cushion.rotation.y=x*.14;
  }
  for(let i=0;i<6;i++)block(g,1.86,.012,.014,'#c9acd0',0,.709,-.23+i*.225,.004);
  const stand=group(scene,-4.27,0,-2.79);
  block(stand,.55,.49,.60,p.oak,0,.26,0,.08);
  block(stand,.51,.023,.54,p.cream,0,.518,0,.016);
  block(stand,.12,.029,.041,brass,0,.3,.312,.007);
  return lamp(stand,0,.53,0);
}

function sofa(scene){
  const g=group(scene,-3.36,0,.88);
  g.rotation.y=.57;
  shadow(scene,-3.38,.94,3.25,2.36);
  block(g,2.62,.34,1.13,p.plum,0,.27,0,.105);
  block(g,2.50,.70,.31,p.mauve,0,.67,-.45,.12);
  for(const x of [-.57,.57]){
    block(g,1.12,.216,.87,'#c6a7c6',x,.50,.02,.103);
    block(g,.72,.42,.225,'#b48fb9',x,.81,-.29,.10).rotation.x=-.22;
  }
  for(const x of [-1.20,1.20])block(g,.26,.48,1.06,p.mauve,x,.55,.04,.103);
  const pillow=block(g,.49,.43,.21,'#eac0c1',-.71,.77,-.15,.085);pillow.rotation.z=.27;
  block(g,.44,.38,.22,p.cream,.62,.71,-.17,.09).rotation.z=-.22;
  block(g,.49,.071,.77,'#93afbc',1.10,.49,.27,.029);
  return lamp(scene,-4.32,0,-.27,true);
}

function desk(scene){
  const g=group(scene,2.30,0,-2.70);
  shadow(scene,2.3,-2.60,3.5,2.22);
  for(const x of [-1.12,1.12]){
    block(g,.095,.87,.77,p.walnut,x,.44,0,.035);
    block(g,.32,.055,.73,brass,x,.062,0,.025);
  }
  block(g,2.58,.113,.99,p.oak,0,.93,0,.063);
  block(g,.74,.13,.58,p.walnut,.78,.81,.12,.03);
  for(let i=0;i<2;i++){
    const monitor=group(g,-.61+i*1.04,.99,-.30);monitor.rotation.y=i===0?.10:-.14;
    block(monitor,.48,.042,.29,p.walnut,0,.026,.073,.035);
    block(monitor,.077,.31,.07,brass,0,.168,0);
    block(monitor,1.03,.59,.096,p.navy,0,.50,0,.048);
    const map=texture(264,144,(c,w,h)=>{
      const bg=c.createLinearGradient(0,0,w,h);bg.addColorStop(0,'#302a62');bg.addColorStop(1,'#527b97');c.fillStyle=bg;c.fillRect(0,0,w,h);
      c.strokeStyle='#c5c6ee99';c.lineWidth=2;
      for(let line=0;line<4;line++){c.beginPath();for(let x=0;x<w;x+=5)c.lineTo(x,66+line*12+Math.sin(x/24+line)*11);c.stroke();}
      c.fillStyle='#eee4e4';for(let n=0;n<20;n++)c.fillRect((n*41)%w,(n*77)%h,2,2);
    });
    flat(monitor,.951,.51,map,0,.50,.052);
  }
  block(g,.87,.037,.23,'#e6c4d3',-.16,1.016,.246,.018);
  for(let i=0;i<8;i++)block(g,.063,.009,.057,'#fff0e8',-.49+i*.094,1.039,.246,.004);
  oval(g,.072,.027,.11,p.navy,.45,1.016,.26);
  plant(g,1.00,1.008,-.25,.60);
  const mug=cylinder(g,.074,.06,.132,p.cream,.77,1.057,.27);
  mesh(g,new THREE.TorusGeometry(.047,.012,8,18),p.cream,.844,1.057,.27);
  const chair=group(scene,2.22,0,-1.57);
  chair.rotation.y=-.29;
  cylinder(chair,.075,.105,.54,p.walnut,0,.29,0);
  cylinder(chair,.27,.29,.065,brass,0,.042,0);
  block(chair,.69,.18,.63,'#9d80a7',0,.57,0,.10);
  block(chair,.69,.66,.19,p.mauve,0,.87,.27,.09).rotation.x=.09;
  return lamp(g,-1.01,1.01,.10);
}

function accessories(scene){
  const table=group(scene,-.64,0,1.98);shadow(scene,-.64,1.98,1.83,1.52);
  for(const [x,z] of [[-.47,.22],[.47,.22],[0,-.27]])cylinder(table,.043,.034,.43,p.walnut,x,.22,z);
  block(table,1.28,.1,.72,p.oak,0,.46,0,.11);
  block(table,.36,.055,.28,'#779ba8',-.26,.543,-.025,.022).rotation.y=.28;
  cylinder(table,.081,.064,.13,porcelain,.30,.574,.045);
  const cupTop=cylinder(table,.058,.058,.006,'#966971',.30,.638,.045);
  cupTop.material=glow('#a57273');
  const cat=group(scene,-1.62,0,2.77);cat.rotation.y=-.23;
  oval(cat,.36,.152,.228,'#847e98',0,.16,0);
  oval(cat,.23,.20,.183,'#9e95aa',.264,.23,.054);
  for(const x of [.12,.37]){
    const ear=mesh(cat,new THREE.ConeGeometry(.094,.19,4),'#9e95aa',x,.40,.063);ear.rotation.y=.78;
  }
  line(cat,[[-.27,.13,.0],[-.51,.14,-.02],[-.55,.21,.23],[-.38,.15,.31]],.052,'#a39aad');
  for(const x of [.19,.34])line(cat,[[x-.034,.241,.221],[x,.224,.233],[x+.036,.244,.224]],.011,p.walnut);
  plant(scene,4.18,0,.12,1.39);
  const tank=group(scene,3.78,0,1.34);
  shadow(scene,3.78,1.34,1.9,1.5);
  block(tank,1.36,.62,.72,p.walnut,0,.32,0,.075);
  block(tank,1.45,.061,.81,brass,0,.65,0,.042);
  block(tank,1.31,.54,.67,new THREE.MeshStandardMaterial({color:'#a5d5de',transparent:true,opacity:.38,roughness:.25,depthWrite:false}),0,.955,0,.041);
  block(tank,1.30,.08,.64,'#90b6c0',0,.729,0,.044);
  for(let i=0;i<5;i++)oval(tank,.095,.06,.083,'#cabac4',-.46+i*.23,.78,(i%2)*.15-.10);
  for(const x of [-.50,.47])plant(tank,x,.754,-.17,.36);
  const fish=[0,1].map(i=>{
    const g=group(tank,0,1.02-i*.13,.02+i*.16);
    oval(g,.11,.055,.049,i===0?'#f3ac97':'#f2d3a7');
    const tail=oval(g,.062,.038,.021,'#e7b4a8',-.113,0,0);tail.rotation.z=.24;
    oval(g,.012,.012,.009,p.navy,.045,.012,.042);return g;
  });
  return t=>fish.forEach((f,i)=>{f.position.x=Math.sin(t*(.55+i*.13)+i*2)*.37;f.rotation.y=Math.cos(t*(.55+i*.13)+i*2)>0?0:Math.PI;});
}

export function furnish(scene){
  floor(scene);
  block(scene,9.70,3.13,.16,wall,0,1.55,-3.69,.04);
  block(scene,.16,3.13,7.44,'#b9a5c6',-4.79,1.55,.0,.04);
  block(scene,9.72,.13,.069,p.ivory,0,.08,-3.565,.018);
  block(scene,.061,.12,7.43,p.ivory,-4.67,.09,0,.018);
  block(scene,9.76,.105,.24,p.cream,0,3.123,-3.68,.042);
  block(scene,.24,.105,7.44,p.cream,-4.79,3.123,0,.04);
  for(let i=0;i<9;i++){
    block(scene,.035,1.13,.042,'#a894b8',-4.684,.72,-3.0+i*.78,.009);
  }
  block(scene,.042,.048,7.24,'#d8c3d4',-4.677,1.30,.03,.009);
  const windowX=-.16,windowY=2.04;
  block(scene,2.93,1.89,.074,p.walnut,windowX,windowY,-3.545,.04);
  const day=windowScene('day'),warm=windowScene('warm');
  const view=flat(scene,2.72,1.65,day,windowX,windowY,-3.493);
  block(scene,.047,1.69,.06,p.cream,windowX,windowY,-3.447,.012);
  block(scene,2.76,.046,.06,p.cream,windowX,windowY-.07,-3.446,.013);
  block(scene,3.0,.096,.29,p.cream,windowX,1.154,-3.414,.028);
  line(scene,[[-1.96,3.01,-3.34],[1.59,3.01,-3.34]],.028,brass);
  for(const sign of [-1,1]){
    const side=windowX+sign*1.48;
    for(let i=0;i<6;i++){
      const width=.075+(i%2)*.014;
      const curtain=block(scene,width,1.72,.145,i%2?'#a783b7':'#c3a0cf',side+sign*(i-2)*.078,2.077,-3.32+(i%2)*.032,.035);
      curtain.rotation.z=sign*(i-2)*.023;
    }
    block(scene,.44,.07,.174,brass,side+sign*.049,1.64,-3.295,.019);
  }
  picture(scene,-3.34,2.15,.93,.75,0);
  picture(scene,2.73,2.30,.67,.55,1);
  const shelf=group(scene,-4.59,1.93,-1.46);shelf.rotation.y=Math.PI/2;
  block(shelf,1.60,.11,.33,p.oak);
  plant(shelf,-.52,.05,.012,.52);
  for(let i=0;i<5;i++)block(shelf,.113,.33+i*.025,.24,i%2?p.lilac:p.cream,-.15+i*.145,.23+i*.012,.01,.017);
  const lamps=[bed(scene),sofa(scene),desk(scene)];
  shelving(scene);
  const animate=accessories(scene);
  return {animate,setWarm(on){
    view.material.map=on?warm:day;view.material.needsUpdate=true;
    for(const {shade,light} of lamps){shade.emissiveIntensity=on?.9:.28;light.intensity=(on?1.4:.45)*(light.distance);}
  }};
}
