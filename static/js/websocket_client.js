// static/js/websocket_client.js
const socket = io(); // Connect to the Socket.IO server

socket.on('connect', () => {
    console.log('Connected to WebSocket server');
    // You might want to join the current chat room here if one is already selected
    // emit_join_chat(currentChatId); // This would be called from chat_ui.js
});

socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket server');
});

socket.on('status', (data) => {
    console.log('Server Status:', data.msg);
});

socket.on('receive_message', async (data) => {
    console.log('Received raw message:', data);
    // Assuming 'currentChatPassword' and 'currentChatSalt' are set in chat_ui.js
    if (window.currentChatId === data.chat_id && window.currentChatPassword && window.currentChatSalt) {
        try {
            const decryptedContent = await decryptMessage({iv: data.message.iv, ciphertext: data.message.ciphertext}, window.currentChatPassword, window.currentChatSalt);
            data.content = decryptedContent; // Add decrypted content for display
            addMessageToChat(data); // Call function from chat_ui.js
        } catch (error) {
            console.error('Error decrypting message:', error);
            data.content = "Error decrypting message."; // Display error
            addMessageToChat(data);
        }
    } else {
        // If chat isn't active or password not entered, just show encrypted or a notification
        console.warn('Received message for inactive chat or no chat password set.');
        // You might want a subtle notification here (e.g., in chat list preview)
        // BUT remember the "no notifications or sounds" rule.
        // So, update the chat list preview directly without sound/pop-up.
    }
});

socket.on('typing_status', (data) => {
    if (window.currentChatId === data.chat_id && data.user_id !== window.currentUserId) { // Prevent showing own typing
        displayTypingIndicator(data.username, data.is_typing); // Call function from chat_ui.js
    }
});

// Functions to emit messages (called from chat_ui.js)
function emit_join_chat(chatId) {
    socket.emit('join_chat', { room_id: chatId });
}

function emit_leave_chat(chatId) {
    socket.emit('leave_chat', { room_id: chatId });
}

async function emit_send_message(chatId, messageContent, chatPassword, chatSalt) {
    if (!messageContent.trim()) return;

    try {
        const encryptedData = await encryptMessage(messageContent, chatPassword, chatSalt);
        // The server-side will receive this and just relay it.
        socket.emit('send_message', {
            chat_id: chatId,
            message: encryptedData
        });
    } catch (error) {
        console.error('Error encrypting and sending message:', error);
        alert('Failed to send message: Encryption error.');
    }
}

function emit_typing_status(chatId, isTyping) {
    socket.emit('typing', { chat_id: chatId, is_typing: isTyping });
}