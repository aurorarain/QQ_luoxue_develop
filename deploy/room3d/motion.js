// Deterministic presentation timing. Brain activity selects the action; this module completes its movement.
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const ease=v=>{v=clamp(v);return v*v*(3-2*v);};
const mix=(a,b,t)=>a+(b-a)*t;
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]);
const angle=(a,b)=>Math.atan2(Math.sin(b-a),Math.cos(b-a));
const seated=new Set(['sit','sit-read','listen','watch','game','browse','write','draw']);
const lying=new Set(['sleep','recline']);
const finite=new Set(['stretch','shelve','unpack','dress','wash']);
const durations={read:10,'sit-read':10,write:8,draw:9,game:7,browse:7,phone:7,cook:8,
  eat:7,water:7,pet:6,window:9,stretch:6,shelve:6,unpack:8,dress:7,wash:8,listen:9,watch:10};

export function headingFor(action){
  if(lying.has(action))return 0;
  if(['game','browse','write','draw','wash','cook','window','shelve','dress','eat'].includes(action))return Math.PI;
  if(action==='water')return -2.55;
  if(action==='pet')return -.18;
  return seated.has(action)?.55:.24;
}

export function approachFor(target,action){
  if(lying.has(action))return [target[0]+1.94,0,target[2]-1.25];
  if(seated.has(action))return [target[0],0,target[2]+.43];
  return [target[0],0,target[2]];
}

