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

async function login() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value.trim();
  const res = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password })});
  const data = await res.json();
  if (data.ok) {
    localStorage.setItem('token', data.token);
    showToast('Login successful', true);
    setTimeout(() => { window.location.href = '/dashboard'; }, 500);
  } else {
    showToast('Invalid credentials', false);
  }
}

document.getElementById('loginBtn').addEventListener('click', login);

