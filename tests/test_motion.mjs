import test from 'node:test';
import assert from 'node:assert/strict';
import {MotionDirector,approachFor} from '../deploy/room3d/motion.js';
import {floorRoute,walkable} from '../deploy/room3d/navigation.js';
const tick=(d,seconds,dt=1/60)=>{let frame;for(let t=0;t<seconds-1e-7;t+=dt)frame=d.update(dt);return frame;};

test('seat exit, walk, turn and sit happen in order; arrival promise means settled',async()=>{
 const d=new MotionDirector();await d.request([-3,-.48,1.19],'sit',true);
 let arrived=false;const pending=d.request([.9,-.6,-1.86],'game').then(v=>{arrived=v;});
 const phases=[];
 for(let i=0;i<1500&&d.stage!=='perform';i++){const f=d.update(1/60);if(phases.at(-1)!==f.stage)phases.push(f.stage);}
 await pending;assert.equal(arrived,true);
 assert.deepEqual(phases,['stand-up','walk','turn','sit-down','perform']);
 assert.equal(d.seat,1);assert.deepEqual(d.position,[.9,-.6,-1.86]);
});

test('bed entry and exit remain continuous in position and weight',async()=>{
 const d=new MotionDirector();d.request([-3.42,.78,-1],'sleep');
 let last=d.update(0),phases=new Set();
 for(let i=0;i<1400;i++){
  const f=d.update(1/60);phases.add(f.stage);
  assert.ok(Math.hypot(...f.position.map((v,j)=>v-last.position[j]))<.12);
  assert.ok(Math.abs(f.lie-last.lie)<.04);last={...f,position:[...f.position]};
 }
 assert.equal(d.lie,1);assert.ok(phases.has('sit-down')&&phases.has('lie-down'));
 d.request([0,0,0],'idle');const exits=[];
 for(let i=0;i<1400&&d.stage!=='perform';i++){const f=d.update(1/60);if(exits.at(-1)!==f.stage)exits.push(f.stage);}
 assert.ok(exits.indexOf('sit-up')<exits.indexOf('stand-up'));assert.equal(d.lie,0);
});

test('repeated state polls do not restart an action cycle',async()=>{
 const d=new MotionDirector();await d.request([0,0,0],'wash',true);tick(d,9);
 const before=d.taskTime;d.request([0,0,0],'wash');assert.equal(d.taskTime,before);
 const f=d.update(.01);assert.equal(f.completed,true);assert.equal(f.taskPhase,'rest');
});

test('continuous use has reach, take, work, return and rest phases',async()=>{
 const d=new MotionDirector();await d.request([0,0,0],'eat',true);const phases=new Set();
 for(let i=0;i<600;i++)phases.add(d.update(1/60).taskPhase);
 assert.deepEqual([...phases],['reach','take','work','return','rest']);assert.ok(d.cycles>=1);
});

test('a new intent cancels the old arrival promise',async()=>{
 const d=new MotionDirector();const old=d.request([3,0,0],'cook');tick(d,.3);
 const next=d.request([0,0,1],'idle');assert.equal(await old,false);tick(d,15);assert.equal(await next,true);
 assert.deepEqual(d.position,[0,0,1]);
});

test('motion timing is consistent across frame rates',()=>{
 const a=new MotionDirector(),b=new MotionDirector();a.request([2,0,1],'write');b.request([2,0,1],'write');
 tick(a,1,1/60);tick(b,1,1/20);
 assert.ok(Math.hypot(...a.position.map((v,i)=>v-b.position[i]))<.001);
});

test('walking routes avoid furniture in every room',()=>{
 const targets={living:[-3,-.48,1.19],bedroom:[-3.42,.78,-1],study:[1.4,-.63,.18],gaming:[.9,-.6,-1.86],kitchen:[2.44,0,-2.02],garden:[-2.6,0,-.36]};
 const actions={living:'sit',bedroom:'sleep',study:'write',gaming:'game',kitchen:'cook',garden:'water'};
 for(const [room,target] of Object.entries(targets)){
  let start=[-3.65,0,room==='garden'?1.65:2.24];const end=approachFor(target,actions[room]);
  const path=floorRoute(room,start,end);assert.ok(path,room);
  for(const point of path){
   const length=Math.hypot(point[0]-start[0],point[2]-start[2]);
   for(let t=.05;t<length-.05;t+=.05)assert.ok(walkable(room,start[0]+(point[0]-start[0])*t/length,start[2]+(point[2]-start[2])*t/length),room+' crosses furniture');
   start=point;
  }
 }
});

test('reduced motion settles without a walking animation',async()=>{
 const d=new MotionDirector();const pending=d.request([-3.42,.78,-1],'sleep');const f=d.update(1/60,true);
 assert.equal(await pending,true);assert.equal(f.stage,'perform');assert.equal(f.lie,1);
});