export class MotionDirector{
  constructor(position=[.53,0,.62],route=(a,b)=>[b]){
    this.position=[...position];this.heading=.24;this.seat=0;this.lie=0;
    this.route=route;this.action='idle';this.stage='hold';this.queue=[];
    this.elapsed=0;this.taskTime=0;this.cycles=0;this.sequence=0;this.lastKey='';
    this.waiter=null;this.destination=[...position];this.engagement=0;
  }
  request(target,action,snap=false){
    const key=action+':'+target.join(',');
    if(key===this.lastKey&&!snap)return this.promise||Promise.resolve(true);
    this.waiter?.(false);this.waiter=null;this.sequence++;
    this.lastKey=key;this.destination=[...target];
    if(lying.has(action))this.bedTarget=[...target];
    this.promise=new Promise(resolve=>{this.waiter=resolve;});
    if(snap){
      this.queue=[];this.position=[...target];this.heading=headingFor(action);
      this.seat=seated.has(action)?1:0;this.lie=lying.has(action)?1:0;
      this.action=action;this.stage='perform';this.taskTime=0;this.cycles=0;
      this.waiter(true);this.waiter=null;return this.promise;
    }
    if(this.stage==='perform'&&distance(this.position,target)<.025&&Math.abs(this.position[1]-target[1])<.025&&
      ((lying.has(this.action)&&lying.has(action))||(seated.has(this.action)&&seated.has(action)))){
      this.queue=[];
      if(this.engagement>.05)this.queue.push({kind:'put-away',from:[...target],to:[...target],duration:.65,
        seatFrom:this.seat,seatTo:this.seat,lieFrom:this.lie,lieTo:this.lie,heading:this.heading,action:this.action});
      this.nextAction=action;this.nextSegment();return this.promise;
    }
    let point=[...this.position],seat=this.seat,lie=this.lie;
    const queue=[];
    const add=(kind,end,duration,nextSeat=seat,nextLie=lie,face=this.heading,act=this.action)=>{
      queue.push({kind,from:[...point],to:[...end],duration,seatFrom:seat,seatTo:nextSeat,
        lieFrom:lie,lieTo:nextLie,heading:face,action:act});
      point=[...end];seat=nextSeat;lie=nextLie;
    };
    if(this.stage==='perform'&&this.engagement>.05)add('put-away',point,.65);
    if(lie>.01){
      const bed=this.bedTarget||point,edge=[bed[0]+1.37,-.47,bed[2]-1.25];
      add('sit-up',edge,1.3,1,0,0);
      add('stand-up',[edge[0]+.57,0,edge[2]],1.05,0,0,Math.PI/2);
    }else if(seat>.01){
      add('stand-up',[point[0],0,point[2]+.43],.95,0,0,this.heading);
    }else if(Math.abs(point[1])>.02){add('stand-up',[point[0],0,point[2]],.55,0,0);}
    const approach=approachFor(target,action);
    const path=this.route(point,approach);
    if(!path){this.lastKey='';this.waiter(false);this.waiter=null;return this.promise;}
    for(const waypoint of path){
      const length=distance(point,waypoint);
      if(length>.015)add('walk',waypoint,length/1.12,0,0,Math.atan2(waypoint[0]-point[0],waypoint[2]-point[2]),'stroll');
    }
    add('turn',approach,.40,0,0,headingFor(action),'idle');
    if(lying.has(action)){
      add('sit-down',[target[0]+1.37,-.47,target[2]-1.25],1.05,1,0,0,'sit');
      add('lie-down',target,1.45,0,1,0,action);
    }else if(seated.has(action))add('sit-down',target,1.05,1,0,headingFor(action),action);
    else add('settle',target,.35,0,0,headingFor(action),action);
    this.queue=queue;this.elapsed=0;this.nextAction=action;this.nextSegment();
    return this.promise;
  }
  nextSegment(){
    this.segment=this.queue.shift()||null;this.elapsed=0;
    if(this.segment){
      this.segment.startHeading=this.heading;this.stage=this.segment.kind;this.action=this.segment.action;
    }else{
      this.action=this.nextAction||this.action;this.stage='perform';this.taskTime=0;this.cycles=0;
      this.waiter?.(true);this.waiter=null;
    }
  }
  update(dt,reduce=false){
    dt=clamp(dt,0,.1);
    if(reduce&&this.segment){
      while(this.segment){
        this.position=[...this.segment.to];this.seat=this.segment.seatTo;this.lie=this.segment.lieTo;
        this.heading=this.segment.heading;this.nextSegment();
      }
    }
    let left=dt;
    while(this.segment&&left>0){
      const s=this.segment,used=Math.min(left,s.duration-this.elapsed);
      this.elapsed+=used;left-=used;
      const progress=clamp(this.elapsed/s.duration),t=ease(progress);
      this.position=s.from.map((v,i)=>mix(v,s.to[i],t));
      this.seat=mix(s.seatFrom,s.seatTo,t);this.lie=mix(s.lieFrom,s.lieTo,t);
      this.heading=s.startHeading+angle(s.startHeading,s.heading)*ease(clamp(progress*2));
      if(progress>=1)this.nextSegment();else break;
    }
    const duration=durations[this.action]||8;
    if(this.stage==='perform'&&!reduce)this.taskTime+=left;
    if(this.stage==='perform'&&reduce)this.taskTime=finite.has(this.action)?duration:duration*.5;
    this.cycles=Math.floor(this.taskTime/duration);
    if(finite.has(this.action))this.cycles=Math.min(1,this.cycles);
    const completed=finite.has(this.action)&&this.cycles>0;
    const cycle=completed?1:(this.taskTime%duration)/duration;
    const phase=completed?'rest':cycle<.14?'reach':cycle<.28?'take':cycle<.76?'work':cycle<.91?'return':'rest';
    let engagement=phase==='reach'?ease(cycle/.14)*.15:phase==='take'?mix(.15,1,ease((cycle-.14)/.14)):
      phase==='work'?1:phase==='return'?1-ease((cycle-.76)/.15):0;
    if(this.stage==='put-away')engagement=1-ease(this.elapsed/this.segment.duration);
    else if(this.stage!=='perform')engagement=0;
    this.engagement=engagement;
    return {position:this.position,heading:this.heading,seat:this.seat,lie:this.lie,action:this.action,
      stage:this.stage,taskPhase:phase,cycle,work:clamp((cycle-.28)/.48),engagement,
      moving:this.stage==='walk',progress:this.segment?clamp(this.elapsed/this.segment.duration):1,
      time:this.taskTime,cycles:this.cycles,completed,sequence:this.sequence};
  }
}
