import * as THREE from 'three';
import {DOOR_OPENING,GATE_CENTER} from './doors.js';
import {block,cylinder,flat,group,line,mesh,oval,palette as p,shadow,texture} from './shapes.js';

const brass='#c58e73', porcelain='#ffeadb', wall='#c7b6cd';
const glow=color=>new THREE.MeshBasicMaterial({color});

function floor(scene, rugVisible=true, theme="oak"){
  block(scene,9.84,.43,7.51,p.walnut,0,-.28,0,.16);
  const wood=texture(1024,768,(c,w,h)=>{
    const shades=theme==='stone'
      ? ['#bfbac0','#d7d1ce','#b4acb4','#c8c0bf','#ded5ce','#c8bdc0']
      : ['#c59980','#cb9e85','#b98e79','#d2a58b','#d6ab8f','#c69c82'];
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
  if(!rugVisible)return;
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

function desk(scene,gaming=false){
  const g=group(scene,gaming?1.1:2.30,0,-2.70);
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
      const bg=c.createLinearGradient(0,0,w,h);bg.addColorStop(0,gaming?'#3e2675':'#302a62');bg.addColorStop(1,gaming?'#349b9c':'#527b97');c.fillStyle=bg;c.fillRect(0,0,w,h);
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
  cylinder(g,.074,.06,.132,p.cream,.77,1.057,.27);
  mesh(g,new THREE.TorusGeometry(.047,.012,8,18),p.cream,.844,1.057,.27);
  const chair=group(scene,gaming?.9:2.22,0,-1.57);
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

export function furnish(scene, kind='living'){
  if(kind==='garden')return garden(scene);
  floor(scene,kind!=='kitchen'&&kind!=='gaming',kind==='kitchen'?'stone':'oak');
  const colors={bedroom:'#d4b9ca',study:'#bdc9ca',gaming:'#9a91b7',kitchen:'#ead5c9',living:wall};
  const roomWall=colors[kind];
  block(scene,9.70,3.13,.16,roomWall,0,1.55,-3.69,.04);
  const {wallX,center,width,height}=DOOR_OPENING;
  const start=center-width/2,end=center+width/2;
  const leftSegments=[[-3.72,start],[end,3.72]];
  for(const [a,b] of leftSegments){
    block(scene,.16,3.13,b-a,'#b9a5c6',wallX,1.55,(a+b)/2,.023);
    block(scene,.061,.12,b-a,p.ivory,-4.67,.09,(a+b)/2,.018);
    block(scene,.042,.048,b-a,'#d8c3d4',-4.677,1.30,(a+b)/2,.009);
  }
  block(scene,.16,3.12-height,width,'#b9a5c6',wallX,(3.12+height)/2,center,.018);
  block(scene,9.72,.13,.069,p.ivory,0,.08,-3.565,.018);
  block(scene,9.76,.105,.24,p.cream,0,3.123,-3.68,.042);
  block(scene,.24,.105,7.44,p.cream,-4.79,3.123,0,.04);
  for(let i=0;i<9;i++){
    const z=-3.0+i*.78;
    if(z<start-.07 || z>end+.07)block(scene,.035,1.13,.042,'#a894b8',-4.684,.72,z,.009);
  }
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
  const lamps=[];
  let animate=()=>{};
  if(kind==='living'){
    lamps.push(sofa(scene));
    animate=accessories(scene);
    mediaCabinet(scene);
  }else if(kind==='bedroom'){
    lamps.push(bed(scene));
    wardrobe(scene);
    plant(scene,3.85,0,1.95,1.26);
  }else if(kind==='study'){
    shelving(scene);
    lamps.push(sofa(scene),readingDesk(scene));
    plant(scene,-3.3,0,-2.6);
  }else if(kind==='gaming'){
    lamps.push(desk(scene,true));
    gameCorner(scene);
  }else if(kind==='kitchen'){
    lamps.push(kitchen(scene));
  }
  return {animate,setWarm(on){
    view.material.map=on?warm:day;view.material.needsUpdate=true;
    for(const {shade,light} of lamps){shade.emissiveIntensity=on?.9:.28;light.intensity=(on?1.4:.45)*(light.distance);}
  }};
}

function mediaCabinet(scene){
  const g=group(scene,2.75,0,-2.82);
  shadow(scene,2.75,-2.82,3.58,1.79);
  block(g,2.68,.49,.62,p.oak,0,.28,0,.08);
  for(const x of [-.89,0,.89]){
    block(g,.81,.30,.047,'#d8b5a9',x,.29,.329,.025);
    block(g,.11,.03,.052,brass,x,.325,.371,.009);
  }
  block(g,2.18,1.19,.111,p.navy,0,1.19,-.02,.07);
  flat(g,2.05,1.07,windowScene('warm'),0,1.19,.042);
  block(g,.63,.046,.25,p.walnut,0,.55,0,.026);
  plant(g,1.09,.55,.11,.65);
}

function wardrobe(scene){
  const g=group(scene,2.94,0,-2.76);
  shadow(scene,2.94,-2.72,3.8,1.9);
  block(g,2.65,2.42,.79,p.oak,0,1.24,0,.12);
  for(const x of [-.64,.64]){
    block(g,1.18,1.64,.11,'#d4b1bc',x,1.42,.43,.075);
    block(g,1.01,1.47,.016,'#e9ccce',x,1.42,.494,.009);
    block(g,.055,.22,.057,brass,x<0?-.16:.16,1.36,.516,.020);
  }
  block(g,2.46,.41,.11,p.cream,0,.42,.427,.06);
  block(g,.21,.034,.053,brass,0,.45,.508,.015);
  const bench=group(scene,1.43,0,1.39);
  block(bench,1.52,.35,.68,p.walnut,0,.24,0,.12);
  block(bench,1.53,.21,.70,'#c3a7ca',0,.49,0,.097);
  const cushion=block(bench,.41,.11,.39,'#f0cfcb',.42,.63,-.04,.066);
  cushion.rotation.y=.24;
  const vanity=group(scene,-3.63,0,1.26);vanity.rotation.y=Math.PI/2;
  block(vanity,1.34,.47,.66,p.oak,0,.53,0,.08);
  for(const x of [-.54,.54])block(vanity,.105,.38,.54,p.walnut,x,.20,0,.03);
  oval(vanity,.42,.56,.061,brass,0,1.28,-.26);
  oval(vanity,.365,.49,.025,'#abbed2',0,1.28,-.20);
  for(let i=0;i<3;i++)cylinder(vanity,.045,.06,.12,['#e1aeb7','#c3adca','#bfc3c6'][i],-.37+i*.16,.825,.16);
  const basket=group(scene,3.54,0,.40);
  cylinder(basket,.34,.28,.41,'#ba8793',0,.22,0);
  for(let i=0;i<4;i++)cylinder(basket,.33,.33,.015,'#d8a9ad',0,.13+i*.069,0);
  oval(basket,.292,.098,.25,p.cream,0,.407,0);
}

function readingDesk(scene){
  const g=group(scene,1.22,0,-.64);
  shadow(scene,1.22,-.64,3.48,2.12);
  for(const x of [-1.05,1.05])for(const z of [-.32,.32])block(g,.106,.87,.106,p.walnut,x,.444,z,.027);
  block(g,2.38,.09,.87,p.oak,0,.901,0,.054);
  for(let i=0;i<3;i++)block(g,.47,.078,.32,['#7ba2aa','#b792b7','#d6ad9d'][i],-.61,.983+i*.072,-.10,.022);
  const notebook=group(g,.18,.961,.10);notebook.rotation.y=-.13;
  block(notebook,.72,.065,.42,p.navy);
  block(notebook,.67,.034,.393,p.ivory,0,.041,0,.014);
  for(let i=0;i<5;i++)block(notebook,.49,.006,.008,'#aa9eae',0,.061,-.145+i*.063,.002);
  plant(g,.84,.951,-.17,.51);
  const stool=group(scene,1.13,0,.56);
  block(stool,.69,.13,.66,p.lilac,0,.478,0,.068);
  for(const x of [-.27,.27])for(const z of [-.24,.24])cylinder(stool,.035,.029,.43,brass,x,.221,z);
  return lamp(g,-.87,.949,-.18);
}

function gameCorner(scene){
  const mat=block(scene,4.4,.023,2.95,'#77749c',.68,.009,1.22,.015);
  mat.rotation.y=.035;
  for(let i=0;i<6;i++)block(scene,3.78,.004,.018,i%2?'#8c87ad':'#8882a8',.68,.023,.18+i*.38,.002);
  for(const [x,y,len] of [[-.37,2.54,1.12],[.22,2.35,1.42],[.82,2.56,1.08]]){
    block(scene,len,.07,.087,glow('#b3a3ff'),x,y,-3.54,.024).rotation.z=-.25;
  }
  const casePC=group(scene,2.85,0,-2.58);
  block(casePC,.46,.94,.74,'#363652',0,.53,0,.075);
  block(casePC,.387,.84,.047,'#4a486c',0,.53,.395,.026);
  for(let i=0;i<3;i++){
    const tint=i%2?'#b886f4':'#85dfd8';
    mesh(casePC,new THREE.TorusGeometry(.124,.016,8,26),glow(tint),0,.28+i*.247,.432);
    oval(casePC,.044,.044,.014,'#adade1',0,.28+i*.247,.428);
  }
  const rack=group(scene,-3.47,0,-1.60);rack.rotation.y=.12;
  block(rack,1.28,1.38,.51,p.navy,0,.70,0,.09);
  for(let i=0;i<3;i++)block(rack,1.12,.057,.52,p.lilac,0,.32+i*.35,.003,.020);
  block(rack,.88,.072,.39,p.oak,0,1.407,0,.04);
  for(const [x,color] of [[-.27,'#c3b5e7'],[.28,'#84b3bd']]){
    const ctrl=group(rack,x,1.49,.05);
    block(ctrl,.32,.12,.18,color,0,0,0,.042);
    oval(ctrl,.035,.022,.029,p.navy,-.085,.064,.013);
    oval(ctrl,.030,.021,.029,p.cream,.077,.061,.017);
  }
  plant(scene,3.8,0,1.45,1.2);
  shadow(scene,-2.58,1.83,2.08,1.77);
  oval(scene,.73,.34,.58,'#846e9f',-2.58,.24,1.83);
  oval(scene,.61,.43,.49,'#aa8ab7',-2.71,.47,1.62).rotation.x=-.26;
}

function kitchen(scene){
  const g=group(scene,1.83,0,-2.62);shadow(scene,1.83,-2.63,5.42,2.13);
  block(g,5.12,.83,.82,'#a5b8b1',0,.45,0,.08);
  block(g,5.24,.104,.91,p.cream,0,.918,0,.055);
  for(let i=0;i<6;i++){
    const x=-2.08+i*.83;
    block(g,.76,.58,.065,'#c3cec0',x,.47,.426,.045);
    block(g,.19,.037,.058,brass,x,.62,.477,.013);
  }
  block(g,1.08,.07,.51,'#8c9eaa',-1.28,.983,-.02,.046);
  block(g,.86,.025,.37,'#536977',-1.28,1.012,-.01,.037);
  line(g,[[-1.31,.985,-.3],[-1.31,1.32,-.31],[-1.31,1.41,-.15],[-1.31,1.28,.002]],.025,brass);
  block(g,1.15,.043,.60,p.navy,.43,.997,-.075,.038);
  for(const x of [.16,.71])for(const z of [-.20,.035])cylinder(g,.094,.094,.012,'#646a81',x,1.027,z);
  cylinder(g,.233,.206,.181,'#b88a9f',.63,1.107,-.15);
  cylinder(g,.243,.234,.028,p.cream,.63,1.213,-.15);
  oval(g,.045,.042,.049,p.walnut,.63,1.248,-.15);
  block(g,.53,.04,.35,p.oak,1.67,.996,.096,.025);
  for(let i=0;i<3;i++)oval(g,.064,.035,.065,'#dca188',1.59+i*.10,1.046,.09);
  const fridge=group(scene,-3.57,0,-2.75);
  block(fridge,1.22,2.23,.88,'#dfc1bd',0,1.137,0,.13);
  block(fridge,1.08,.52,.09,'#f0d4ce',0,1.90,.47,.075);
  block(fridge,1.08,1.34,.08,'#e9c8c4',0,.872,.47,.076);
  for(const y of [1.28,1.79])block(fridge,.054,.28,.06,brass,.38,y,.529,.024);
  const island=group(scene,-.65,0,1.03);
  shadow(scene,-.65,1.02,2.98,1.91);
  block(island,2.12,.73,.99,'#a9b5b7',0,.394,0,.082);
  block(island,2.30,.105,1.08,p.oak,0,.810,0,.06);
  cylinder(island,.21,.16,.08,p.cream,.43,.904,.03);
  for(let i=0;i<4;i++)oval(island,.078,.077,.071,['#e6a291','#eec387','#bfb590'][i%3],.32+i*.069,.978,(i%2)*.09);
  return lamp(g,2.03,.978,-.18);
}

function garden(scene){
  block(scene,9.8,.39,7.5,'#7e706b',0,-.27,0,.18);
  block(scene,9.67,.08,7.37,'#a9bba1',0,-.036,0,.10);
  for(let i=0;i<15;i++){
    const x=-4.5+i*.65;
    oval(scene,.53,.42,.42,['#789f86','#88ad8e','#9cb89d'][i%3],x,.48,-3.20);
  }
  for(const z of [-2.80,-2.06,-1.32,-.58,.04,GATE_CENTER-1.04,GATE_CENTER+1.04,3.30]){
    oval(scene,.48,.45,.46,'#89ae94',-4.33,.43,z);
  }
  for(let i=0;i<10;i++){
    const z=-2.55+i*.54,x=.27*Math.sin(i*.85);
    block(scene,.64+(i%2)*.13,.065,.38,i%2?'#d1c0b9':'#e2d1bf',x,.027,z,.07).rotation.y=Math.sin(i)*.25;
  }
  for(const [x,z] of [[-3.76,GATE_CENTER],[-3.21,1.94],[-2.62,2.18],[-2.04,2.30]]){
    block(scene,.43,.065,.35,'#d9c9bf',x,.027,z,.067);
  }
  const pond=group(scene,2.62,0,1.16);
  oval(pond,1.49,.06,1.03,'#c0b3b6',0,.035,0);
  oval(pond,1.31,.058,.86,new THREE.MeshStandardMaterial({color:'#8cc5cb',roughness:.29}),0,.068,0);
  for(let i=0;i<12;i++){
    const a=i*Math.PI/6;
    oval(pond,.195,.074,.138,i%2?'#d7c5bc':'#a59ea8',1.37*Math.cos(a),.097,.91*Math.sin(a));
  }
  for(const [x,z] of [[-.55,.29],[.42,-.22],[.49,.33]]){
    oval(pond,.16,.016,.12,'#79a58e',x,.138,z);
    oval(pond,.05,.028,.042,'#edb3b6',x+.035,.163,z);
  }
  const bench=group(scene,-2.38,0,1.18);bench.rotation.y=.48;
  for(const x of [-.65,.65])block(bench,.116,.45,.36,p.walnut,x,.239,0,.032);
  for(let i=0;i<3;i++){
    block(bench,1.69,.073,.13,p.oak,0,.49,-.17+i*.14,.030);
    block(bench,1.69,.106,.074,p.oak,0,.65+i*.114,-.23,.029);
  }
  for(const [x,z] of [[-2.68,-2.52],[2.18,-2.64],[4.01,-1.74],[-3.63,3.09]]){
    plant(scene,x,0,z,1.28);
  }
  for(const [x,z] of [[-2.98,-.85],[3.29,2.58],[-2.88,2.79]]){
    const patch=group(scene,x,0,z);
    block(patch,1.26,.115,.68,'#b9908c',0,.055,0,.075);
    block(patch,1.10,.025,.54,'#847577',0,.123,0,.039);
    for(let i=0;i<8;i++){
      const px=-.43+(i%4)*.281,pz=(i<4?-.13:.13);
      const height=.22+(i*7)%13/100;
      cylinder(patch,.012,.018,height,'#6e9886',px,.128+height/2,pz);
      oval(patch,.074,.072,.069,['#e6a5b5','#c0a8d0','#e9c5aa'][i%3],px,.12+height,pz);
    }
  }
  const pergola=group(scene,2.03,0,-1.72);
  for(const x of [-.8,.8])for(const z of [-.47,.47])block(pergola,.099,1.88,.099,'#c19a8f',x,.938,z,.027);
  for(let i=0;i<6;i++)block(pergola,.077,.088,1.11,'#cfaa9a',-.82+i*.326,1.91,0,.027);
  for(const z of [-.48,.48])block(pergola,1.82,.096,.089,'#bc9187',0,1.79,z,.023);
  line(pergola,[[-.80,.18,-.49],[-.85,.73,-.49],[-.73,1.35,-.47],[-.59,1.85,-.34],[.36,1.89,-.29]],.027,'#7fa391');
  for(let i=0;i<7;i++)oval(pergola,.116,.063,.077,i%2?'#b0c5a7':'#e0a8b8',-.82+i*.169,1.83,-.36);
  const lantern=lamp(scene,-3.59,0,-1.55,true);
  return {animate:()=>{},setWarm(on){lantern.shade.emissiveIntensity=on?.88:.30;lantern.light.intensity=on?5:1.5;}};
}
