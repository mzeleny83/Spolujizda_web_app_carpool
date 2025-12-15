let currentUserId = null;

function showSection(sectionId) {
  const sections = ['loginSection','registerSection','userSection','offerRideSection','searchRideSection','myRidesSection','myReservationsSection','allRidesSection','mapSection'];
  sections.forEach(id => document.getElementById(id).classList.add('hidden'));
  document.getElementById(sectionId).classList.remove('hidden');
  if (sectionId === 'mapSection' && typeof initMap === 'function') {
    initMap();
    loadMapRides();
  }
}

function normalizePhone(raw) {
  return (raw || '').trim().replace(/\s+/g, '');
}

function loginUser() {
  const phone = normalizePhone(document.getElementById('loginPhone').value);
  const password = document.getElementById('loginPassword').value;
  const resultDiv = document.getElementById('loginResult');
  resultDiv.innerHTML = '<span class="info">P?ihla?uji...</span>';

  fetch('/api/users/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, password })
  })
    .then(r => r.json())
    .then(data => {
      if (data.user_id) {
        currentUserId = data.user_id;
        document.getElementById('userInfo').innerHTML = `<strong>${data.name}</strong><br>Hodnocen?: ${data.rating}/5<br>Telefon: ${phone}`;
        document.getElementById('loginResult').innerHTML = '';
        showSection('userSection');
      } else {
        resultDiv.innerHTML = `<span class="error">${data.error || 'Chyba p?ihl??en?'}</span>`;
      }
    })
    .catch(() => { resultDiv.innerHTML = '<span class="error">Chyba p?ipojen?</span>'; });
}

function logoutUser() {
  currentUserId = null;
  showSection('loginSection');
}

function submitRegistration() {
  const name = document.getElementById('regName').value.trim();
  const phone = normalizePhone(document.getElementById('regPhone').value);
  const email = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPassword').value;
  const passwordConfirm = document.getElementById('regPasswordConfirm').value;
  const resultDiv = document.getElementById('registerResult');

  if (!name || !phone || !password) return resultDiv.innerHTML = '<span class="error">Vypl?te jm?no, telefon a heslo.</span>';
  if (password.length < 6) return resultDiv.innerHTML = '<span class="error">Heslo mus? m?t alespo? 6 znak?.</span>';
  if (password !== passwordConfirm) return resultDiv.innerHTML = '<span class="error">Hesla se neshoduj?.</span>';
  if (!/^\+?\d{9,15}$/.test(phone)) return resultDiv.innerHTML = '<span class="error">Telefon ve tvaru +420... (9-15 ??slic).</span>';

  resultDiv.innerHTML = '<span class="info">Registruji...</span>';

  fetch('/api/users/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, phone, email, password })
  })
    .then(res => res.json().then(body => ({ status: res.status, body })))
    .then(({ status, body }) => {
      if (status === 201 && body.user_id) {
        document.getElementById('loginPhone').value = phone;
        document.getElementById('loginPassword').value = password;
        document.getElementById('loginResult').innerHTML = '<span class="success">??et vytvo?en, p?ihlaste se.</span>';
        resultDiv.innerHTML = '';
        showSection('loginSection');
      } else {
        resultDiv.innerHTML = `<span class="error">${body.error || 'Chyba registrace'}</span>`;
      }
    })
    .catch(() => { resultDiv.innerHTML = '<span class="error">Chyba p?ipojen?</span>'; });
}

function offerRide() {
  if (!currentUserId) return alert('Nejd??ve se p?ihlaste.');
  const payload = {
    driver_id: currentUserId,
    from_location: document.getElementById('offerFrom').value,
    to_location: document.getElementById('offerTo').value,
    departure_time: document.getElementById('offerDateTime').value,
    available_seats: parseInt(document.getElementById('offerSeats').value || '1', 10),
    price: parseInt(document.getElementById('offerPrice').value || '0', 10),
    description: document.getElementById('offerNote').value
  };
  const resultDiv = document.getElementById('offerResult');
  if (!payload.from_location || !payload.to_location || !payload.departure_time) {
    resultDiv.innerHTML = '<span class="error">Vypl?te v?echna povinn? pole.</span>';
    return;
  }
  fetch('/api/rides/offer', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  }).then(r => r.json()).then(data => {
    if (data.ride_id) {
      resultDiv.innerHTML = '<span class="success">J?zda nab?dnuta.</span>';
    } else { resultDiv.innerHTML = `<span class="error">${data.error || 'Chyba nab?dky'}</span>`; }
  }).catch(() => resultDiv.innerHTML = '<span class="error">Chyba p?ipojen?</span>');
}

