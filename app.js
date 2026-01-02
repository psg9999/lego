"use strict";

const productsEl = document.getElementById('products');
const fileInput = document.getElementById('file-input');
const searchInput = document.getElementById('search');
const conditionFilter = document.getElementById('condition-filter');
const cartCountEl = document.getElementById('cart-count');
const downloadTemplateBtn = document.getElementById('download-template');
const exportOrderBtn = document.getElementById('export-order');
const clearCartBtn = document.getElementById('clear-cart');
const sortSelect = document.getElementById('sort');
const priceMinInput = document.getElementById('price-min');
const priceMaxInput = document.getElementById('price-max');
const viewCartBtn = document.getElementById('view-cart');
const cartOffcanvasEl = document.getElementById('cart-offcanvas');
const cartItemsEl = document.getElementById('cart-items');
const cartTotalEl = document.getElementById('cart-total');
const exportOrderBtn2 = document.getElementById('export-order-2');
const cartCountTop = document.getElementById('cart-count-top');

let products = [];
let cart = {}; // id -> {product, qty}
let currentPage = 1;
const pageSize = 24; // products per page
const paginationEl = document.getElementById('pagination');

function loadCart(){
  try{
    const raw = localStorage.getItem('lego_cart_v1');
    cart = raw ? JSON.parse(raw) : {};
  }catch(e){ cart = {}; }
  updateCartSummary();
}

function saveCart(){
  localStorage.setItem('lego_cart_v1', JSON.stringify(cart));
  updateCartSummary();
}

function updateCartSummary(){
  const total = Object.values(cart).reduce((s,i)=>s + (i.qty||0), 0);
  cartCountEl.textContent = total;
  if(cartCountTop) cartCountTop.textContent = total;
}

function normalizeRow(row){
  // Map common column names to our fields
  const map = {};
  for(const k of Object.keys(row)){
    const key = k.trim().toLowerCase();
    map[key] = row[k];
  }

  const id = map.id || map.sku || map.part || (map.title || '').slice(0,30);
  const title = map.title || map.name || '';
  const description = map.description || map.desc || '';
  const price = parseFloat((map.price||0).toString().replace(/[^0-9.-]+/g,'')) || 0;
  const quantity = parseInt(map.quantity || map.qty || map.count || 0) || 0;
  const msrp = parseFloat((map.msrp||map.list_price||0).toString().replace(/[^0-9.-]+/g,'')) || 0;
  const imageUrl = map.imageurl || map.image || map.img || '';
  const condition = (map.condition || '').toString().toLowerCase();

  return { id: id?.toString() || title, title, description, price, msrp, quantity, imageUrl, condition };
}

