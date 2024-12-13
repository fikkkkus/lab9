const username = prompt("Enter your username:") || "admin";
const chatRoom = prompt("Enter the chat room name:") || "admin_room";
const websocket = new WebSocket(`ws://localhost:8888/websocket?user=${encodeURIComponent(username)}&room_name=${encodeURIComponent(chatRoom)}`);

const chatContainer = document.getElementById("chat-container");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");

document.getElementById('user-info').innerText = `User: ${username}`;
document.getElementById('room-info').innerText = `Room: ${chatRoom}`;

websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const messageElement = document.createElement("div");

    if (data.type === "message") {
        messageElement.classList.add("message");
        if (data.user === username) {
            messageElement.classList.add("user");
            messageElement.textContent = `${data.text}`;
        } else {
            messageElement.classList.add("other");
            messageElement.textContent = `${data.user}: ${data.text}`;
        }
    } else if (data.type === "join") {
        // Системное сообщение
        messageElement.classList.add("system-message");
        messageElement.textContent = `${data.user} joined the room.`;
    }

    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight; // Автопрокрутка вниз
};

sendButton.addEventListener("click", () => {
    const text = messageInput.value.trim();
    if (text) {
        websocket.send(JSON.stringify({ text: text, room: chatRoom }));
        messageInput.value = "";
    }
});

messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) { // Проверяем, что нажат только Enter без Shift
        event.preventDefault(); // Предотвращаем добавление новой строки
        sendMessage(); // Вызываем функцию отправки сообщения
    }
});

// Функция отправки сообщения
function sendMessage() {
    const text = messageInput.value.trim();
    if (text) {
        websocket.send(JSON.stringify({ text: text, room: chatRoom }));
        messageInput.value = ""; // Очищаем поле ввода
    }
}

// Обновляем обработчик кнопки
sendButton.addEventListener("click", sendMessage);

websocket.onopen = () => console.log("Connected to the server");
websocket.onclose = () => console.log("Disconnected from the server");
