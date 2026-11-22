/* Descriptive point-in-time market series. No external chart service. */
(() => {
  const el = id => document.getElementById(id);
  const format = n => n == null ? '—' : new Intl.NumberFormat('id-ID', {maximumFractionDigits: 1}).format(n);
  const points = n => n === null ? 'Belum cukup data' : (n > 0 ? '+' : '') + format(n) + ' poin';
  const date = value => new Date(value).toLocaleDateString('id-ID', {day: 'numeric', month: 'short', year: 'numeric'});
  const moneyIDR=n=>new Intl.NumberFormat('id-ID',{style:'currency',currency:'IDR',maximumFractionDigits:0}).format(n);
  const label = value => ({Coffee:'Kopi', Tea:'Teh', Bakery:'Roti & pastry', 'Drinking Chocolate':'Minuman cokelat'}[value] || value);
  let data, requestNumber = 0, chartWidth = 960, firstLoad=true;
  const initial = window.CafeStockInitial || new URLSearchParams(location.search);
  function node(name, attrs, text) {
    const item = document.createElementNS('http://www.w3.org/2000/svg', name);
    Object.entries(attrs || {}).forEach(([key, value]) => item.setAttribute(key, value));
    if (text !== undefined) item.textContent = text;
    return item;
  }
  const specs = [
    {key:'interest_index', label:'Minat pasar', color:'var(--chart-1)', dash:'', unit:'indeks 0–100'},
    {key:'sentiment_score', label:'Sentimen mingguan', color:'var(--chart-2)', dash:'7 4', unit:'skor −1 sampai +1'},
    {key:'sales_units', label:'Menu terjual dalam 7 hari', color:'var(--chart-3)', dash:'', unit:'porsi / gelas'},
    {key:'stock_value_idr', label:'Nilai bahan tersisa', color:'var(--chart-4)', dash:'3 3', unit:'Rp'}
  ];
  function selectedSpecs() {return specs.filter(s=>el('series-'+s.key).checked);}
  let selectedPoint=null;
  function hidePoint(){
    el('chart-point-detail').hidden=true;
    selectedPoint?.element.removeAttribute('data-selected');selectedPoint=null;
  }
  function showPoint(point,nearest=false){
    hidePoint();selectedPoint=point;point.element.setAttribute('data-selected','true');
    const {spec,row,value}=point,box=el('chart-point-detail'),svg=el('trend-chart');
    el('chart-point-series').textContent=spec.label;
    el('chart-point-value').textContent=spec.key==='stock_value_idr'?moneyIDR(value):format(value)+' '+spec.unit;
    el('chart-point-date').textContent=new Intl.DateTimeFormat('id-ID',{weekday:'long',day:'numeric',month:'long',year:'numeric',timeZone:'Asia/Jakarta'}).format(new Date(row.week_start));
    const others=el('chart-point-other-values');others.replaceChildren();
    for(const other of selectedSpecs().filter(s=>s.key!==spec.key)){
      const entry=document.createElement('div'),name=document.createElement('dt'),number=document.createElement('dd');
      name.textContent=other.label;
      number.textContent=row[other.key]===null?'Belum tersedia':other.key==='stock_value_idr'?moneyIDR(row[other.key]):format(row[other.key])+' '+other.unit;
      entry.append(name,number);others.append(entry);
    }
    el('chart-point-source').textContent=nearest?'Titik pengamatan terdekat. Nilai asli, bukan hasil interpolasi.':'Nilai asli pada tanggal pengamatan.';
    box.hidden=false;
    const position=svg.createSVGPoint();position.x=point.x;position.y=point.y;
    const anchor=position.matrixTransform(svg.getScreenCTM()),frame=svg.parentElement.getBoundingClientRect();
    const left=Math.max(8,Math.min(anchor.x-frame.left+12,frame.width-box.offsetWidth-8));
    const above=anchor.y-frame.top-box.offsetHeight-12;
    const top=above>=8?above:Math.min(anchor.y-frame.top+12,frame.height-box.offsetHeight-8);
    box.style.left=left+'px';box.style.top=Math.max(8,top)+'px';
  }
  el('chart-point-close').addEventListener('click',hidePoint);
  document.addEventListener('keydown',event=>{if(event.key==='Escape')hidePoint();});
  document.addEventListener('pointerdown',event=>{if(!el('trend-chart').parentElement.contains(event.target))hidePoint();});
  function draw(category) {
    const svg=el('trend-chart');hidePoint();svg.replaceChildren();svg.onclick=null;
    const chartPoints=[],chartSegments=[];
    const selected=selectedSpecs(), rows=category.series, original=el('trend-scale').value==='original';
    el('chart-scale-note').textContent=original
      ? 'Setiap grafik memiliki satuan sendiri. Baca tanggal dari kiri ke kanan dan nilai pada sumbu kiri. Angka pada kartu di atas adalah nilai terakhir, bukan total seluruh periode.'
      : 'Mode gabungan hanya untuk melihat pola naik dan turun. Pada setiap garis, 0 berarti nilai terendah dan 100 nilai tertinggi selama periode pilihan; garis yang tetap berada di 50 berarti nilainya tidak berubah. Angka 0 tidak selalu berarti tidak ada penjualan atau stok. Tinggi garis yang berbeda tidak menunjukkan jumlah yang sama. Kartu di atas tetap menampilkan nilai asli terakhir.';
    const panelHeight=230, count=original?Math.max(1,selected.length):1, svgWidth=Math.max(300,chartWidth), plotWidth=svgWidth-80;
    svg.setAttribute('viewBox','0 0 '+svgWidth+' '+(count*panelHeight+30));
    svg.append(node('title',{},'Perbandingan tren, sentimen, penjualan dan stok '+label(category.name)),
      node('desc',{},original?'Panel nilai asli dengan sumbu berbeda.':'Setiap seri diskalakan sendiri dari minimum ke maksimum periode menjadi 0–100. Tabel memuat nilai asli.'));
    if(!rows.length||!selected.length){svg.append(node('text',{x:50,y:90,fill:'var(--muted)'},'Pilih minimal satu seri untuk menampilkan grafik.'));el('trend-comparisons').replaceChildren();return;}
    const x=i=>52+(rows.length===1?plotWidth/2:i/(rows.length-1)*plotWidth);
    const drawAxis=(offset,lo,hi,title)=>{
      svg.append(node('text',{x:52,y:offset+16,fill:'var(--text)','font-size':14},title));
      for(const f of [0,.25,.5,.75,1]){
        const y=offset+35+155*(1-f),value=lo+(hi-lo)*f;
        svg.append(node('line',{x1:52,x2:svgWidth-28,y1:y,y2:y,stroke:'var(--rule)'}),node('text',{x:44,y:y+4,'text-anchor':'end',fill:'var(--muted)','font-size':12},new Intl.NumberFormat('id-ID',{notation:Math.abs(value)>=10000?'compact':'standard',maximumFractionDigits:1}).format(value)));
      }
      [...new Set([0,Math.floor((rows.length-1)/2),rows.length-1])].forEach(i=>{
        const labelDate=svgWidth<600?new Intl.DateTimeFormat('id-ID',{day:'numeric',month:'short'}).format(new Date(rows[i].week_start)):date(rows[i].week_start);
        svg.append(node('text',{x:x(i),y:offset+215,'text-anchor':i===0?'start':i===rows.length-1?'end':'middle',fill:'var(--muted)','font-size':12},labelDate));
      });
    };
    if(!original)drawAxis(0,0,100,'Skala perbandingan 0–100 per seri');
    selected.forEach((spec,panel)=>{
      const values=rows.map(r=>r[spec.key]).filter(v=>v!==null),offset=original?panel*panelHeight:0;
      const minimum=values.length?Math.min(...values):0,maximum=values.length?Math.max(...values):1;
      const lo=original?(spec.key==='sentiment_score'?-1:0):0;
      const hi=original?(spec.key==='sentiment_score'?1:spec.key==='interest_index'?100:Math.max(1,maximum*1.08)):100;
      if(original)drawAxis(offset,lo,hi,spec.label+' ('+spec.unit+')');
      const scaled=v=>original?v:maximum===minimum?50:100*(v-minimum)/(maximum-minimum);
      const y=v=>offset+35+155*(1-(scaled(v)-lo)/(hi-lo));
      if(original&&spec.key==='sentiment_score')svg.append(node('line',{x1:52,x2:svgWidth-28,y1:y(0),y2:y(0),stroke:'var(--muted)','stroke-dasharray':'3 4'}));
      let segment=[];
      function finish(){if(segment.length){svg.append(node('polyline',{'data-series':spec.key,points:segment.join(' '),fill:'none',stroke:spec.color,'stroke-width':2.5,'stroke-dasharray':spec.dash,'stroke-linejoin':'round','vector-effect':'non-scaling-stroke'}));segment=[];}}
      rows.forEach((row,i)=>{
        const value=row[spec.key];if(value===null){finish();return;}
        segment.push(x(i)+','+y(value));
      });finish();
      let previous=null;
      rows.forEach((row,i)=>{
        const value=row[spec.key];if(value===null){previous=null;return;}
        const summary=date(row.week_start)+' — '+spec.label+': '+(spec.key==='stock_value_idr'?moneyIDR(value):format(value)+' '+spec.unit);
        const group=node('g',{class:'trend-point',role:'button',tabindex:0,'aria-label':summary,'data-point-series':spec.key,'data-point-index':i});
        group.append(node('title',{},summary),
          node('circle',{cx:x(i),cy:y(value),r:12,fill:'transparent'}),
          node('circle',{class:'point-ring',cx:x(i),cy:y(value),r:8,fill:'none',stroke:spec.color,'stroke-width':2}),
          node('circle',{class:'point-marker',cx:x(i),cy:y(value),r:3.5,fill:spec.color}));
        const point={spec,row,value,x:x(i),y:y(value),element:group};chartPoints.push(point);
        if(previous)chartSegments.push({left:previous,right:point});previous=point;
        group.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();showPoint(point);}});
        group.addEventListener('focus',()=>showPoint(point));
        svg.append(group);
      });
    });
    svg.onclick=event=>{
      const mouse=svg.createSVGPoint();mouse.x=event.clientX;mouse.y=event.clientY;
      const matrix=svg.getScreenCTM(),position=mouse.matrixTransform(matrix.inverse());
      const tolerance=14/Math.hypot(matrix.a,matrix.b);
      let point=null,best=Infinity;
      for(const candidate of chartPoints){const distance=Math.hypot(position.x-candidate.x,position.y-candidate.y);if(distance<best){best=distance;point=candidate;}}
      if(best<=tolerance){showPoint(point);return;}
      let nearest=null;best=Infinity;
      for(const {left,right} of chartSegments){
        const dx=right.x-left.x,dy=right.y-left.y;
        const t=Math.max(0,Math.min(1,((position.x-left.x)*dx+(position.y-left.y)*dy)/(dx*dx+dy*dy)));
        const distance=Math.hypot(position.x-left.x-t*dx,position.y-left.y-t*dy);
        if(distance<best){best=distance;nearest=t<=.5?left:right;}
      }
      if(nearest&&best<=tolerance)showPoint(nearest,true);else hidePoint();
    };
    const comparison=el('trend-comparisons');comparison.replaceChildren();
    const chosen=selected.map(s=>s.key);
    category.comparisons.filter(c=>chosen.includes(c.left)&&chosen.includes(c.right)).forEach(c=>{
      const tr=document.createElement('tr');
      [specs.find(s=>s.key===c.left).label+' ↔ '+specs.find(s=>s.key===c.right).label,c.direction,c.r===null?'—':c.r.toFixed(3),String(c.paired_changes)].forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.append(td);});comparison.append(tr);
    });
    if(!comparison.children.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=4;td.textContent='Pilih minimal dua seri untuk membandingkan arah.';tr.append(td);comparison.append(tr);}
  }
  function render() {
    if (!data) return;
    const category = data.categories.find(c => c.category_id === Number(el('trend-category').value)) || data.categories[0];
    const pair=category.comparisons.find(c=>c.left==='interest_index'&&c.right==='sales_units');
    el('trend-finding').textContent=!pair||pair.r===null?'Data belum cukup untuk menilai hubungan perubahan minat pasar dan penjualan.':
      (pair.direction==='hubungan lemah'?'Pada periode ini, kenaikan atau penurunan minat pasar belum diikuti perubahan penjualan yang konsisten.':
      pair.direction==='cenderung sejalan'?'Pada periode ini, perubahan minat pasar dan penjualan cenderung searah.':'Pada periode ini, perubahan minat pasar dan penjualan cenderung berlawanan arah.')+
      ' Hubungan ini tidak membuktikan bahwa tren pasar menyebabkan perubahan penjualan.';
    const latest=category.series.at(-1);
    el('sentiment-batch-note').textContent=latest?.sentiment_period_start
      ? 'Sentimen terakhir: '+latest.social_post_count+' penyebutan menu dari minggu mulai '+date(latest.sentiment_period_start)+'. Data tersedia sejak '+date(latest.sentiment_available_at)+'. Jumlah penyebutan yang sedikit dapat membuat skor lebih mudah berubah.'
      : 'Sentimen mingguan belum tersedia untuk pengamatan terakhir.';
    specs.forEach(s=>{el('legend-'+s.key).textContent=!latest||latest[s.key]==null?'—':s.key==='stock_value_idr'?moneyIDR(latest[s.key]):format(latest[s.key]);});
    window.CafeStockUI?.syncURL();
    el('trend-latest').textContent = format(category.latest_index) + ' / 100';
    el('trend-weekly').textContent = points(category.weekly_change_points);
    el('trend-monthly').textContent = points(category.four_week_change_points);
    el('trend-direction').textContent = category.direction;
    el('trend-status').textContent = 'Data tersedia sampai ' + date(category.latest_available_at) +
      ' • ' + category.series.length + ' observasi mingguan • ' + data.source + '.';
    el('trend-insight').textContent = category.four_week_change_points === null ?
      'Belum cukup data untuk membandingkan dua periode empat minggu.' :
      'Rata-rata indeks ' + label(category.name).toLowerCase() + ' empat minggu terakhir ' + format(category.four_week_mean) +
      ', dibanding ' + format(category.prior_four_week_mean) + ' pada empat minggu sebelumnya (' +
      points(category.four_week_change_points) + '). Arah minat ' + category.direction +
      '. Gunakan bersama stok dan perkiraan kebutuhan; perubahan indeks bukan jumlah bahan yang harus dibeli.';
    el('trend-menus').textContent = category.menus.join(', ') || 'Belum ada pemetaan menu.';
    el('trend-ingredients').textContent = category.ingredients.join(', ') || 'Belum ada pemetaan bahan.';
    el('trend-model').textContent = 'F1 test risiko stok: operasional ' + data.model_comparison.operational_f1.toFixed(4) +
      '; operasional + tren ' + data.model_comparison.with_trend_f1.toFixed(4) +
      '. Pada eksperimen ini, penambahan tren saja belum meningkatkan F1. Indeks tidak membuktikan sebab-akibat permintaan.';
    // Derive the interpretation from the measured comparison if artifacts change.
    if (data.model_comparison.with_trend_f1 > data.model_comparison.operational_f1)
      el('trend-model').textContent = 'F1 test risiko stok: operasional ' + data.model_comparison.operational_f1.toFixed(4) +
        '; operasional + tren ' + data.model_comparison.with_trend_f1.toFixed(4) +
        '. Penambahan tren meningkatkan F1 pada eksperimen ini; hasil ini tidak membuktikan sebab-akibat permintaan.';
    const body = el('trend-values'); body.replaceChildren();
    category.series.forEach(row => {
      const tr = document.createElement('tr');
      [date(row.week_start), format(row.interest_index), format(row.sentiment_score), row.social_post_count ? String(row.social_post_count)+' penyebutan; '+date(row.sentiment_available_at) : 'Belum tersedia', format(row.sales_units), row.stock_value_idr===null?'Belum tersedia':moneyIDR(row.stock_value_idr)].forEach(value => {
        const td = document.createElement('td'); td.textContent = value; tr.append(td);
      }); body.append(tr);
    });
    draw(category);
  }
  async function load() {
    hidePoint();
    const ticket = ++requestNumber;
    el('trend-status').textContent = 'Memuat analisis tren…';
    el('trends-panel').setAttribute('aria-busy','true');el('retry-trends').hidden=true;
    try {
      const response = await fetch('/api/trends?branch=' + el('branch').value + '&weeks=' + el('trend-period').value);
      const result = await response.json();
      if (!response.ok) throw Error(result.error || 'Data tren belum tersedia.');
      if (ticket !== requestNumber) return;
      data = result;
      const selected = firstLoad ? (initial.get('category') || el('trend-category').value) : el('trend-category').value;firstLoad=false;
      el('trend-category').replaceChildren();
      data.categories.forEach(c => {
        const option = document.createElement('option'); option.value = c.category_id; option.textContent = label(c.name);
        el('trend-category').append(option);
      });
      if (data.categories.some(c => String(c.category_id) === selected)) el('trend-category').value = selected;
      render();
    } catch (error) {
      if (ticket === requestNumber) {
        hidePoint();
        data = null; el('trend-status').textContent = 'Analisis tren tidak berhasil dimuat. Coba muat tren kembali.';
        el('retry-trends').hidden=false;
        for(const id of ['trend-latest','trend-weekly','trend-monthly','trend-direction','trend-menus','trend-ingredients'])el(id).textContent='—';
        specs.forEach(s=>el('legend-'+s.key).textContent='—');
        el('trend-finding').textContent='Data perbandingan belum tersedia.';
        el('sentiment-batch-note').textContent='';
        el('trend-insight').textContent='';el('trend-model').textContent='';
        el('trend-chart').replaceChildren(); el('trend-values').replaceChildren();el('trend-comparisons').replaceChildren();
      }
    } finally {if(ticket===requestNumber)el('trends-panel').setAttribute('aria-busy','false');}
  }
  if(['4','12','26','52'].includes(initial.get('weeks')))el('trend-period').value=initial.get('weeks');
  if(['compare','original'].includes(initial.get('scale')))el('trend-scale').value=initial.get('scale');
  if(initial.has('series'))specs.forEach(s=>el('series-'+s.key).checked=initial.get('series').split(',').includes(s.key));
  new ResizeObserver(entries=>{const width=Math.round(entries[0].contentRect.width);if(width>0&&width!==chartWidth){chartWidth=width;if(data)draw(data.categories.find(c=>c.category_id===Number(el('trend-category').value))||data.categories[0]);}}).observe(el('trend-chart').parentElement);
  window.addEventListener('cafestock:view',()=>{if(data)render();});
  el('retry-trends').addEventListener('click',load);
  el('trend-scale').addEventListener('change',render);
  specs.forEach(s=>el('series-'+s.key).addEventListener('change',render));
  el('branch').addEventListener('change', load);
  el('trend-period').addEventListener('change', load);
  el('trend-category').addEventListener('change', render);
  load();
})();
