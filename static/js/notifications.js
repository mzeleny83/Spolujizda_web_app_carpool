// Notifikační systém v358 - nový soubor
let shownNotifications = new Set();
let notificationInterval = null;

function startNotificationCheck() {
  console.log('NOTIF v358 - Starting notification check');
  if (notificationInterval) {
    clearInterval(notificationInterval);
  }
  
  checkForNotifications();
  notificationInterval = setInterval(checkForNotifications, 10000);
}

function stopNotificationCheck() {
  console.log('NOTIF v358 - Stopping notification check');
  if (notificationInterval) {
    clearInterval(notificationInterval);
    notificationInterval = null;
  }
}

async function checkForNotifications() {
  const currentUser = localStorage.getItem('currentUser');
  if (!currentUser) {
    console.log('NOTIF v358 - No current user');
    return;
  }
  
  try {
    const user = JSON.parse(currentUser);
    const url = `/api/notifications/${encodeURIComponent(user.name)}`;
    console.log('NOTIF v358 - Checking notifications for:', user.name);
    
    const response = await fetch(url);
    if (!response.ok) {
      console.error('NOTIF v358 - API error:', response.status, response.statusText);
      return;
    }
    
    const notifications = await response.json();
    console.log('NOTIF v358 - Got', notifications.length, 'notifications:', notifications);
    
    if (notifications.length > 0) {
      let newCount = 0;
      notifications.forEach(notification => {
        const notifId = `${notification.ride_id}-${notification.sender_name}-${notification.created_at}`;
        if (!shownNotifications.has(notifId)) {
          console.log('NOTIF v358 - NEW notification:', notification.sender_name, notification.message);
          showFloatingNotification(notification.sender_name, notification.message, notification.ride_id);
          shownNotifications.add(notifId);
          newCount++;
        }
      });
      
      if (newCount > 0) {
        console.log(`NOTIF v358 - Showed ${newCount} new notifications`);
      }
    }
  } catch (error) {
    console.error('NOTIF v358 - Error:', error);
  }
}

function showFloatingNotification(senderName, message, rideId) {
  console.log('NOTIFICATION v358 - Showing notification:', senderName, message, rideId);
  
  // Zvukový signál
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (e) {
    console.log('Audio notification failed:', e);
  }
  
  const notification = document.createElement('div');
  notification.innerHTML = `
    <div style="background: #4CAF50; color: white; padding: 15px; border-radius: 8px; margin: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-family: Arial, sans-serif;">
      <div style="font-weight: bold; margin-bottom: 5px;">📨 Nová zpráva!</div>
      <div style="margin-bottom: 5px;">Od: <strong>${senderName}</strong></div>
      <div style="margin-bottom: 10px; font-style: italic;">"${message}"</div>
      <button onclick="alert('Chat otevřen pro jízdu ${rideId}'); this.parentElement.parentElement.remove();" style="background: white; color: #4CAF50; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;">💬 Otevřít chat</button>
      <button onclick="this.parentElement.parentElement.remove()" style="background: rgba(255,255,255,0.3); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; margin-left: 5px;">×</button>
    </div>
  `;
  
  notification.style.cssText = 'position: fixed !important; top: 20px !important; right: 20px !important; z-index: 999999 !important; pointer-events: auto !important;';
  
  document.body.appendChild(notification);
  console.log('NOTIFICATION v358 - Notification added to DOM');
  
  setTimeout(() => {
    if (document.body.contains(notification)) {
      notification.remove();
    }
  }, 8000);
}

function testNotificationDisplay() {
  console.log('TEST v358 - Testing notification system');
  
  const currentUser = localStorage.getItem('currentUser');
  if (!currentUser) {
    alert('Musíte být přihlášeni pro test notifikací!');
    return;
  }
  
  showFloatingNotification('Test Uživatel', 'Testovací zpráva pro ověření notifikací', 999);
  checkForNotifications();
  
  const user = JSON.parse(currentUser);
  alert(`Test notifikací spuštěn pro uživatele: ${user.name}\n\nKontroluje se každých 10 sekund.`);
}

async function createTestMessage() {
  const currentUser = localStorage.getItem('currentUser');
  if (!currentUser) {
    alert('Musíte být přihlášeni pro test zpráv!');
    return;
  }
  
  const action = prompt('Vyberte akci:\n1 - Odeslat testovací zprávu\n2 - Zkontrolovat notifikace\n3 - Zobrazit test notifikaci\n\nZadejte číslo (1-3):');
  
  if (action === '1') {
    await sendTestMessage();
  } else if (action === '2') {
    await manualCheckNotifications();
  } else if (action === '3') {
    showFloatingNotification('Test Uživatel', `Testovací notifikace - ${new Date().toLocaleTimeString()}`, 999);
    alert('Testovací notifikace zobrazena!');
  }
}

async function sendTestMessage() {
  const currentUser = localStorage.getItem('currentUser');
  const user = JSON.parse(currentUser);
  
  try {
    const response = await fetch('/api/rides/search');
    const rides = await response.json();
    
    if (rides.length === 0) {
      alert('Nejsou k dispozici žádné jízdy pro test!');
      return;
    }
    
    const testRide = rides[0];
    const testMessage = `Test zpráva od ${user.name} - ${new Date().toLocaleTimeString()}`;
    
    const sendResponse = await fetch('/api/chat/send', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        ride_id: testRide.id,
        sender_name: user.name,
        message: testMessage
      })
    });
    
    if (sendResponse.ok) {
      alert(`✅ Testovací zpráva odeslána!\n\nJízda: ${testRide.from_location} → ${testRide.to_location}\nZpráva: "${testMessage}"\n\nNotifikace by se měly zobrazit ostatním účastníkům jízdy za 10 sekund.`);
    } else {
      const error = await sendResponse.json();
      alert('❌ Chyba při odesílání: ' + (error.error || 'Neznámá chyba'));
    }
  } catch (error) {
    alert('❌ Chyba: ' + error.message);
  }
}

async function manualCheckNotifications() {
  const currentUser = localStorage.getItem('currentUser');
  const user = JSON.parse(currentUser);
  
  try {
    console.log('MANUAL CHECK v358 - Checking notifications for:', user.name);
    const response = await fetch(`/api/notifications/${encodeURIComponent(user.name)}`);
    
    if (!response.ok) {
      alert(`❌ API chyba: ${response.status} ${response.statusText}`);
      return;
    }
    
    const notifications = await response.json();
    console.log('MANUAL CHECK v358 - Got notifications:', notifications);
    
    if (notifications.length === 0) {
      alert('📭 Žádné nové notifikace');
    } else {
      let message = `📨 Nalezeno ${notifications.length} notifikací:\n\n`;
      notifications.forEach((notif, index) => {
        message += `${index + 1}. Od: ${notif.sender_name}\n   Zpráva: "${notif.message}"\n   Jízda: ${notif.ride_id}\n   Čas: ${notif.created_at}\n\n`;
      });
      alert(message);
    }
  } catch (error) {
    alert('❌ Chyba při kontrole: ' + error.message);
  }
}

console.log('NOTIFICATIONS v358 - Loaded successfully');