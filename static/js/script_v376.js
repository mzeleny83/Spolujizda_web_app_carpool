// Chat funkce v376
async function loadChatMessages(rideId) {
  try {
    const response = await fetch('/api/chat/' + rideId + '/messages');
    const messages = await response.json();
    
    const messagesDiv = document.getElementById('chatMessages');
    if (!messagesDiv) return;
    
    // Získej jméno uživatele z localStorage
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
      const isMyMessage = msg.sender_name === userName;
      div.style.cssText = `margin: 8px 0; padding: 8px; border-radius: 8px; ${isMyMessage ? 'background: #e3f2fd; text-align: right; margin-left: 50px;' : 'background: #f5f5f5; margin-right: 50px;'}`;
      
      // Jednoduché zobrazení času
      const now = new Date();
      const hours = now.getHours();
      const minutes = now.getMinutes();
      const timeStr = hours + ':' + (minutes < 10 ? '0' + minutes : minutes);
      
      div.innerHTML = `<strong>${msg.sender_name}:</strong> ${msg.message}<br><small style="color: #666;">${timeStr}</small>`;
      messagesDiv.appendChild(div);
    });
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  } catch (error) {
    console.error('Chyba při načítání zpráv:', error);
  }
}