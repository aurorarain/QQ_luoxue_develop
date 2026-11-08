(() => {
  const slot=document.querySelector('[data-site-nav]');
  if(!slot)return;
  const active=slot.dataset.siteNav;
  const routes=[
    ['home','房间','/'],['brain','大脑','/brain.html'],['log','日志','/log.html'],['console','控制台','/console.html'],
  ];
  const extra=[
    ['runtime','运行日志','/runtime.html'],['pixel','像素房间','/pixel-room.html'],['voices','音色试听','/voices.html'],
    ['tieba','贴吧节点','/tieba-login.html'],['doubao','豆包登录','/doubao-login.html'],
  ];
  function link([id,label,href]){
    const el=document.createElement('a');el.href=href;el.textContent=label;
    if(id===active)el.setAttribute('aria-current','page');
    return el;
  }
  const nav=document.createElement('nav');nav.className='site-nav';nav.setAttribute('aria-label','洛雪站内导航');
  for(const entry of routes)nav.append(link(entry));
  const dropdown=document.createElement('details');dropdown.className='site-more';
  const summary=document.createElement('summary');summary.textContent='更多';dropdown.append(summary);
  if(extra.some(([id])=>id===active))summary.classList.add('current');
  const menu=document.createElement('div');menu.className='site-menu';
  for(const entry of extra)menu.append(link(entry));
  dropdown.append(menu);nav.append(dropdown);slot.append(nav);
  document.addEventListener('pointerdown',event=>{if(dropdown.open&&!dropdown.contains(event.target))dropdown.open=false;});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&dropdown.open){dropdown.open=false;summary.focus();}});
})();
