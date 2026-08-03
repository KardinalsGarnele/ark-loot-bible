const $=s=>document.querySelector(s), esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function params(){const p=new URLSearchParams();[['map_id','#map'],['source_group','#group'],['drop_color','#color'],['has_ring','#ring'],['required_level_min','#level'],['verification_status','#status']].forEach(([k,s])=>{const v=$(s).value;if(v!=='')p.set(k,v)});return p}
function pct(v){return v===null||v===undefined?'—':`${Number(v).toLocaleString('de-DE',{maximumFractionDigits:2})}%`}
async function load(){const p=params(),r=await fetch(`/api/v1/loot-matrix?${p}`),d=await r.json();$('#summary').textContent=`${d.row_count} Zeilen · Sortierung: Map, Farbe, Ring, Level`;$('#csv').href=`/api/v1/loot-matrix/export.csv?${p}`;$('#json').href=`/api/v1/loot-matrix/export.json?${p}`;$('#rows').innerHTML=d.rows.length?d.rows.map(x=>`<tr>
<td>${esc(x.map_name)}</td>
<td><span class="pill ${esc(x.drop_color)}">${esc(x.drop_color)}</span>${x.has_ring===1?'<span class="pill">Ring</span>':x.has_ring===0?'<span class="pill muted">No Ring</span>':'<span class="pill muted">Unknown</span>'}</td>
<td>${esc(x.required_level)}</td>
<td><span class="pill">${esc(x.source_group)}</span><br><strong>${esc(x.loot_source_name)}</strong><div class="muted">${esc(x.loot_set_name)}</div></td>
<td><strong>${esc(x.blueprint_name||x.item_name||x.loot_entry_name)}</strong><div class="muted">${esc(x.loot_entry_name)}</div></td>
<td>${pct(x.source_quality_min_percent)} – ${pct(x.source_quality_max_percent)}</td>
<td>${pct(x.item_quality_multiplier_percent)}</td>
<td><strong>${pct(x.calculated_quality_min_percent)} – ${pct(x.calculated_quality_max_percent)}</strong></td>
<td>${esc(x.loot_entry_verification_status)}</td></tr>`).join(''):'<tr><td colspan="9">Keine Treffer.</td></tr>'}
$('#apply').onclick=load;fetch('/health').then(r=>r.json()).then(x=>$('#version').textContent=`v${x.version}`);load();