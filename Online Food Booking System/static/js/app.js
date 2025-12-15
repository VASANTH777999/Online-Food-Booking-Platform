const state = {
  items: [],
  filtered: [],
  bookings: [],
};

async function fetchRestaurants() {
  const res = await fetch('/api/restaurants');
  const data = await res.json();
  state.items = data.data || [];
  state.filtered = state.items;
  renderChips();
  renderList();
  applyAuthUI();
}

function renderList() {
  const list = document.getElementById('list');
  list.innerHTML = '';
  state.filtered.slice(0, 60).forEach((r) => {
    const card = document.createElement('div');
    card.className = 'rounded border bg-white p-0 shadow-sm flex flex-col overflow-hidden';
    const name = r.Restaurant || r.Name || 'Unknown';
    const cost = r.Cost ? `₹${r.Cost}` : '—';
    const cuisines = r.Cuisines || '';
    const rating = r.Rating ? Number(r.Rating).toFixed(1) : '—';
    const bannerId = 'b_' + Math.random().toString(36).slice(2);
    const review = r.Review || '';
    card.innerHTML = `
      <div class="h-20 bg-gradient-to-r from-indigo-500 via-fuchsia-500 to-rose-500 text-white px-4 py-3 flex items-center justify-between">
        <div class="font-semibold">${name}</div>
        <span class="text-xs bg-white/20 px-2 py-1 rounded">★ ${rating}</span>
      </div>
      <div class="px-4 pt-3 flex items-start justify-between">
        <div>
          <p class="text-sm text-slate-600">${cuisines}</p>
        </div>
      </div>
      <div class="px-4 mt-2 text-sm text-slate-700">Avg Cost: ${cost}</div>
      <div class="px-4 mt-2 text-xs text-slate-500">${r.Timings || ''}</div>
      <div id="${bannerId}" class="px-4 mt-3 text-sm text-slate-700 italic">${review}</div>
      <div class="mt-3 flex items-center gap-2 px-4 pb-3">
        <a href="${r.Links || '#'}" target="_blank" class="text-indigo-600 text-sm">View</a>
        <button class="ml-auto bg-indigo-600 text-white text-sm px-3 py-1 rounded">Book</button>
      </div>
    `;
    card.querySelector('button').addEventListener('click', () => book(name, r));
    list.appendChild(card);
    const texts = [review, cuisines, r.address || ''];
    let idx = 0;
    setInterval(() => {
      const el = document.getElementById(bannerId);
      if (el) el.textContent = texts[idx++ % texts.length];
    }, 2500);
  });
}

async function book(name, r) {
  const user = localStorage.getItem('token') || 'guest';
  const payload = { user, name, when: new Date().toISOString(), item: r };
  const res = await fetch('/api/book', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)});
  const data = await res.json();
  if (data.status === 'booked') {
    state.bookings.unshift(payload);
    alert(`Booked: ${name}`);
  } else {
    alert('Booking failed');
  }
}

function filterList(q) {
  const s = (q || '').toLowerCase();
  state.filtered = state.items.filter((r) => {
    const name = (r.Restaurant || r.Name || '').toLowerCase();
    const cuisines = (r.Cuisines || '').toLowerCase();
    return name.includes(s) || cuisines.includes(s);
  });
  renderList();
}

function showToast(msg, ok=true) {
  let t = document.getElementById('toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'toast';
    t.className = 'fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded shadow-lg text-white';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.className = 'fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded shadow-lg text-white ' + (ok ? 'bg-emerald-600' : 'bg-rose-600');
  t.style.opacity = '1';
  setTimeout(() => { t.style.opacity = '0'; }, 2000);
}

// verifyLogin removed; login handled via /login page and sessions

function renderBookingsPanel() {
  const panel = document.getElementById('bookingsPanel');
  const list = document.getElementById('bookingsList');
  list.innerHTML = '';
  state.bookings.forEach((b) => {
    const div = document.createElement('div');
    div.className = 'border rounded p-2';
    div.innerHTML = `<div class="font-medium">${b.name}</div><div class="text-xs text-slate-600">${b.when} • ${b.user}</div>`;
    list.appendChild(div);
  });
  panel.classList.remove('hidden');
  panel.classList.add('flex');
}

function hideBookingsPanel() {
  const panel = document.getElementById('bookingsPanel');
  panel.classList.add('hidden');
  panel.classList.remove('flex');
}

function bindUI() {
  document.getElementById('searchInput').addEventListener('input', (e) => filterList(e.target.value));
  document.getElementById('refreshBtn').addEventListener('click', fetchRestaurants);
  document.getElementById('viewBookingsBtn').addEventListener('click', renderBookingsPanel);
  document.getElementById('closeBookings').addEventListener('click', hideBookingsPanel);
}

function renderChips() {
  const chips = document.getElementById('chips');
  chips.innerHTML = '';
  const set = new Set();
  state.items.forEach((r) => {
    const c = (r.Cuisines || '').split(',').map(s => s.trim()).filter(Boolean);
    c.forEach(x => set.add(x));
  });
  Array.from(set).slice(0, 10).forEach((c) => {
    const b = document.createElement('button');
    b.className = 'text-sm px-3 py-1 rounded-full border hover:bg-indigo-50 hover:border-indigo-300';
    b.textContent = c;
    b.addEventListener('click', () => {
      const s = c.toLowerCase();
      state.filtered = state.items.filter((r) => (r.Cuisines || '').toLowerCase().includes(s));
      renderList();
    });
    chips.appendChild(b);
  });
}

bindUI();
fetchRestaurants();
async function applyAuthUI() {
  const token = localStorage.getItem('token') || '';
  if (!token) return;
  let me = null;
  try { me = await fetch(`/api/me?token=${encodeURIComponent(token)}`).then(r=>r.json()); } catch {}
  const title = document.getElementById('titleCenter');
  const btnSignup = document.getElementById('btnSignup');
  const btnLogin = document.getElementById('btnLogin');
  const btnDashboard = document.getElementById('btnDashboard');
  const btnBackDashboard = document.getElementById('btnBackDashboard');
  if (me && me.profile) {
    title.textContent = `Welcome, ${me.profile.name}`;
    btnSignup && (btnSignup.style.display = 'none');
    btnLogin && (btnLogin.style.display = 'none');
    btnDashboard && (btnDashboard.style.display = 'none');
    btnBackDashboard && btnBackDashboard.classList.remove('hidden');
  }
}
