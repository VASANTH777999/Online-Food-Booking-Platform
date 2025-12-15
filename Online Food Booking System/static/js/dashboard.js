function showToast(msg, ok = true) {
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

async function load() {
  const token = localStorage.getItem('token') || 'guest';
  const me = await fetch(`/api/me?token=${encodeURIComponent(token)}`).then(r => r.json());
  const restaurants = await fetch('/api/restaurants').then(r => r.json());
  const bookings = await fetch(`/api/bookings?user=${encodeURIComponent(token)}`).then(r => r.json());

  document.getElementById('userName').textContent = (me.profile && me.profile.name) || token;
  document.getElementById('userEmail').textContent = (me.profile && me.profile.email) || '';
  document.getElementById('countRestaurants').textContent = (restaurants.data || []).length;
  const list = bookings.data || [];
  document.getElementById('countBookings').textContent = list.length;
  const container = document.getElementById('bookingsList');
  container.innerHTML = '';
  list.slice(0, 10).forEach(b => {
    const div = document.createElement('div');
    div.className = 'bg-white rounded border p-3';
    div.innerHTML = `<div class="font-medium">${b.name}</div><div class="text-xs text-slate-600">${b.when}</div>`;
    container.appendChild(div);
  });
  const slider = document.getElementById('restaurantsSlider');
  if (slider) {
    const names = (restaurants.data || []).slice(0, 8).map(r => r.Restaurant || r.Name || '');
    let i = 0;
    slider.textContent = names[0] || '—';
    setInterval(() => {
      slider.textContent = names[(i++ % names.length)] || '—';
    }, 2000);
  }
}

async function logout() {
  const token = localStorage.getItem('token') || '';
  try {
    await fetch('/api/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    });
  } catch (err) {
    console.error('Logout error:', err);
  }
  localStorage.removeItem('token');
  showToast('Logged out successfully', true);
  setTimeout(() => { window.location.href = '/login'; }, 500);
}

// Bind logout button
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
  logoutBtn.addEventListener('click', logout);
}

// header has only Back to Dashboard per requirements

load();

