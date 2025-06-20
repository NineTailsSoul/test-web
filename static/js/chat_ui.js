// static/js/chat_ui.js
let currentChatId = null;
let currentChatPassword = null;
let currentChatSalt = "some_static_salt_for_testing"; // **IMPORTANT: MAKE THIS DYNAMIC PER CHAT**
let currentUserId = "{{ session['user_id'] }}"; // Passed from Jinja2 template

const chatMessagesContainer = document.getElementById('chat-messages-container');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatUnlockPasswordInput = document.getElementById('chat-unlock-password');
const messageInputWrapper = document.querySelector('.message-input-wrapper');
const typingIndicator = document.getElementById('typing-indicator');
const currentChatNameDisplay = document.getElementById('current-chat-name');
const chatItems = document.querySelectorAll('.chat-item');
const startChatButtons = document.querySelectorAll('.start-chat-btn');

function displayTypingIndicator(username, isTyping) {
    if (isTyping) {
        typingIndicator.innerHTML = `<p>${username} is typing...</p>`;
        typingIndicator.style.display = 'block';
    } else {
        typingIndicator.style.display = 'none';
    }
}

function addMessageToChat(message) {
    const messageBubble = document.createElement('div');
    messageBubble.classList.add('message-bubble');
    messageBubble.classList.add(message.is_self ? 'sent' : 'received');
    messageBubble.dataset.messageId = message.id;

    const senderSpan = document.createElement('span');
    senderSpan.classList.add('message-sender');
    senderSpan.textContent = message.is_self ? 'You' : message.sender_username;

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.textContent = message.content;

    const timeSpan = document.createElement('span');
    timeSpan.classList.add('message-time');
    timeSpan.textContent = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageBubble.appendChild(senderSpan);
    messageBubble.appendChild(contentDiv);
    messageBubble.appendChild(timeSpan);

    chatMessagesContainer.appendChild(messageBubble);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight; // Scroll to bottom
}

async function loadChatMessages(chatId) {
    chatMessagesContainer.innerHTML = ''; // Clear existing messages
    typingIndicator.style.display = 'none'; // Hide typing indicator
    
    // Fetch chat history
    const response = await fetch(`/chat/get_messages/${chatId}`);
    if (response.ok) {
        const messages = await response.json();
        if (messages.length === 0) {
            chatMessagesContainer.innerHTML = '<p class="empty-chat-message">No messages in this chat yet.</p>';
        } else {
            for (const msg of messages) {
                // Decrypt and add message
                try {
                    const decryptedContent = await decryptMessage({iv: msg.content.iv, ciphertext: msg.content.ciphertext}, currentChatPassword, currentChatSalt);
                    msg.content = decryptedContent;
                    addMessageToChat(msg);
                } catch (error) {
                    console.error('Error decrypting historical message:', error);
                    msg.content = "Error decrypting message.";
                    addMessageToChat(msg);
                }
            }
        }
    } else {
        const errorData = await response.json();
        chatMessagesContainer.innerHTML = `<p class="empty-chat-message">Error loading messages: ${errorData.error}</p>`;
    }
}

// Event listener for chat item clicks (to select a chat)
chatItems.forEach(item => {
    item.addEventListener('click', () => {
        // Leave previous chat room if any
        if (currentChatId) {
            emit_leave_chat(currentChatId);
        }

        // Reset UI state
        currentChatId = item.dataset.chatId;
        currentChatNameDisplay.textContent = item.dataset.chatName;
        messageInput.value = '';
        messageInput.disabled = true;
        sendButton.disabled = true;
        messageInputWrapper.style.display = 'none';
        chatUnlockPasswordInput.value = '';
        chatUnlockPasswordInput.style.display = 'block';
        chatMessagesContainer.innerHTML = '<p class="empty-chat-message">Enter chat password to unlock this chat.</p>';
        
        // Highlight selected chat
        chatItems.forEach(ci => ci.classList.remove('active-chat'));
        item.classList.add('active-chat');

        // Join the new chat room
        emit_join_chat(currentChatId);
    });
});

// Event listener for chat unlock password
chatUnlockPasswordInput.addEventListener('keypress', async (e) => {
    if (e.key === 'Enter' && currentChatId) {
        const password = chatUnlockPasswordInput.value;
        const response = await fetch('/auth/check_chat_password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: currentChatId, password: password })
        });

        if (response.ok) {
            currentChatPassword = password; // Store for encryption/decryption
            chatUnlockPasswordInput.style.display = 'none';
            messageInputWrapper.style.display = 'flex';
            messageInput.disabled = false;
            sendButton.disabled = false;
            chatMessagesContainer.innerHTML = ''; // Clear "Enter password" message
            loadChatMessages(currentChatId); // Load messages after successful unlock
            messageInput.focus();
        } else {
            alert('Incorrect chat password!');
            chatUnlockPasswordInput.value = ''; // Clear password on failure
        }
    }
});

// Event listener for sending messages
sendButton.addEventListener('click', () => {
    const messageContent = messageInput.value;
    if (messageContent && currentChatId && currentChatPassword) {
        emit_send_message(currentChatId, messageContent, currentChatPassword, currentChatSalt);
        messageInput.value = ''; // Clear input after sending
        emit_typing_status(currentChatId, false); // Stop typing after sending
    }
});

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendButton.click(); // Trigger send button click
    }
});

// Typing indicator logic
let typingTimer;
const TYPING_DELAY = 1000; // 1 second

messageInput.addEventListener('input', () => {
    if (!currentChatId || !messageInput.value.trim()) {
        clearTimeout(typingTimer);
        emit_typing_status(currentChatId, false); // Stop typing if input is empty
        return;
    }

    emit_typing_status(currentChatId, true);
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
        emit_typing_status(currentChatId, false);
    }, TYPING_DELAY);
});


// Event listener for starting a chat with a friend directly from the friend list
startChatButtons.forEach(button => {
    button.addEventListener('click', async (e) => {
        const friendUsername = e.target.dataset.friendUsername;
        const response = await fetch(`/chat/start_chat_with_friend/${friend_username}`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            // Find the chat item in the sidebar and trigger a click
            const chatItem = document.querySelector(`.chat-item[data-chat-id="${data.chat_id}"]`);
            if (chatItem) {
                chatItem.click(); // Simulate clicking the chat item to open it
            } else {
                // If chat item wasn't already in DOM (e.g., brand new chat),
                // you'd need to dynamically add it to the chat list here
                // and then trigger its click. For now, a full page reload might be easiest for new chats.
                alert('Chat created! Please refresh to see it in your chat list and open it.');
                window.location.reload(); // Simple reload for now
            }
        } else {
            alert(`Error starting chat: ${data.error}`);
        }
    });
});

// Event listener for message deletion
chatMessagesContainer.addEventListener('contextmenu', async (e) => {
    const messageBubble = e.target.closest('.message-bubble');
    if (!messageBubble) return;

    e.preventDefault(); // Prevent default right-click context menu

    const messageId = messageBubble.dataset.messageId;
    const isSelfMessage = messageBubble.classList.contains('sent');

    if (isSelfMessage) {
        if (confirm('Delete this message for yourself?')) {
            const response = await fetch(`/chat/delete_message/${messageId}`, {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                messageBubble.remove(); // Remove from UI
            } else {
                alert(`Error deleting message: ${data.message}`);
            }
        }
    }
});