// Chat functions for ride sharing app v361
let chatMap, routeWaypoints = [], routeMarkers = [], routeLine = null, userMarker = null;

// NOTIFIKAČNÍ SYSTÉM v361 - OPRAVENO ZOBRAZOVÁNÍ
console.log('SCRIPT v361 - Loading fixed notification system');

// Track shown notifications
let shownNotifications = new Set();
let notificationInterval = null;

function startNotificationCheck() {
  console.log('NOTIF v361 - Starting notification check');
  if (notificationInterval) {
    clearInterval(notificationInterval);
  }
  checkForNotifications();
  notificationInterval = setInterval(checkForNotifications, 10000);
}

function stopNotificationCheck() {
  console.log('NOTIF v361 - Stopping notification check');
  if (notificationInterval) {
    clearInterval(notificationInterval);
    notificationInterval = null;
  }
}

async function checkForNotifications() {
  const currentUser = localStorage.getItem('currentUser');
  if (!currentUser) {
    console.log('NOTIF v361 - No current user');
    return;
  }
  
  try {
    const user = JSON.parse(currentUser);
    const url = `/api/notifications/v361/${encodeURIComponent(user.name)}`;
    console.log('NOTIF v361 - Checking notifications for:', user.name, 'URL:', url);
    
    const response = await fetch(url);
    if (!response.ok) {
      console.error('NOTIF v361 - API error:', response.status, response.statusText);
      return;
    }
    
    const notifications = await response.json();
    console.log('NOTIF v361 - Got', notifications.length, 'notifications:', notifications);
    
    if (notifications.length > 0) {
      let newCount = 0;
      notifications.forEach(notification => {
        const notifId = `${notification.ride_id}-${notification.sender_name}-${notification.created_at}`;
        if (!shownNotifications.has(notifId)) {
          console.log('NOTIF v361 - NEW notification:', notification.sender_name, notification.message);
          showFloatingNotification(notification.sender_name, notification.message, notification.ride_id);
          shownNotifications.add(notifId);
          newCount++;
        }
      });
      
      if (newCount > 0) {
        console.log(`NOTIF v361 - Showed ${newCount} new notifications`);
      }
    }
  } catch (error) {
    console.error('NOTIF v361 - Error:', error);
  }
}

function showFloatingNotification(senderName, message, rideId) {
  console.log('NOTIFICATION v361 - Showing notification:', senderName, message, rideId);
  
  // Vytvoř notifikaci přímo jako div
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    z-index: 999999 !important;
    background: #4CAF50 !important;
    color: white !important;
    padding: 15px !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    font-family: Arial, sans-serif !important;
    max-width: 300px !important;
    pointer-events: auto !important;
  `;
  
  notification.innerHTML = `
    <div style="font-weight: bold; margin-bottom: 5px;">📨 Nová zpráva!</div>
    <div style="margin-bottom: 5px;">Od: <strong>${senderName}</strong></div>
    <div style="margin-bottom: 10px; font-style: italic;">"${message}"</div>
    <button onclick="alert('Chat pro jízdu ${rideId}'); this.remove();" style="background: white; color: #4CAF50; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-right: 5px;">💬 Chat</button>
    <button onclick="this.parentElement.remove()" style="background: rgba(255,255,255,0.3); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">×</button>
  `;
  
  document.body.appendChild(notification);
  console.log('NOTIFICATION v361 - Added to DOM, element:', notification);
  
  // Automatické odstranění po 8 sekundách
  setTimeout(() => {
    if (document.body.contains(notification)) {
      notification.remove();
      console.log('NOTIFICATION v361 - Auto-removed');
    }
  }, 8000);
}

function testNotificationDisplay() {
  console.log('TEST v361 - Testing notification system');
  const currentUser = localStorage.getItem('currentUser');
  if (!currentUser) {
    alert('Musíte být přihlášeni!');
    return;
  }
  
  // Přímý test notifikace
  console.log('TEST v361 - Creating test notification');
  showFloatingNotification('Test Uživatel', 'Testovací zpráva', 999);
  
  // Zkontroluj skutečné notifikace
  console.log('TEST v361 - Checking real notifications');
  checkForNotifications();
  
  // Debug info
  setTimeout(() => {
    const notifications = document.querySelectorAll('[style*="position: fixed"]');
    console.log('TEST v361 - Found', notifications.length, 'fixed elements on page');
    notifications.forEach((el, i) => {
      console.log(`Element ${i}:`, el.style.cssText, el.innerHTML.substring(0, 50));
    });
  }, 1000);
  
  alert('Test notifikací spuštěn! Zkontrolujte konzoli.');
}

async function createTestMessage() {
  const currentUser = localStorage.getItem('currentUser');
  if (!currentUser) {
    alert('Musíte být přihlášeni!');
    return;
  }
  
  const action = prompt('1 - Odeslat zprávu\n2 - Zkontrolovat notifikace\n3 - Test notifikace');
  
  if (action === '1') {
    const user = JSON.parse(currentUser);
    try {
      const response = await fetch('/api/rides/search');
      const rides = await response.json();
      if (rides.length === 0) {
        alert('Žádné jízdy!');
        return;
      }
      const testRide = rides[0];
      const testMessage = `Test od ${user.name} - ${new Date().toLocaleTimeString()}`;
      
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
        alert(`✅ Zpráva odeslána: "${testMessage}"`);
      } else {
        alert('❌ Chyba při odesílání');
      }
    } catch (error) {
      alert('❌ Chyba: ' + error.message);
    }
  } else if (action === '2') {
    checkForNotifications();
  } else if (action === '3') {
    showFloatingNotification('Test', 'Testovací notifikace', 999);
  }
}

// Dummy funkce pro kompatibilitu
function updateRoutePreview() { console.log('updateRoutePreview called'); }
function planRoute() { console.log('planRoute called'); }
function toggleFullscreen() { console.log('toggleFullscreen called'); }
function centerOnUser() { console.log('centerOnUser called'); }
function showAllUsers() { console.log('showAllUsers called'); }
function clearRideMarkers() { console.log('clearRideMarkers called'); }
function stopVoiceGuidance() { console.log('stopVoiceGuidance called'); }