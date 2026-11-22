
const $=id=>document.getElementById(id),money=n=>new Intl.NumberFormat('id-ID',{style:'currency',currency:'IDR',maximumFractionDigits:0}).format(n),num=n=>new Intl.NumberFormat('id-ID',{maximumFractionDigits:1}).format(n);
function setSidebarCollapsed(collapsed,persist=false){
  document.documentElement.classList.toggle('sidebar-collapsed',collapsed);
  const button=$('sidebar-toggle'),label=collapsed?'Perluas sidebar':'Minimalkan sidebar';
  button.setAttribute('aria-expanded',String(!collapsed));button.setAttribute('aria-label',label);button.title=label;
  if(persist){try{localStorage.setItem('cafestock.sidebar.collapsed',String(collapsed));}catch{}}
}
setSidebarCollapsed(document.documentElement.classList.contains('sidebar-collapsed'));
$('sidebar-toggle').addEventListener('click',()=>setSidebarCollapsed(!document.documentElement.classList.contains('sidebar-collapsed'),true));
async function request(url,body){const r=await fetch(url,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const d=await r.json();if(!r.ok)throw Error(d.error||'Permintaan gagal');return d}
function cell(row,text){const td=document.createElement('td');td.textContent=text;td.dataset.label=['Bahan & alasan','Stok di cabang','Sudah dipesan, belum diterima','Saran pesanan tambahan','Biaya pesanan tambahan'][row.children.length];row.append(td);return td}
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
  const stamp=rows[0]?.decision_at;
  $('purchase-context').textContent=stamp?'Acuan rencana: '+new Intl.DateTimeFormat('id-ID',{dateStyle:'long',timeStyle:'short',timeZone:'Asia/Jakarta'}).format(new Date(stamp))+' WIB. Stok di cabang hanya mencakup bahan yang sudah diterima.':'Tanggal acuan rencana belum tersedia.';
  $('rows').replaceChildren();
  const filtered=$('purchase-only').checked?rows.filter(r=>r.purchase_qty>0):rows;
  for(const r of filtered){
    const tr=document.createElement('tr'),name=cell(tr,r.ingredient_name);
    tr.dataset.ingredient=String(r.ingredient_id);
    const rationale=document.createElement('p');rationale.className='purchase-rationale';
    const e=r.purchase_explanation;
    rationale.textContent=r.purchase_qty>0
      ?'Stok + pesanan berjalan '+num(e.stock_position)+' '+r.unit+', di bawah batas pemesanan '+num(e.reorder_point)+' '+r.unit+'. Disarankan memesan tambahan '+num(r.purchase_qty)+' '+r.unit+'.'
      :'Stok + pesanan berjalan '+num(e.stock_position)+' '+r.unit+' masih memenuhi batas pemesanan '+num(e.reorder_point)+' '+r.unit+'. Belum perlu pesanan tambahan.';
    name.append(rationale);
    const details=document.createElement('details'),summary=document.createElement('summary');
    summary.textContent='Lihat alasan';summary.setAttribute('aria-label','Lihat alasan '+r.ingredient_name);details.append(summary,explanation(r));name.append(details);
    details.addEventListener('toggle',()=>{
      tr.dataset.expanded=String(details.open);
      name.colSpan=details.open?5:1;
    });
    cell(tr,num(r.on_hand)+' '+r.unit);cell(tr,num(r.on_order)+' '+r.unit);
    cell(tr,r.purchase_qty?num(r.purchase_qty)+' '+r.unit:'Tidak perlu tambahan').className=r.purchase_qty?'buy':'';
    cell(tr,money(r.estimated_cost_idr));$('rows').append(tr);
  }
  if(!filtered.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='Tidak ada bahan yang perlu dibeli. Stok sesuai rencana saat ini.';tr.append(td);$('rows').append(tr);}
  $('purchase-total').textContent=filtered.length+' dari '+rows.length+' bahan ditampilkan. Total biaya pesanan tambahan '+money(rows.reduce((total,r)=>total+r.estimated_cost_idr,0))+'. Tidak termasuk biaya pesanan yang sudah berjalan.';
  const preview=$('purchase-preview');preview.replaceChildren();
  const needed=rows.filter(r=>r.purchase_qty>0).sort((a,b)=>b.estimated_cost_idr-a.estimated_cost_idr);
  $('preview-count').textContent=needed.length+' bahan';
  $('preview-cost').textContent=money(rows.reduce((total,r)=>total+r.estimated_cost_idr,0));
  needed.slice(0,4).forEach(r=>{
    const li=document.createElement('li'),button=document.createElement('button'),content=document.createElement('span'),name=document.createElement('strong'),amount=document.createElement('small');
    button.type='button';button.className='preview-item';button.title='Buka alasan pembelian '+r.ingredient_name;
    name.textContent=r.ingredient_name;amount.textContent=num(r.purchase_qty)+' '+r.unit+' tambahan · '+money(r.estimated_cost_idr);
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
    $('purchase-context').textContent='Tanggal acuan rencana belum tersedia.';
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
const sentimentNames={positive:'Positif',negative:'Negatif',neutral:'Netral',mixed:'Campuran'};
const interestNames={positive:'Tertarik mencoba',negative:'Tidak tertarik',neutral:'Arah ketertarikan belum jelas',mixed:'Tertarik tetapi ragu/menolak'};
const sentimentNotes={
  indobert:'IndoBERT menilai sentimen teks produk: positif, negatif, netral, atau campuran.',
  laya_product:'Laya Sentimen Produk menilai opini kualitas atau pengalaman konsumsi produk.',
  laya_trend:'Laya Tren Sentimen menilai ketertarikan mencoba menu dari komentar dan konteks postingan. Pujian rasa saja dapat netral. Hasil ini bukan ramalan penjualan.'
};
let sentimentAvailability=null;
function syncSentimentModel(resetResult=false){
  const model=$('sentiment-model').value,trend=model==='laya_trend';
  $('trend-sentiment-context').hidden=!trend;
  for(const id of ['sentiment-target','sentiment-caption']){
    $(id).disabled=!trend;$(id).required=trend;$(id).removeAttribute('aria-invalid');
  }
  $('sentiment-text-label').textContent=trend?'Komentar publik':'Teks ulasan produk';
  $('text').placeholder=trend?'Contoh: Pengin coba menu ini, tapi masih ragu karena harganya.':'Contoh: Matchanya enak, tetapi harganya mahal…';
  $('text').removeAttribute('aria-invalid');
  $('sentiment-model-note').textContent=sentimentAvailability&&!Object.values(sentimentAvailability).some(Boolean)
    ?'Belum ada model yang siap. Periksa checkpoint lokal dan dependensi model.'
    :sentimentNotes[model];
  if(resetResult)$('sentiment').textContent=trend?'Isi produk target, konteks postingan, dan komentar untuk membaca ketertarikan.':'Masukkan teks ulasan untuk memulai analisis.';
}
async function configureSentimentOptions(){
  const select=$('sentiment-model'),options=Object.fromEntries([...select.options].map(option=>[option.value,option]));
  try{
    const config=await request('/api/sentiment/options');
    sentimentAvailability={indobert:config.indobert_available,laya_product:config.laya_product_available,laya_trend:config.laya_trend_available};
    for(const [id,available] of Object.entries(sentimentAvailability))options[id].disabled=!available;
    const ready=Object.keys(sentimentAvailability).filter(id=>sentimentAvailability[id]);
    if(!sentimentAvailability[select.value]&&ready.length)select.value=ready[0];
    select.disabled=!ready.length;$('analyze').disabled=!ready.length;
    syncSentimentModel();
  }catch(error){
    $('sentiment-model-note').textContent='Status model belum dapat dimuat. Periksa apakah server berjalan.';
  }
}
$('sentiment-model').addEventListener('change',()=>syncSentimentModel(true));
$('sentiment-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const text=$('text').value.trim();
  if(!text){$('text').setAttribute('aria-invalid','true');$('sentiment').textContent='Isi pembahasan menu terlebih dahulu, lalu pilih Analisis teks.';$('text').focus();return;}
  const selectedModel=$('sentiment-model').value;
  const payload={text,model:selectedModel};
  if(selectedModel==='laya_trend'){
    for(const [id,key,message] of [['sentiment-target','target_product','Isi produk/menu target terlebih dahulu.'],['sentiment-caption','parent_caption','Isi caption atau konteks postingan terlebih dahulu.']]){
      const value=$(id).value.trim();
      if(!value){$(id).setAttribute('aria-invalid','true');$('sentiment').textContent=message;$(id).focus();return;}
      $(id).removeAttribute('aria-invalid');payload[key]=value;
    }
  }
  $('text').removeAttribute('aria-invalid');$('analyze').disabled=true;$('analyze').setAttribute('aria-busy','true');$('sentiment').textContent='Menganalisis teks…';
  try{
    const result=await request('/api/sentiment',payload);
    if($('sentiment-model').value!==selectedModel)return;
    const names=result.task==='menu_interest'?interestNames:sentimentNames;
    const label=names[result.label]||result.label;
    const probability=result.probability==null?'':' Probabilitas label pilihan: '+new Intl.NumberFormat('id-ID',{style:'percent',maximumFractionDigits:1}).format(result.probability)+'.';
    $('sentiment').textContent='Hasil '+result.model+': '+label+'.'+probability;
  }
  catch(error){if($('sentiment-model').value===selectedModel)$('sentiment').textContent='Analisis gagal: '+error.message;}
  finally{$('analyze').disabled=sentimentAvailability&&!sentimentAvailability[$('sentiment-model').value];$('analyze').removeAttribute('aria-busy');}
});
window.addEventListener('popstate',()=>location.reload());
configureSentimentOptions();
load();
