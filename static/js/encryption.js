// static/js/encryption.js
// This requires a library like 'crypto-js' for AES-256 in the browser.
// <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>
// Include this script in your base.html or chat/index.html AFTER crypto-js.

const KEY_SIZE = 256; // AES-256
const IV_SIZE = 128;  // 16 bytes for IV

// Derive a key from the chat password using PBKDF2
// This is a crucial part for security. The server should never know this key.
async function deriveKeyFromChatPassword(chatPassword, salt) {
    // Convert password and salt to Uint8Array
    const enc = new TextEncoder();
    const passwordBytes = enc.encode(chatPassword);
    const saltBytes = enc.encode(salt); // Salt should be unique per chat/user, ideally stored (non-secretly) with chat details

    // Use Web Crypto API for PBKDF2
    const keyMaterial = await crypto.subtle.importKey(
        "raw",
        passwordBytes,
        { name: "PBKDF2" },
        false,
        ["deriveBits", "deriveKey"]
    );

    const derivedKey = await crypto.subtle.deriveKey(
        {
            name: "PBKDF2",
            salt: saltBytes,
            iterations: 100000, // High iteration count for security
            hash: "SHA-256",
        },
        keyMaterial,
        { name: "AES-CBC", length: KEY_SIZE }, // AES-CBC is common for messages
        true, // extractable
        ["encrypt", "decrypt"]
    );

    return derivedKey;
}

// Encrypt message
async function encryptMessage(message, chatPassword, chatSalt) {
    const key = await deriveKeyFromChatPassword(chatPassword, chatSalt);
    const iv = CryptoJS.lib.WordArray.random(IV_SIZE / 8); // Generate random IV

    const encrypted = CryptoJS.AES.encrypt(message, key, { iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 });

    // Return IV and ciphertext, combined or separate, to be sent to server
    // The server just stores this blob, it doesn't decrypt.
    return {
        iv: iv.toString(CryptoJS.enc.Hex),
        ciphertext: encrypted.ciphertext.toString(CryptoJS.enc.Hex)
    };
}

// Decrypt message
async function decryptMessage(encryptedData, chatPassword, chatSalt) {
    const key = await deriveKeyFromChatPassword(chatPassword, chatSalt);
    const iv = CryptoJS.enc.Hex.parse(encryptedData.iv);

    const decrypted = CryptoJS.AES.decrypt({ ciphertext: CryptoJS.enc.Hex.parse(encryptedData.ciphertext) }, key, { iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 });

    return decrypted.toString(CryptoJS.enc.Utf8);
}

// Function to generate a new salt (e.g., for a new chat password setup)
function generateSalt() {
    return CryptoJS.lib.WordArray.random(128 / 8).toString(CryptoJS.enc.Hex); // 16 bytes salt
}

// Placeholder for managing chat salts (You'll need to fetch and store these)
// In a real application, each chat might have a unique salt or derive it from chat_id + user_id.
// For simplicity, we'll assume a shared, known salt or a fixed one for now.
// A better approach: When a chat is created, generate a random salt and store it with the chat in MongoDB (it's not sensitive).
// Then, when retrieving messages, fetch this salt.
let currentChatSalt = "some_static_salt_for_testing"; // **IMPORTANT: This needs to be dynamic per chat!**
// In a real app, this would be retrieved from the server along with chat details
// or derived from known, non-secret chat identifiers.