
const $=id=>document.getElementById(id),money=n=>new Intl.NumberFormat('id-ID',{style:'currency',currency:'IDR',maximumFractionDigits:0}).format(n),num=n=>new Intl.NumberFormat('id-ID',{maximumFractionDigits:1}).format(n);
async function request(url,body){const r=await fetch(url,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const d=await r.json();if(!r.ok)throw Error(d.error||'Permintaan gagal');return d}
function cell(row,text){const td=document.createElement('td');td.textContent=text;td.dataset.label=['Bahan / alasan','Stok tersedia','Dalam pesanan','Beli','Estimasi biaya'][row.children.length];row.append(td);return td}
function icon(name){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg'),use=document.createElementNS(svg.namespaceURI,'use');svg.classList.add('icon');svg.setAttribute('aria-hidden','true');use.setAttribute('href','#i-'+name);svg.append(use);return svg}
function explanation(r){
  const box=document.createElement('div');box.className='reason-content';
  const figure=document.createElement('figure');figure.className='stock-chart';
  const e=r.purchase_explanation;
  const caption=document.createElement('figcaption');caption.textContent='Proyeksi stok ('+r.unit+') setelah keputusan hari ini';figure.append(caption);
  const wrap=document.createElement('div');wrap.className='stock-plot-wrap';
  wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Grafik proyeksi '+r.ingredient_name+'; geser untuk melihat seluruh waktu');
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 640 320');svg.setAttribute('role','img');
  svg.setAttribute('aria-label','Grafik proyeksi stok tanpa pembelian dan dengan rencana pembelian, serta titik pemesanan dan target stok.');
  const make=(tag,attrs={},text='')=>{const node=document.createElementNS(ns,tag);for(const [key,value]of Object.entries(attrs))node.setAttribute(key,value);if(text)node.textContent=text;return node};
  const W=640,H=320,pad={left:64,right:24,top:30,bottom:52};
  const lead=Math.max(0,Number(e.lead_days)),horizon=Math.max(lead+0.1,Number(e.target_days),1);
  const high=Math.max(Number(e.target_stock),Number(e.post_order_stock),Number(e.reorder_point),Number(e.stock_position),1);
  const magnitude=10**Math.floor(Math.log10(high)),step=Math.max(1,Math.ceil(high/(magnitude*5))*magnitude),yMax=step*5;
  const x=d=>pad.left+(d/horizon)*(W-pad.left-pad.right),y=v=>H-pad.bottom-(Math.max(0,Math.min(yMax,v))/yMax)*(H-pad.top-pad.bottom);
  for(let value=0;value<=yMax;value+=step){
    svg.append(make('line',{x1:pad.left,y1:y(value),x2:W-pad.right,y2:y(value),stroke:'var(--rule)','stroke-width':1}));
    svg.append(make('text',{x:pad.left-10,y:y(value)+4,'text-anchor':'end',fill:'var(--muted)','font-size':12},num(value)));
  }
  const days=[...new Set([0,lead,horizon])].sort((a,b)=>a-b);
  for(const day of days){
    svg.append(make('line',{x1:x(day),y1:H-pad.bottom,x2:x(day),y2:H-pad.bottom+5,stroke:'var(--control)','stroke-width':1}));
    svg.append(make('text',{x:x(day),y:H-pad.bottom+22,'text-anchor':'middle',fill:'var(--muted)','font-size':12},day===0?'Hari ini':'Hari +'+num(day)));
  }
  svg.append(make('line',{x1:pad.left,y1:y(e.reorder_point),x2:W-pad.right,y2:y(e.reorder_point),stroke:'var(--chart-3)','stroke-width':2,'stroke-dasharray':'7 5'}));
  svg.append(make('line',{x1:pad.left,y1:y(e.target_stock),x2:W-pad.right,y2:y(e.target_stock),stroke:'var(--chart-4)','stroke-width':2,'stroke-dasharray':'3 5'}));
  svg.append(make('line',{x1:x(lead),y1:pad.top,x2:x(lead),y2:H-pad.bottom,stroke:'var(--accent)','stroke-width':1.5,'stroke-dasharray':'3 4'}));
  svg.append(make('text',{x:x(lead)+5,y:pad.top+12,fill:'var(--accent)','font-size':11},'Pesanan tiba'));
  const noOrderDays=[...new Set([0,lead,horizon])].sort((a,b)=>a-b);
  const planPoints=[[0,e.stock_position],[lead,e.stock_position-e.planned_daily_rate*lead],[lead,e.stock_position+e.purchase_qty-e.planned_daily_rate*lead],[horizon,e.stock_position+e.purchase_qty-e.planned_daily_rate*horizon]];
  const noOrderPoints=noOrderDays.map(day=>[day,Math.max(0,e.stock_position-e.planned_daily_rate*day)]);
  const pathFor=points=>points.map(([day,value],index)=>(index?'L':'M')+' '+x(day)+' '+y(value)).join(' ');
  svg.append(make('path',{d:pathFor(noOrderPoints),fill:'none',stroke:'var(--chart-2)','stroke-width':3,'stroke-dasharray':'7 5','stroke-linejoin':'round','stroke-linecap':'round'}));
  svg.append(make('path',{d:pathFor(planPoints),fill:'none',stroke:'var(--chart-1)','stroke-width':3,'stroke-linejoin':'round','stroke-linecap':'round'}));
  for(const [day,value]of [planPoints[0],planPoints[2],planPoints[3]])svg.append(make('circle',{cx:x(day),cy:y(value),r:4,fill:'var(--surface)',stroke:'var(--chart-1)','stroke-width':2}));
  const legend=document.createElement('ul');legend.className='chart-legend';
  for(const [label,tone]of [['Tanpa pembelian','no-order'],['Dengan rencana beli','with-order'],['Titik pemesanan','reorder'],['Target stok','target']]){
    const item=document.createElement('li'),swatch=document.createElement('span'),name=document.createElement('span');swatch.className='line-swatch '+tone;swatch.setAttribute('aria-hidden','true');name.textContent=label;item.append(swatch,name);legend.append(item);
  }
  const context=document.createElement('p');context.className='chart-context';
  context.textContent=(e.policy.startsWith('ML_')?'Ramalan model ':'Rata-rata pemakaian historis ')+num(e.forecast_daily_rate)+' '+r.unit+'/hari × faktor kebijakan '+num(e.safety_factor)+' = '+num(e.planned_daily_rate)+' '+r.unit+'/hari. Garis rencana beli memasukkan kedatangan '+num(e.purchase_qty)+' '+r.unit+' setelah '+num(e.lead_days)+' hari waktu tunggu pemasok.';
  wrap.append(svg);figure.append(wrap,legend,context);
  const heading=document.createElement('h3');heading.textContent='Dasar rekomendasi';
  const reason=document.createElement('p');reason.className='business-reason';reason.textContent=r.reason;
  box.append(figure,heading,reason);return box;
}

const parameters = new URLSearchParams(location.search);
const branchValue = parameters.get('branch');
if (['1','2','3'].includes(branchValue)) $('branch').value = branchValue;
const views = {
  analysis: ['Analisis persediaan', 'Baca pergerakan pasar sebelum menentukan pembelian.', 'Analisis pasar'],
  purchase: ['Rencana pembelian', 'Periksa jumlah bahan dan alasan sebelum menyetujui rencana.', 'Rencana pembelian'],
  evaluation: ['Evaluasi & sentimen', 'Bandingkan kebijakan dan coba klasifikasi pembahasan menu.', 'Evaluasi & sentimen']
};
function syncURL() {
  const url = new URL(location.href);
  url.searchParams.set('view', document.querySelector('nav a[aria-current="page"]').dataset.route);
  url.searchParams.set('branch', $('branch').value);
  url.searchParams.set('category', $('trend-category').value);
  url.searchParams.set('weeks', $('trend-period').value);
  url.searchParams.set('scale', $('trend-scale').value);
  url.searchParams.set('series', [...document.querySelectorAll('.series-toggles input:checked')].map(i=>i.value).join(','));
  if ($('purchase-only').checked) url.searchParams.set('buy', '1'); else url.searchParams.delete('buy');
  history.replaceState({}, '', url);
  document.querySelectorAll('a[data-route]').forEach(a=>{const target=new URL(url);target.searchParams.set('view',a.dataset.route);a.href=target.pathname+target.search;});
}
function showView(name, focus=false) {
  if (!views[name]) name='analysis';
  document.querySelectorAll('[data-view]').forEach(view=>view.hidden=view.dataset.view!==name);
  document.querySelectorAll('nav a[data-route]').forEach(a=>{
    if(a.dataset.route===name)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
  });
  [$('page-title').textContent,$('page-description').textContent,$('view-label').textContent]=views[name];
  document.title='CafeStock • '+views[name][0];
  syncURL();
  window.dispatchEvent(new Event('cafestock:view'));
  if(focus){$('page-title').tabIndex=-1;$('page-title').focus({preventScroll:true});window.scrollTo(0,0);}
}
window.CafeStockUI={syncURL,showView};
document.querySelectorAll('a[data-route]').forEach(a=>a.addEventListener('click',event=>{
  if(event.button||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  event.preventDefault();showView(a.dataset.route,true);
}));
// Capture query state before URL synchronization writes default controls.
window.CafeStockInitial=parameters;
showView(parameters.get('view')||'analysis');
$('purchase-only').checked=parameters.get('buy')==='1';
let sequence=0, overviewData=null;
function renderPurchases(){
  if(!overviewData)return;
  const rows=overviewData.recommendations;
  $('rows').replaceChildren();
  const filtered=$('purchase-only').checked?rows.filter(r=>r.purchase_qty>0):rows;
  for(const r of filtered){
    const tr=document.createElement('tr'),name=cell(tr,r.ingredient_name);
    tr.dataset.ingredient=String(r.ingredient_id);
    const details=document.createElement('details'),summary=document.createElement('summary');
    summary.textContent='Lihat alasan';summary.setAttribute('aria-label','Lihat alasan '+r.ingredient_name);details.append(summary,explanation(r));name.append(details);
    details.addEventListener('toggle',()=>{
      tr.dataset.expanded=String(details.open);
      name.colSpan=details.open?5:1;
    });
    cell(tr,num(r.on_hand)+' '+r.unit);cell(tr,num(r.on_order)+' '+r.unit);
    cell(tr,r.purchase_qty?num(r.purchase_qty)+' '+r.unit:'Cukup').className=r.purchase_qty?'buy':'';
    cell(tr,money(r.estimated_cost_idr));$('rows').append(tr);
  }
  if(!filtered.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='Tidak ada bahan yang perlu dibeli. Stok sesuai rencana saat ini.';tr.append(td);$('rows').append(tr);}
  $('purchase-total').textContent=filtered.length+' dari '+rows.length+' bahan ditampilkan. Total rencana '+money(rows.reduce((total,r)=>total+r.estimated_cost_idr,0))+'.';
  const preview=$('purchase-preview');preview.replaceChildren();
  const needed=rows.filter(r=>r.purchase_qty>0).sort((a,b)=>b.estimated_cost_idr-a.estimated_cost_idr);
  $('preview-count').textContent=needed.length+' bahan';
  $('preview-cost').textContent=money(rows.reduce((total,r)=>total+r.estimated_cost_idr,0));
  needed.slice(0,4).forEach(r=>{
    const li=document.createElement('li'),button=document.createElement('button'),content=document.createElement('span'),name=document.createElement('strong'),amount=document.createElement('small');
    button.type='button';button.className='preview-item';button.title='Buka alasan pembelian '+r.ingredient_name;
    name.textContent=r.ingredient_name;amount.textContent=num(r.purchase_qty)+' '+r.unit+' · '+money(r.estimated_cost_idr);
    content.append(name,amount);button.append(content,icon('arrow-up-right'));li.append(button);preview.append(li);
    button.addEventListener('click',()=>{
      // A priority ingredient unfolds its own evidence in the purchasing ledger.
      showView('purchase',true);
      const row=[...$('rows').children].find(item=>item.dataset.ingredient===String(r.ingredient_id));
      if(!row)return;
      const disclosure=row.querySelector('details');disclosure.open=true;
      const summary=disclosure.querySelector('summary');summary.focus({preventScroll:true});
      row.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
    });
  });
  if(!needed.length){const li=document.createElement('li');li.textContent='Belum perlu pembelian tambahan.';preview.append(li);}
  if(needed.length>4){const li=document.createElement('li');li.textContent='+'+(needed.length-4)+' bahan pada rencana lengkap.';preview.append(li);}
}
async function load(){
  const ticket=++sequence;
  $('message').textContent='Memuat rencana cabang…';$('approve').disabled=true;
  $('retry-overview').hidden=true;
  try{
    const d=await request('/api/overview?branch='+$('branch').value);if(ticket!==sequence)return;
    overviewData=d;const rows=d.recommendations;
    const total=rows.reduce((sum,r)=>sum+r.estimated_cost_idr,0);
    const stamp=rows.length?rows[0].decision_at:null;
    $('date').textContent=stamp?new Intl.DateTimeFormat('id-ID',{dateStyle:'medium',timeStyle:'short',timeZone:'Asia/Jakarta'}).format(new Date(stamp))+' WIB':'Tanggal belum tersedia';
    if(stamp)$('date').dateTime=stamp;
    $('count').textContent=rows.filter(r=>r.purchase_qty>0).length+' dari '+rows.length;
    $('cost').textContent=money(total);$('policy').textContent=d.optimization.recommended_policy;
    const selected=d.optimization.policies[d.optimization.recommended_policy];
    $('coverage').textContent=selected?new Intl.NumberFormat('id-ID',{style:'percent',maximumFractionDigits:1}).format(selected.test.fill_rate):'—';
    $('export').href='/api/export?branch='+$('branch').value;
    renderPurchases();$('policies').replaceChildren();
    for(const [name,result]of Object.entries(d.optimization.policies)){
      const tr=document.createElement('tr');tr.dataset.selected=String(name===d.optimization.recommended_policy);cell(tr,name);cell(tr,new Intl.NumberFormat('id-ID',{style:'percent',maximumFractionDigits:1}).format(result.test.fill_rate));cell(tr,money(result.test.objective_cost_idr));$('policies').append(tr);
    }
    $('message').textContent=d.approvals.length?'Rencana snapshot ini sudah disetujui lokal.':'Rencana siap diperiksa. Persetujuan disimpan lokal.';
    $('approve').disabled=!rows.length;
    syncURL();
  }catch(error){
    if(ticket!==sequence)return;
    overviewData=null;
    for(const id of ['count','cost','policy','coverage','preview-count','preview-cost'])$(id).textContent='—';
    $('rows').replaceChildren();$('purchase-preview').replaceChildren();$('policies').replaceChildren();
    $('purchase-total').textContent='Rencana belum tersedia untuk cabang ini.';
    $('date').textContent='Snapshot belum tersedia';$('date').removeAttribute('datetime');
    $('message').textContent='Rencana tidak berhasil dimuat. Coba muat kembali.';
    $('retry-overview').hidden=false;
  }
}
$('branch').addEventListener('change',()=>{syncURL();load();});
$('retry-overview').addEventListener('click',load);
$('purchase-only').addEventListener('change',()=>{renderPurchases();syncURL();});
$('approve').addEventListener('click',async()=>{
  const branch=Number($('branch').value);$('approve').disabled=true;$('approve').setAttribute('aria-busy','true');
  try{const result=await request('/api/approve',{branch_id:branch});if(Number($('branch').value)===branch)$('message').textContent=result.message;}
  catch(error){$('message').textContent='Persetujuan belum tersimpan. Coba setujui kembali.';}
  finally{$('approve').removeAttribute('aria-busy');$('approve').disabled=!overviewData;}
});
$('sentiment-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const text=$('text').value.trim();
  if(!text){$('text').setAttribute('aria-invalid','true');$('sentiment').textContent='Isi pembahasan menu terlebih dahulu, lalu pilih Analisis teks.';$('text').focus();return;}
  $('text').removeAttribute('aria-invalid');$('analyze').disabled=true;$('analyze').setAttribute('aria-busy','true');$('sentiment').textContent='Menganalisis teks…';
  try{const result=await request('/api/sentiment',{text});$('sentiment').textContent='Hasil IndoBERT: '+({positive:'Positif',negative:'Negatif',neutral:'Netral',mixed:'Campuran'}[result.label]||result.label)+'.';}
  catch(error){$('sentiment').textContent='Teks belum berhasil dianalisis. Pilih Analisis teks untuk mencoba kembali.';}
  finally{$('analyze').disabled=false;$('analyze').removeAttribute('aria-busy');}
});
window.addEventListener('popstate',()=>location.reload());
load();