function renderRideCard(ride) {
  return `<div class="ride">
    <strong>${ride.from_location} ? ${ride.to_location}</strong><br>
    ?idi?: ${ride.driver_name || ''} | ?as: ${ride.departure_time || ''}<br>
    Cena: ${ride.price_per_person || ride.price || 0} K? | Voln? m?sta: ${ride.available_seats || ''}
    ${ride.description ? `<br>${ride.description}` : ''}
    ${currentUserId && ride.id ? `<div style="margin-top:6px;"><button onclick="reserveRide(${ride.id})">Rezervovat</button></div>` : ''}
  </div>`;
}

function searchRides() {
  const from = document.getElementById('searchFrom').value;
  const to = document.getElementById('searchTo').value;
  const params = new URLSearchParams();
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  const url = params.toString() ? `/api/rides/search?${params}` : '/api/rides/search';
  const container = document.getElementById('searchResults');
  fetch(url).then(r => r.json()).then(rides => {
    container.innerHTML = rides.length ? rides.map(renderRideCard).join('') : '<p>??dn? j?zdy.</p>';
  }).catch(() => container.innerHTML = '<p class="error">Chyba na?ten?.</p>');
}

function showAllRides() {
  fetch('/api/rides/search').then(r => r.json()).then(rides => {
    document.getElementById('allRidesList').innerHTML = rides.length ? rides.map(renderRideCard).join('') : '<p>??dn? j?zdy.</p>';
    showSection('allRidesSection');
  }).catch(() => document.getElementById('allRidesList').innerHTML = '<p class="error">Chyba na?ten?.</p>');
}

function showMyRides() {
  if (!currentUserId) return;
  fetch(`/api/rides/my?user_id=${currentUserId}`).then(r => r.json()).then(rides => {
    document.getElementById('myOffers').innerHTML = rides.length ? rides.map(renderRideCard).join('') : '<p>Nem?te ??dn? j?zdy.</p>';
    showSection('myRidesSection');
  }).catch(() => document.getElementById('myOffers').innerHTML = '<p class="error">Chyba na?ten?.</p>');
}

function showMyReservations() {
  if (!currentUserId) return;
  fetch(`/api/reservations?user_id=${currentUserId}`).then(r => r.json()).then(res => {
    document.getElementById('myBookings').innerHTML = res.length ? res.map(renderRideCard).join('') : '<p>Nem?te rezervace.</p>';
    showSection('myReservationsSection');
  }).catch(() => document.getElementById('myBookings').innerHTML = '<p class="error">Chyba na?ten?.</p>');
}

function reserveRide(id) {
  if (!currentUserId) return alert('Nejd??ve se p?ihlaste.');
  fetch('/api/rides/reserve', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ride_id: id, passenger_id: currentUserId, seats_reserved: 1 })
  }).then(r => r.json()).then(data => {
    if (data.reservation_id) alert('Rezervace potvrzena.'); else alert(data.error || 'Chyba rezervace');
  }).catch(() => alert('Chyba p?ipojen?'));
}

// Map functions (simplified)
let mapInstance = null;
let markers = [];

function initMap() {
  if (mapInstance) return;
  mapInstance = L.map('map').setView([49.75, 15.5], 7);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '? OpenStreetMap'
  }).addTo(mapInstance);
}

function cityCoords(name) {
  const lookup = {
    'Praha': [50.0755, 14.4378], 'Brno': [49.1951, 16.6068], 'Ostrava': [49.8209, 18.2625],
    'Plze?': [49.7384, 13.3736], 'Liberec': [50.7663, 15.0543], '?esk? Bud?jovice': [48.9745, 14.4742], 'Zl?n': [49.2265, 17.6679]
  };
  const entry = Object.entries(lookup).find(([city]) => (name || '').toLowerCase().includes(city.toLowerCase()));
  return entry ? entry[1] : null;
}

function loadMapRides() {
  if (!mapInstance) initMap();
  markers.forEach(m => mapInstance.removeLayer(m)); markers = [];
  fetch('/api/rides/search').then(r => r.json()).then(rides => {
    rides.forEach(ride => {
      const from = cityCoords(ride.from_location);
      const to = cityCoords(ride.to_location);
      if (from) {
        const m = L.marker(from).addTo(mapInstance).bindPopup(`${ride.from_location}<br>${ride.driver_name || ''}`);
        markers.push(m);
      }
      if (to) {
        const m = L.marker(to).addTo(mapInstance).bindPopup(`${ride.to_location}<br>${ride.driver_name || ''}`);
        markers.push(m);
      }
      if (from && to) {
        const line = L.polyline([from, to], { color: '#0066ff', weight: 3, opacity: 0.7 }).addTo(mapInstance);
        markers.push(line);
      }
    });
    document.getElementById('mapInfo').innerText = `Na?teno ${rides.length} j?zd.`;
  }).catch(() => document.getElementById('mapInfo').innerText = 'Chyba na?ten? j?zd.');
}

showSection('loginSection');
