(() => {
  const filters = document.querySelectorAll('[data-filter]');
  filters.forEach(button => button.addEventListener('click', () => {
    filters.forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    let count = 0;
    document.querySelectorAll('[data-category]').forEach(card => {
      card.hidden = button.dataset.filter !== 'All' && card.dataset.category !== button.dataset.filter;
      if (!card.hidden) count++;
    });
    document.getElementById('filter-count').textContent = `${count} figures`;
  }));
  const svg = document.getElementById('route-map');
  if (!svg || !window.ROUTE_DATA) return;
  const data = window.ROUTE_DATA;
  const select = document.getElementById('route-select');
  const slider = document.getElementById('route-progress');
  const button = document.getElementById('play-route');
  let run, elapsed = 0, playing = false, last = 0;
  const ns = 'http://www.w3.org/2000/svg';
  function shape(tag, attrs, text) {
    const el = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
    if (text) el.textContent = text;
    svg.appendChild(el); return el;
  }
  const x = v => 20 + v * 24, y = v => 500 - v * 24;
  let trail, robot;
  function stop() { playing = false; button.textContent = 'Play replay'; button.setAttribute('aria-pressed', 'false'); }
  function load() {
    stop(); run = data.runs[Number(select.value)]; elapsed = 0; slider.value = 0;
    svg.replaceChildren();
    data.geometry.forEach(([px, py, w, h]) => shape('rect', {x:x(px), y:y(py+h), width:w*24, height:h*24, fill:'#bac6d0'}));
    for (let i=0; i<=20; i+=5) {
      shape('text', {x:x(i), y:517, 'text-anchor':'middle', 'font-size':10, fill:'#526779'}, String(i));
    }
    trail=shape('polyline', {fill:'none', stroke:'#087f8c', 'stroke-width':3, 'stroke-linejoin':'round'});
    const list = document.getElementById('route-targets'); list.replaceChildren();
    run.plan.plan.filter(step=>step.action==='navigate').forEach((step,i) => {
      const p=data.locations[step.target];
      shape('circle', {cx:x(p.x),cy:y(p.y),r:7,fill:'#d56b35',stroke:'white','stroke-width':2});
      shape('text', {x:x(p.x)+9,y:y(p.y)-9,'font-size':13,fill:'#86401f','font-weight':700},String(i+1));
      const item=document.createElement('li'); item.textContent=step.target; list.appendChild(item);
    });
    robot=shape('circle', {r:7,fill:'#162b3b',stroke:'#fff','stroke-width':2});
    update();
  }
  const duration = () => run.points[run.points.length-1].sim_time_s - run.points[0].sim_time_s;
  function update() {
    const start=run.points[0].sim_time_s;
    let end=run.points.findIndex(p=>p.sim_time_s > start+elapsed);
    if(end < 0) end=run.points.length;
    const visible=run.points.slice(0,Math.max(1,end));
    const current=visible[visible.length-1];
    trail.setAttribute('points',visible.map(p=>`${x(p.x)},${y(p.y)}`).join(' '));
    robot.setAttribute('cx',x(current.x)); robot.setAttribute('cy',y(current.y));
    slider.value=String(Math.round(elapsed/duration()*1000));
    document.getElementById('route-time').textContent = `${elapsed.toFixed(1)} / ${duration().toFixed(1)} s of recording · x ${current.x.toFixed(2)}, y ${current.y.toFixed(2)} m`;
  }
  function animate(now) {
    if(!playing) return;
    elapsed=Math.min(duration(),elapsed+(now-last)/1000*8); last=now; update();
    if(elapsed>=duration()) stop(); else requestAnimationFrame(animate);
  }
  button.addEventListener('click',()=>{
    if(playing) {stop();return;}
    if(elapsed>=duration()) elapsed=0;
    playing=true; last=performance.now(); button.textContent='Pause replay'; button.setAttribute('aria-pressed','true');
    requestAnimationFrame(animate);
  });
  select.addEventListener('change',load);
  slider.addEventListener('input',()=>{stop();elapsed=Number(slider.value)/1000*duration();update();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
  load();
})();
