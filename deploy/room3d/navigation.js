// Floor-space obstacles; the final sit/bed interaction is handled separately from walking.
const boxes={
  living:[[-1.31,.03,1.56,2.36],[3.02,4.54,.90,1.80],[1.34,4.18,-3.16,-2.42]],
  bedroom:[[-4.07,-1.80,-3.52,-.77],[1.55,4.34,-3.20,-2.26],[-4.03,-3.24,.55,1.96],[.66,2.21,1.04,1.75]],
  study:[[.02,2.43,-1.10,-.20],[3.25,4.65,-3.25,-2.51]],
  gaming:[[-.20,2.41,-3.23,-2.20],[2.58,3.12,-3.0,-2.15],[-4.13,-2.81,-1.94,-1.30],[-3.31,-1.88,1.16,2.42]],
  kitchen:[[-.78,4.48,-3.10,-2.21],[-4.21,-2.93,-3.23,-2.28],[-1.82,.52,.47,1.60]],
  garden:[[1.19,4.05,.23,2.07],[-3.32,-1.42,.70,1.72]],
};
const pad=.14;
function hits(a,b,bounds){
  let low=0,high=1;
  for(const [index,min,max] of [[0,bounds[0],bounds[1]],[2,bounds[2],bounds[3]]]){
    const d=b[index]-a[index];
    if(Math.abs(d)<1e-8){if(a[index]<=min||a[index]>=max)return false;continue;}
    let t1=(min-a[index])/d,t2=(max-a[index])/d;if(t1>t2)[t1,t2]=[t2,t1];
    low=Math.max(low,t1);high=Math.min(high,t2);if(low>=high)return false;
  }
  return high>0&&low<1;
}
function clearSegment(room,a,b){
  if((boxes[room]||[]).some(([x1,x2,z1,z2])=>hits(a,b,[x1-pad,x2+pad,z1-pad,z2+pad])))return false;
  if(room==='living'||room==='study'){
    const local=p=>{const dx=p[0]+3.36,dz=p[2]-.88;return [dx*Math.cos(.57)-dz*Math.sin(.57),0,dx*Math.sin(.57)+dz*Math.cos(.57)];};
    if(hits(local(a),local(b),[-1.43,1.43,-.72,.72]))return false;
  }
  return true;
}
export function walkable(room,x,z){
  if(room==='living'||room==='study'){
    const dx=x+3.36,dz=z-.88,lx=dx*Math.cos(.57)-dz*Math.sin(.57),lz=dx*Math.sin(.57)+dz*Math.cos(.57);
    if(Math.abs(lx)<1.43&&Math.abs(lz)<.72)return false;
  }
  return Math.abs(x)<4.55&&Math.abs(z)<3.42&&!(boxes[room]||[]).some(([a,b,c,d])=>x>a-pad&&x<b+pad&&z>c-pad&&z<d+pad);
}
export function floorRoute(room,start,end){
  const step=.24,cell=p=>[Math.round(p[0]/step),Math.round(p[2]/step)],key=p=>p.join(',');
  const first=cell(start),last=cell(end),goal=key(last),open=[first],cost=new Map([[key(first),0]]),prev=new Map();
  const valid=p=>walkable(room,p[0]*step,p[1]*step)||key(p)===goal||key(p)===key(first);
  let found=false;
  for(let n=0;n<1800&&open.length;n++){
    open.sort((a,b)=>(cost.get(key(a))+Math.hypot(a[0]-last[0],a[1]-last[1]))-(cost.get(key(b))+Math.hypot(b[0]-last[0],b[1]-last[1])));
    const p=open.shift(),id=key(p);
    if(id===goal){found=true;break;}
    for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]){
      const next=[p[0]+dx,p[1]+dz],nextId=key(next);
      if(!valid(next)||(dx&&dz&&(!valid([p[0]+dx,p[1]])||!valid([p[0],p[1]+dz]))))continue;
      if(!clearSegment(room,[p[0]*step,0,p[1]*step],[next[0]*step,0,next[1]*step]))continue;
      const value=cost.get(id)+Math.hypot(dx,dz);
      if(value>=(cost.get(nextId)??Infinity))continue;
      cost.set(nextId,value);prev.set(nextId,p);if(!open.some(v=>key(v)===nextId))open.push(next);
    }
  }
  if(!found)return null; // Wait in place instead of walking through furniture.
  const path=[];let p=last;
  while(key(p)!==key(first)){path.unshift([p[0]*step,0,p[1]*step]);p=prev.get(key(p));}
  path.push([...end]);
  const clear=(a,b)=>clearSegment(room,a,b);
  const reduced=[];let from=start;
  while(path.length){
    let far=0;for(let i=1;i<path.length;i++){if(clear(from,path[i]))far=i;}
    const next=path[far];reduced.push(next);path.splice(0,far+1);from=next;
  }
  return reduced;
}