function renderProducts(list){
  productsEl.innerHTML = '';
  if(!list.length){
    productsEl.innerHTML = '<div class="col-12 text-muted">No items loaded. Upload a CSV/XLSX to begin.</div>';
    return;
  }
  // sort
  const sort = sortSelect ? sortSelect.value : 'title_asc';
  if(sort){
    list = list.slice();
    if(sort === 'title_asc') list.sort((a,b)=> (a.title||'').localeCompare(b.title||''));
    if(sort === 'title_desc') list.sort((a,b)=> (b.title||'').localeCompare(a.title||''));
    if(sort === 'price_asc') list.sort((a,b)=> (Number(a.price||0) - Number(b.price||0)) );
    if(sort === 'price_desc') list.sort((a,b)=> (Number(b.price||0) - Number(a.price||0)) );
  }

  for(const p of list){
    const col = document.createElement('div');
    col.className = 'col-sm-6 col-md-4 col-lg-3';

    const card = document.createElement('div');
    card.className = 'card product-card h-100';

    const img = document.createElement('img');
    img.className = 'card-img-top product-img p-3';
    img.alt = p.title;
  img.src = p.imageUrl || 'https://via.placeholder.com/300x150?text=No+Image';
  img.loading = 'lazy';
  img.onerror = ()=>{ img.src = 'https://via.placeholder.com/300x150?text=No+Image'; };
  if(p.rebrickablePage){ img.style.cursor = 'pointer'; img.onclick = ()=> window.open(p.rebrickablePage, '_blank'); }

    const body = document.createElement('div');
    body.className = 'card-body d-flex flex-column';

    const title = document.createElement('h5');
    title.className = 'card-title';
    title.textContent = p.title || 'Untitled';

    const desc = document.createElement('p');
    desc.className = 'card-text text-muted small mb-2';
    desc.textContent = p.description || '';

    const bottom = document.createElement('div');
    bottom.className = 'mt-auto d-flex justify-content-between align-items-center';

    const left = document.createElement('div');
    // display msrp if available and greater than sale price
    const sale = Number(p.price||0);
    const orig = Number(p.msrp||0);
    let priceHtml = '';
    if(orig && orig > 0 && sale > 0 && orig > sale){
      const margin = (orig - sale).toFixed(2);
      const pct = ((orig - sale) / orig * 100).toFixed(1);
      priceHtml = `<div class="price"><span class="text-muted text-decoration-line-through">$${orig.toFixed(2)}</span> <strong class="ms-2">$${sale.toFixed(2)}</strong></div><div class="small text-success">Margin: $${margin} (${pct}%)</div>`;
    }else if(orig && orig > 0 && (!sale || sale === 0)){
      priceHtml = `<div class="price">$${orig.toFixed(2)}</div>`;
    }else{
      priceHtml = `<div class="price">$${sale.toFixed(2)}</div>`;
    }
    left.innerHTML = `${priceHtml}<div class="small"><span class="badge badge-qty">Qty: ${p.quantity||0}</span> ${p.condition?'<span class="ms-2">'+p.condition+'</span>':''}</div>`;

  const right = document.createElement('div');
  // quantity input + add button
  const qtyIn = document.createElement('input');
  qtyIn.type = 'number'; qtyIn.min = 1; qtyIn.value = 1; qtyIn.style.width = '70px'; qtyIn.className = 'form-control form-control-sm me-2';
  const btn = document.createElement('button');
  btn.className = 'btn btn-sm btn-primary';
  btn.textContent = 'Add';
  btn.onclick = ()=>{ const q = Math.max(1, parseInt(qtyIn.value)||1); addToCart(p.id, q); };
  right.appendChild(qtyIn);
  right.appendChild(btn);

    bottom.appendChild(left);
    bottom.appendChild(right);

    body.appendChild(title);
    body.appendChild(desc);
    body.appendChild(bottom);

    card.appendChild(img);
    card.appendChild(body);
    col.appendChild(card);
    productsEl.appendChild(col);
  }

  // render pagination
  if(paginationEl){
    paginationEl.innerHTML = '';
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
    const makePageItem = (n, label, active)=>{
      const li = document.createElement('li');
      li.className = 'page-item' + (active ? ' active' : '');
      const a = document.createElement('a'); a.className='page-link'; a.href='#'; a.textContent = label || n;
      a.onclick = (e)=>{ e.preventDefault(); currentPage = n; renderProducts(filteredProducts()); };
      li.appendChild(a); return li;
    };
    // prev
    const prev = document.createElement('li'); prev.className = 'page-item' + (currentPage===1?' disabled':'');
    const pa = document.createElement('a'); pa.className='page-link'; pa.href='#'; pa.textContent='Prev'; pa.onclick=(e)=>{e.preventDefault(); if(currentPage>1){ currentPage--; renderProducts(filteredProducts());}}; prev.appendChild(pa); paginationEl.appendChild(prev);
    // pages (condensed)
    const start = Math.max(1, currentPage-2);
    const end = Math.min(totalPages, currentPage+2);
    for(let i=start;i<=end;i++) paginationEl.appendChild(makePageItem(i,i,i===currentPage));
    // next
    const next = document.createElement('li'); next.className = 'page-item' + (currentPage===totalPages?' disabled':'');
    const na = document.createElement('a'); na.className='page-link'; na.href='#'; na.textContent='Next'; na.onclick=(e)=>{e.preventDefault(); if(currentPage<totalPages){ currentPage++; renderProducts(filteredProducts());}}; next.appendChild(na); paginationEl.appendChild(next);
  }
}

