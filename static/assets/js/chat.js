document.addEventListener("DOMContentLoaded", function () {
  const receiverIdEl = document.getElementById("receiverId");
  const currentUserIdEl = document.getElementById("currentUserId");
  const currentUsernameEl = document.getElementById("currentUsername");

  if (!receiverIdEl || !currentUserIdEl || !currentUsernameEl) {
    console.warn("Chat DOM elements not found.");
    return;
  }

  // Use getAttribute('data-value') instead of textContent
  const receiverId = parseInt(receiverIdEl.getAttribute("data-value"));
  const currentUserId = parseInt(currentUserIdEl.getAttribute("data-value"));
  const currentUsername = currentUsernameEl.getAttribute("data-value");
  const chatLog = document.getElementById("chatLog");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const shownMessages = new Set();

  if (!chatLog || !messageInput) {
    console.warn("Chat log or message input not found.");
    return;
  }

  chatLog.scrollTop = chatLog.scrollHeight;

  const chatSocket = new WebSocket(
    (window.location.protocol === "https:" ? "wss://" : "ws://") +
      window.location.host +
      "/ws/chat/" +
      receiverId +
      "/"
  );

  function escapeHTML(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function removeNoMessagesPlaceholder() {
    const noMessagesEl = document.getElementById("noMessages");
    if (noMessagesEl) noMessagesEl.remove();
  }

  function addMessageToLog(
    senderName,
    messageContent,
    senderId,
    timestamp = new Date()
  ) {
    removeNoMessagesPlaceholder(); // Remove placeholder on any new message

    const messageBubble = document.createElement("div");
    messageBubble.classList.add("message-bubble");
    messageBubble.classList.add(
      senderId === currentUserId ? "sent" : "received"
    );

    let formattedTime = timestamp;
    if (typeof timestamp === "string") {
      try {
        const dateObj = new Date(timestamp);
        formattedTime = dateObj.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
      } catch {
        formattedTime = new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
      }
    } else if (timestamp instanceof Date) {
      formattedTime = timestamp.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else {
      formattedTime = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    if (senderId !== currentUserId) {
      const senderNameSpan = document.createElement("span");
      senderNameSpan.classList.add("sender-name");
      senderNameSpan.innerHTML = escapeHTML(senderName);
      messageBubble.appendChild(senderNameSpan);
    }

    const messageContentSpan = document.createElement("span");
    messageContentSpan.classList.add("message-content");
    messageContentSpan.innerHTML = escapeHTML(messageContent);
    messageBubble.appendChild(messageContentSpan);

    const timestampSpan = document.createElement("span");
    timestampSpan.classList.add("timestamp");
    timestampSpan.textContent = formattedTime;
    messageBubble.appendChild(timestampSpan);

    chatLog.appendChild(messageBubble);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  chatSocket.onopen = function () {
    console.log("WebSocket connection established.");
  };

  chatSocket.onmessage = function (e) {
    try {
      const data = JSON.parse(e.data);
      const { sender, message, sender_id, timestamp, message_id } = data;

      // Ignore if this message_id was already shown (optimistic UI)
      if (message_id && shownMessages.has(message_id)) {
        return;
      }
      if (message_id) shownMessages.add(message_id);

      addMessageToLog(sender, message, sender_id, timestamp);
    } catch (err) {
      console.error("Error parsing message:", err);
    }
  };

  chatSocket.onclose = function () {
    console.error("Chat socket closed unexpectedly. Reloading in 3s...");
    setTimeout(() => location.reload(), 3000);
  };

  chatSocket.onerror = function (e) {
    console.error("WebSocket error:", e);
  };

  function sendMessage() {
    const messageText = messageInput.value.trim();
    if (messageText === "") return;

    const localTimestamp = new Date();
    const messageId = Date.now() + "-" + Math.random(); // simple unique id

    shownMessages.add(messageId); // mark as already shown

    // Optimistically display the message
    addMessageToLog(
      currentUsername,
      messageText,
      currentUserId,
      localTimestamp
    );

    // Send to WebSocket server with message_id
    chatSocket.send(
      JSON.stringify({ message: messageText, message_id: messageId })
    );

    messageInput.value = "";
    removeNoMessagesPlaceholder();
  }

  // Enter key event
  messageInput.addEventListener("keyup", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  });

  // Send button event
  if (sendBtn) {
    sendBtn.addEventListener("click", function (event) {
      event.preventDefault();
      sendMessage();
    });
  }
});
function onMessageSent() {
  // Redirect to the message list page
  window.location.href = "/messages/"; // Adjust this URL to your actual message list route
}
