// Chat funkce v400 - zprávy vlevo
function openChat(rideId, driverName) {
  try {
    console.log('CHAT v400 - Opening chat with:', driverName, 'for ride:', rideId);
    
    // Detekce mobilního zařízení
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;
    
    // Vytvoříme modal okno
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; background: rgba(0,0,0,0.5) !important; z-index: 999999 !important; display: flex !important; align-items: center !important; justify-content: center !important;';
    
    const chatBox = document.createElement('div');
    const chatBox = document.createElement('div');
    let chatBoxStyle = `background: white !important; width: 400px !important; height: 500px !important; border-radius: 10px !important; padding: 20px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; position: relative !important;`;

    if (isMobile) {
        chatBoxStyle = `background: white !important; width: 90vw !important; height: 80vh !important; border-radius: 10px !important; padding: 20px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; position: fixed !important; left: 10px !important; top: 50% !important; transform: translateY(-50%) !important;`;
    }

    chatBox.style.cssText = chatBoxStyle;
    
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.style.cssText = 'background: #f44336; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; position: absolute; top: 10px; right: 10px;';
    closeBtn.onclick = () => modal.remove();
    
    const messagesHeight = isMobile ? 'calc(100% - 120px)' : '350px';
    
    chatBox.innerHTML = `
      <h3 style="margin-top: 0; font-size: ${isMobile ? '18px' : '20px'};">Chat s ${driverName}</h3>
      <div id="chatMessages" style="height: ${messagesHeight}; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background: #f9f9f9;"></div>
      <div style="display: flex; gap: 10px;">
        <input type="text" id="chatInput" placeholder="Napište zprávu..." style="flex: 1; padding: ${isMobile ? '12px' : '8px'}; border: 1px solid #ccc; border-radius: 4px; font-size: ${isMobile ? '16px' : '14px'};">
        <button onclick="sendChatMessage(${rideId})" style="background: #4CAF50; color: white; border: none; padding: ${isMobile ? '12px 20px' : '8px 15px'}; border-radius: 4px; cursor: pointer; font-size: ${isMobile ? '16px' : '14px'};">Odeslat</button>
      </div>
    `;
    
    chatBox.appendChild(closeBtn);
    modal.appendChild(chatBox);
    document.body.appendChild(modal);
    
    // Načteme zprávy
    loadChatMessages(rideId);
    
    // Automatické obnovování
    const interval = setInterval(() => loadChatMessages(rideId), 3000);
    
    // Vyčistíme interval při zavření
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        clearInterval(interval);
        modal.remove();
      }
    });
    
  } catch (error) {
    console.error('Error opening chat:', error);
    alert('Chyba při otevírání chatu: ' + error.message);
  }
}

async function sendChatMessage(rideId) {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;
  
  let userName = 'Anonym';
  const currentUser = localStorage.getItem('currentUser');
  if (currentUser) {
    try {
      const user = JSON.parse(currentUser);
      userName = user.name || 'Anonym';
    } catch (e) {
      console.error('Error parsing currentUser:', e);
    }
  }
  
  try {
    const response = await fetch('/api/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ride_id: rideId,
        sender_name: userName,
        message: message
      })
    });
    
    if (response.ok) {
      input.value = '';
      loadChatMessages(rideId);
    } else {
      const error = await response.json();
      alert('Chyba při odesílání zprávy: ' + (error.error || 'Neznámá chyba'));
    }
  } catch (error) {
    alert('Chyba při odesílání zprávy: ' + error.message);
  }
}

async function loadChatMessages(rideId) {
  try {
    const response = await fetch('/api/chat/' + rideId + '/messages');
    const messages = await response.json();
    
    const messagesDiv = document.getElementById('chatMessages');
    if (!messagesDiv) return;
    
    let userName = 'Anonym';
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
      try {
        const user = JSON.parse(currentUser);
        userName = user.name || 'Anonym';
      } catch (e) {
        console.error('Error parsing currentUser:', e);
      }
    }
    
    messagesDiv.innerHTML = '';
    
    messages.forEach(msg => {
      const div = document.createElement('div');
      // VŠECHNY zprávy vlevo - bez margin-right, bez text-align right
      div.style.cssText = 'margin: 8px 0; padding: 8px; border-radius: 8px; background: #f5f5f5; text-align: left; width: 100%;';
      div.innerHTML = `<strong>${msg.sender_name}:</strong> ${msg.message}`;
      messagesDiv.appendChild(div);
    });
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  } catch (error) {
    console.error('Chyba při načítání zpráv:', error);
  }
}