function addToCart(id, qty=1){
  const p = products.find(x=>x.id==id);
  if(!p) return;
  if(!cart[id]) cart[id] = { product: p, qty: 0 };
  cart[id].qty += Number(qty);
  saveCart();
}

function setCartQty(id, qty){
  if(!cart[id]) return;
  if(qty <= 0){ delete cart[id]; } else { cart[id].qty = qty; }
  saveCart();
}

function removeFromCart(id){
  if(cart[id]){ delete cart[id]; saveCart(); }
}

function clearCart(){
  cart = {};
  saveCart();
}

function exportOrderCSV(){
  const rows = [['id','title','unit_price','qty','line_total']];
  for(const id of Object.keys(cart)){
    const entry = cart[id];
    const p = entry.product;
    const qty = entry.qty || 0;
    rows.push([p.id, p.title, Number(p.price||0).toFixed(2), qty, (Number(p.price||0)*qty).toFixed(2)]);
  }
  const csv = rows.map(r=>r.map(cell=>`"${String(cell).replace(/"/g,'""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'lego-order.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function renderCart(){
  cartItemsEl.innerHTML = '';
  const ids = Object.keys(cart);
  let total = 0;
  if(ids.length === 0){ cartItemsEl.innerHTML = '<div class="text-muted">Cart is empty</div>'; cartTotalEl.textContent = '0.00'; return; }
  for(const id of ids){
    const e = cart[id];
    const row = document.createElement('div');
    row.className = 'd-flex align-items-center mb-2';
    const title = document.createElement('div'); title.className = 'flex-grow-1'; title.textContent = `${e.product.title || id}`;
    const qtyInput = document.createElement('input'); qtyInput.type='number'; qtyInput.min=0; qtyInput.value = e.qty; qtyInput.style.width='80px'; qtyInput.className='form-control form-control-sm me-2';
    qtyInput.onchange = ()=>{ const v = parseInt(qtyInput.value)||0; setCartQty(id, v); renderCart(); };
    const price = Number(e.product.price||0);
    const line = document.createElement('div'); line.className='text-end me-2'; line.textContent = `$${(price*e.qty).toFixed(2)}`;
    const rem = document.createElement('button'); rem.className='btn btn-sm btn-outline-danger'; rem.textContent='Remove'; rem.onclick = ()=>{ removeFromCart(id); renderCart(); };
    row.appendChild(title); row.appendChild(qtyInput); row.appendChild(line); row.appendChild(rem);
    cartItemsEl.appendChild(row);
    total += price*e.qty;
  }
  cartTotalEl.textContent = Number(total).toFixed(2);
  updateCartSummary();
}

function downloadTemplate(){
  const header = ['id','title','description','price','msrp','quantity','imageUrl','condition'];
  const sample = ['1001','Red 2x4 Bricks (100pcs)','Mixed set of 100 red 2x4 bricks', '0.15', '0.20', '100','', 'used'];
  const csv = [header, sample].map(r=>r.join(',')).join('\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'lego-template.csv';
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}

function parseCSVFile(file){
  return new Promise((resolve, reject)=>{
    Papa.parse(file, {header:true, skipEmptyLines:true, complete: (res)=>{
      if(res.errors && res.errors.length) console.warn('CSV parse warnings', res.errors);
      const rows = res.data.map(normalizeRow);
      resolve(rows);
    }, error: reject});
  });
}

function parseXLSXFile(file){
  return new Promise((resolve,reject)=>{
    const reader = new FileReader();
    reader.onload = (e)=>{
      try{
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, {type:'array'});
        const first = workbook.SheetNames[0];
        const sheet = workbook.Sheets[first];
        const json = XLSX.utils.sheet_to_json(sheet, {defval:''});
        resolve(json.map(normalizeRow));
      }catch(err){ reject(err); }
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}

async function handleFile(file){
  const name = (file.name||'').toLowerCase();
  try{
    let rows = [];
    if(name.endsWith('.csv')){
      rows = await parseCSVFile(file);
    }else if(name.endsWith('.xlsx') || name.endsWith('.xls')){
      rows = await parseXLSXFile(file);
    }else{
      // try CSV fallback
      rows = await parseCSVFile(file);
    }
    products = rows;
    renderProducts(filteredProducts());
  }catch(err){
    console.error('Failed to parse file', err);
    alert('Error parsing spreadsheet: '+err.message);
  }
}

function filteredProducts(){
  const q = (searchInput.value||'').toLowerCase().trim();
  const condition = (conditionFilter.value||'').toLowerCase();
  return products.filter(p=>{
    if(condition && (p.condition||'').toLowerCase() !== condition) return false;
    const min = parseFloat(priceMinInput?.value||'') || null;
    const max = parseFloat(priceMaxInput?.value||'') || null;
    const price = Number(p.price||0);
    if(min !== null && !isNaN(min) && price < min) return false;
    if(max !== null && !isNaN(max) && price > max) return false;
    if(!q) return true;
    return (p.title||'').toLowerCase().includes(q) || (p.description||'').toLowerCase().includes(q);
  });
}

// wire events
fileInput.addEventListener('change', (e)=>{
  const f = e.target.files && e.target.files[0];
  if(f) handleFile(f);
});
searchInput.addEventListener('input', ()=> renderProducts(filteredProducts()));
conditionFilter.addEventListener('change', ()=> renderProducts(filteredProducts()));
downloadTemplateBtn.addEventListener('click', downloadTemplate);
exportOrderBtn.addEventListener('click', exportOrderCSV);
exportOrderBtn2.addEventListener('click', exportOrderCSV);
clearCartBtn.addEventListener('click', ()=>{ if(confirm('Clear cart?')){ clearCart(); renderCart(); }});
if(sortSelect) sortSelect.addEventListener('change', ()=> renderProducts(filteredProducts()));
if(priceMinInput) priceMinInput.addEventListener('input', ()=> renderProducts(filteredProducts()));
if(priceMaxInput) priceMaxInput.addEventListener('input', ()=> renderProducts(filteredProducts()));
if(viewCartBtn) viewCartBtn.addEventListener('click', ()=>{ if(cartOffcanvasEl){ const off = new bootstrap.Offcanvas(cartOffcanvasEl); renderCart(); off.show(); }});

// update cart UI on load
renderCart();

// init
loadCart();

// If a server-side-parsed products.json exists (we created one from your Excel file), load it automatically.
fetch('products.json').then(r=>{
  if(!r.ok) throw new Error('no products.json');
  return r.json();
}).then(j=>{
  products = j || [];
  // try to load rebrickable cache and inject images where available
  fetch('rebrickable_cache.json').then(rc=>{
    if(!rc.ok) return null;
    return rc.json();
  }).then(cache=>{
    if(cache){
      const map = cache;
      for(const p of products){
        const sid = (p.id||'').toString();
        const entry = map[sid];
        if(entry){
          // prefer explicit image_url if it looks like an image
          if(entry.image_url && (entry.image_url.endsWith('.jpg') || entry.image_url.endsWith('.png') || entry.image_url.endsWith('.jpeg'))){
            p.imageUrl = entry.image_url;
            p.rebrickablePage = entry.image_url;
          }else if(entry.set_num_found){
            // construct a likely CDN image URL: /media/sets/{prefix}/{set_num_found}.jpg
            const setnum = entry.set_num_found;
            const prefix = setnum.split('-')[0].slice(0,3);
            p.imageUrl = `https://cdn.rebrickable.com/media/sets/${prefix}/${setnum}.jpg`;
            p.rebrickablePage = `https://rebrickable.com/sets/${setnum}/`;
          }
        }
      }
    }
    renderProducts(filteredProducts());
  }).catch(()=>{
    renderProducts(filteredProducts());
  });
}).catch(err=>{
  // no products.json available; start with empty list
  console.info('products.json not found or failed to load — start with empty inventory');
  renderProducts([]);
});
