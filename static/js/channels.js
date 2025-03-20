document.addEventListener("DOMContentLoaded", function() {
    let socket;
    let localStream;
    let peerConnections = {};
    let pendingCandidates = [];
    let currentChannelId = null;
    let pingStartTime = null;
    let pingInterval = null;

    const userElement = document.getElementById("user-info");
    const username = userElement ? userElement.getAttribute("data-username") : null;
    const userId = userElement ? userElement.getAttribute("data-userId") : null;
    const rtcConfig = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

    async function getLocalAudioStream() {
        if (!localStream) {
            try {
                localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                monitorUserVoice(localStream, username);
            } catch (error) {
                console.error("❌ Mic access denied:", error);
                return null;
            }
        }
        return localStream;
    }

    function initWebSocket(channelId) {
        const loc = window.location;
        let wsStart = loc.protocol === 'https:' ? 'wss://' : 'ws://';
        socket = new WebSocket(`${wsStart}${window.location.host}/ws/channel/${channelId}/`);

        socket.onopen = () => {
            sendWebSocketMessage(channelId, "user_update", { action: "join", username });
            // Start the local user's connection after joining
            startConnection(channelId);
        };

        socket.onmessage = event => handleWebSocketMessage(channelId, JSON.parse(event.data));
        socket.onerror = event => console.error("❌ WebSocket error:", event);
        socket.onclose = function () {
            clearInterval(pingInterval);
            pingInterval = null;
        };
    }

    function startConnection(channelId) {
        getLocalAudioStream().then(stream => {
            if (stream) {
                localStream = stream;
                // Notify other users that we're ready to connect
                sendWebSocketMessage(channelId, "ready_to_connect", { userId });
            } else {
                console.error("Failed to get local stream");
            }
        });
    }

    function createPeerConnection(channelId, remoteUserId) {
        if (!peerConnections[channelId]) {
            peerConnections[channelId] = {};
        }

        if (peerConnections[channelId][remoteUserId]) {
            console.warn(`⚠️ PeerConnection with user ${remoteUserId} already exists.`);
            return peerConnections[channelId][remoteUserId];
        }

        const peerConnection = new RTCPeerConnection(rtcConfig);
        peerConnections[channelId][remoteUserId] = peerConnection;

        if (localStream) {
            localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, localStream);
            });
        }

        peerConnection.onicecandidate = event => {
            if (event.candidate) {
                sendWebSocketMessage(channelId, "webrtc_ice_candidate", { candidate: event.candidate, targetUserId: remoteUserId });
            }
        };

        peerConnection.ontrack = event => {
            let remoteAudio = document.getElementById(`remoteAudio_${remoteUserId}`);
            if (!remoteAudio) {
                remoteAudio = document.createElement("audio");
                remoteAudio.id = `remoteAudio_${remoteUserId}`;
                remoteAudio.autoplay = true;
                remoteAudio.controls = true;
                document.getElementById("remoteAudioContainer").appendChild(remoteAudio);
            }
            remoteAudio.srcObject = event.streams[0];
            remoteAudio.muted = false;  // Ensure the audio is not muted
        };

        peerConnection.oniceconnectionstatechange = () => {
            if (peerConnection.iceConnectionState === 'disconnected' ||
                peerConnection.iceConnectionState === 'failed' ||
                peerConnection.iceConnectionState === 'closed') {
            }
        };

        return peerConnection;
    }

    function sendWebSocketMessage(channelId, type, message, attempts = 0) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type, channel_id: channelId, ...message }));
        } else if (attempts < 10) {
            setTimeout(() => sendWebSocketMessage(channelId, type, message, attempts + 1), 100);
        } else {
            console.warn("❌ WebSocket not open. Failed to send message:", { type, channel_id: channelId, ...message });
        }
    }

    function handleWebSocketMessage(channelId, data) {
        switch (data.type) {
            case "ready_to_connect":
                if (data.userId !== userId) {
                    initiateConnection(channelId, data.userId);
                }
                break;
            case "pong":
                if (data.sender === username) {
                    const ping = Date.now() - pingStartTime;
                    document.getElementById(`${username}-ping`).textContent=`${ping} ms`;
                    socket.send(JSON.stringify({ type: "update_ping", sender: username, ping: ping }));
                }
                break;
            case "update_ping":
                document.getElementById(`${data.sender}-ping`).textContent=`${data.ping} ms`;
                break;
            case "voice_activity":
                updateTalkingStatus(data.username, data.is_talking);
                break;
            case "chat_message":
                if (data.userId !== userId) {
                    displayChatMessage(channelId, data.username, data.message, data.timestamp, data.avatar);
                }
                break;
            case "webrtc_offer":
                const offerPC = createPeerConnection(channelId, data.fromUserId);
                offerPC.setRemoteDescription(new RTCSessionDescription(data.offer))
                    .then(() => offerPC.createAnswer())
                    .then(answer => offerPC.setLocalDescription(answer))
                    .then(() => {
                        sendWebSocketMessage(channelId, "webrtc_answer", { answer: offerPC.localDescription, targetUserId: data.fromUserId });
                    })
                    .catch(error => console.error("❌ Error handling offer:", error));
                break;
            case "webrtc_answer":
                const answerPC = peerConnections[channelId][data.fromUserId];
                if (answerPC) {
                    answerPC.setRemoteDescription(new RTCSessionDescription(data.answer))
                        .catch(error => console.error("❌ Failed to set remote answer SDP:", error));
                }
                break;

            case "webrtc_ice_candidate":
                const candidatePC = peerConnections[channelId][data.fromUserId];
                if (candidatePC) {
                    candidatePC.addIceCandidate(new RTCIceCandidate(data.candidate))
                        .catch(error => console.error("❌ ICE Candidate Error:", error));
                }
                break;

            case "user_update":
                if (data.action === "join") {
                    updateUserList(channelId, data, "join");
                    if (data.username !== username) {
                        initiateConnection(channelId, data.username);
                    }
                } else if (data.action === "leave") {
                    updateUserList(channelId, data, "leave");
                    if (peerConnections[channelId] && peerConnections[channelId][data.username]) {
                        peerConnections[channelId][data.username].close();
                        delete peerConnections[channelId][data.username];
                    }
                }
                break;
        }
    }

    function initiateConnection(channelId, remoteUserId) {
        const pc = createPeerConnection(channelId, remoteUserId);
        pc.createOffer()
            .then(offer => {
                return pc.setLocalDescription(offer);
            })
            .then(() => {
                sendWebSocketMessage(channelId, "webrtc_offer", { offer: pc.localDescription, targetUserId: remoteUserId });
            })
            .catch(error => console.error("❌ Error creating offer:", error));
    }

    document.querySelectorAll(".btn-join").forEach(button => {
        button.addEventListener("click", function () {
            let row = this.closest("tr");
            let channelId = row.getAttribute("data-channel-id");
            let detailsRow = row.nextElementSibling;
            let isJoined = button.classList.contains("joined");

            isJoined ? leaveChannel(channelId, button, detailsRow) : checkChannelPassword(channelId, button, detailsRow);
        });
    });

    function checkChannelPassword(channelId, button, detailsRow) {
        fetch(`/check-channel/${channelId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.password_protected) {
                const passwordModal = new bootstrap.Modal(document.getElementById('passwordModal'));
                passwordModal.show();

                document.getElementById('passwordSubmit').onclick = function () {
                    const password = document.getElementById('passwordInput').value;
                        if (!password) {
                            console.warn("Password input is empty.");
                            return;
                        }
                        passwordModal.hide();
                        joinChannel(channelId, button, detailsRow, password);
                    };
                } else {
                    joinChannel(channelId, button, detailsRow, null);
                }
            })
            .catch(error => console.error(`Error checking channel ${channelId}:`, error));
    }

    async function joinChannel(channelId, button, detailsRow, password = null) {
        try {
            button.innerHTML = `Connecting <span class="spinner-border spinner-border-sm"></span>`;
            button.disabled = true;
            currentChannelId = channelId
            const chatInput = document.getElementById(`input-chatbox-${currentChannelId}`);
            const sendButton = document.getElementById(`button-chatbox-${currentChannelId}`);

            sendButton.addEventListener("click", sendMessage);
            chatInput.addEventListener("keypress", function (event) {
                if (event.key === "Enter") {
                    sendMessage();
                }
            });

            let micAvailable = await getLocalAudioStream();
            if (!micAvailable) return showToast("error", "Mic Access Denied", "Please grant microphone access.");

            let response = await fetch(`/join-channel/${channelId}/`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken(), "X-Requested-With": "XMLHttpRequest" },
                body: JSON.stringify({ password }),
            });

            if (response.status === 403) {
                const errorData = await response.json();
                showToast("error", "Authentication Failed", errorData.error || "Incorrect password. Please try again.");
                button.innerHTML = "Join";
                return;
            }
            if (!response.ok) throw new Error(`Server responded with ${response.status}`);
            let data = await response.json();
            button.innerHTML = "Leave";
            button.classList.add("joined");
            detailsRow.classList.remove("hidden")
            detailsRow.querySelector(".user-table tbody").innerHTML = renderUsers(data.users);
            new bootstrap.Collapse(detailsRow.querySelector(".collapse"), { toggle: true });

            initWebSocket(channelId, micAvailable);
            initializeVolumeControls();
            showToast("success", "Joined Channel", `You joined #${channelId}.`);
            pingInterval = setInterval(() => {
                if (socket && socket.readyState === WebSocket.OPEN) {  // Check if socket is open
                    pingStartTime = Date.now();
                    socket.send(JSON.stringify({ type: "ping", sender: username }));
                }
            }, 5000);
        } catch (error) {
            showToast("error", "Join Failed", error.message);
            button.innerHTML = "Join";
        } finally {
            button.disabled = false;
        }
    }

    function leaveChannel(channelId, button, detailsRow) {
        if (peerConnections[channelId]) {
            currentChannelId = null

            if (pingInterval) {
                clearInterval(pingInterval);
                pingInterval = null;
            }

            // Close all tracks in the local stream
            if (localStream) {
                localStream.getTracks().forEach(track => {
                    track.stop();
                });
                localStream = null;  // Reset the stream
            }

            // Close all peer connections for this channel
            Object.entries(peerConnections[channelId]).forEach(([userId, pc]) => {
                pc.ontrack = null;
                pc.onicecandidate = null;
                pc.oniceconnectionstatechange = null;
                pc.close();

                // Remove the remote audio element
                const remoteAudio = document.getElementById(`remoteAudio_${userId}`);
                if (remoteAudio) {
                    remoteAudio.remove();
                }
            });

            delete peerConnections[channelId];  // Remove from the list
        }

        // Ensure WebSocket is closed
        if (socket) {
            socket.close();
            socket = null;
        }

        // Reset UI
        button.textContent = "Join";
        button.classList.remove("joined");
        bootstrap.Collapse.getInstance(detailsRow.querySelector(".collapse")).hide();
        showToast("success", "Left Channel", `You left #${channelId}.`);
        setTimeout(() => detailsRow.classList.add("hidden"), 300);
    }

    function updateUserList(channelId, data, action) {
        let userList = document.querySelector(`#channel-details-${channelId} .user-list`);
        if (!userList) return;

        if (action === "join") {
            let existingRow = userList.querySelector(`tr[id="${data.username}"]`);
            if (existingRow) {

            } else {
                let newRow = document.createElement("tr");
                newRow.id = data.username;
                newRow.innerHTML = `
                    <td>
                        <div class="avatar-wrapper">
                            <img src="${data.avatar}" class="avatar rounded-circle" alt="${data.username}" width="40" height="40">
                            <div id="status-${data.username}" class="status-circle"></div>
                        </div>
                        <a href="/user/profile/${data.username}">${data.name}</a>
                        <span class="badge bg-primary ms-2">member</span>
                        <div class="volume-control">
                            <button type="button" class="volume-btn btn btn-link p-0 align-middle"
                                data-user="${data.user_id}">
                                <i class="bi bi-volume-up fs-3"></i>
                            </button>
                            <div class="volume-slider-container hidden">
                                <input type="range" class="form-range" min="0" max="1" step="0.1" value="1" 
                                    data-user="${data.userId}">
                                <span class="volume-percentage">100%</span>
                            </div>
                        </div>
                    </td>
                    <td><span class="flag flag-${data.flag} align-middle"></span></td>
                    <td class="align-middle"><a id="${data.username}-ping" class="align-middle">0 ms</a></td>
                `;
                userList.appendChild(newRow);
            }
        } else if (action === "leave") {
            let row = userList.querySelector(`tr[id="${data.username}"]`);
            if (row) {
                row.remove();
            }
        }
    }

    function renderUsers(users) {
        return users.map(user => `
        <tr id="${user.username}">
            <td>
                <div class="avatar-wrapper">
                    <img src="${user.avatar}" class="avatar rounded-circle" alt="${user.name}" width="40" height="40">
                    <div id="status-${user.username}" class="status-circle"></div>
                </div>
                <a href="/user/profile/${user.username}">${user.name}</a>
                <span class="badge bg-primary ms-2">member</span>
                ${user.username === username ? `
                <button class="deafen-btn btn btn-link p-0 align-middle" data-username="${user.username}"><i class="bi bi-volume-up fs-3"></i></button>
                <button class="mute-btn btn btn-link p-0 align-middle"><i class="bi bi-mic fs-3"></i></button>
                ` : `
                    <div class="volume-control">
                        <button type="button" class="volume-btn btn btn-link p-0 align-middle"
                            data-user="${user.userId}">
                            <i class="bi bi-volume-up fs-3"></i>
                        </button>
                        <div class="volume-slider-container hidden">
                            <input type="range" class="form-range" min="0" max="1" step="0.01" value="1" 
                                data-user="${user.userId}">
                            <span class="volume-percentage">100%</span>
                        </div>
                    </div>
                `}
            </td>
            <td><span class="flag flag-${user.flag} align-middle"></span></td>
            <td class="align-middle"><a id="${user.username}-ping" class="align-middle">0 ms</a></td>
        </tr>
        `).join('');
    }

    function getCSRFToken() {
        return document.querySelector("input[name='csrfmiddlewaretoken']").value;
    }

    function sendMessage() {
        if (!currentChannelId) {
            console.warn("No active channel selected!");
            return;
        }

        const chatInput = document.getElementById(`input-chatbox-${currentChannelId}`);
        if (!chatInput) {
            console.warn("Chat input not found for channel:", currentChannelId);
            return;
        }

        const message = chatInput.value.trim();
        if (message && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: "chat_message",
                channel_id: currentChannelId,
                message: message,
                username: username,
            }));
            chatInput.value = "";
        }
    }

    function displayChatMessage(channelId, sent_username, message, timestamp, avatar) {
        const chatMessages = document.querySelector(`#chatbox-${channelId} .chat-messages`);
        const isUser = sent_username === username;  // Check if sender is current user

        const messageHTML = `
            <div class="chat-message-${isUser ? "left" : "right"} pb-4">
                <div class="d-flex flex-column align-items-center">
                    <img src="${avatar}" class="rounded-circle mr-1" width="40" height="40" alt="avatar">
                    <div class="text-muted small text-nowrap mt-2">${timestamp}</div>
                </div>
                <div class="flex-shrink-1 bg-light rounded py-2 px-3 ${isUser ? "ml-3" : "mr-3"}">
                    <div class="font-weight-bold mb-1">${isUser ? "You" : sent_username}</div>
                    ${message}
                </div>
            </div>`;

        chatMessages.innerHTML += messageHTML;
        chatMessages.scrollTop = chatMessages.scrollHeight;  // Auto-scroll to the latest message
    }

    document.addEventListener("click", function (event) {
        if (event.target.closest(".mute-btn")) {
            const button = event.target.closest(".mute-btn");
            toggleMuteMic(button);
        }

        if (event.target.closest(".deafen-btn")) {
            const button = event.target.closest(".deafen-btn");
            toggleDeafen(button);
        }

        if (event.target.closest(".volume-btn")) {
            const button = event.target.closest(".volume-btn");
            const username = button.dataset.username;
            const sliderContainer = button.nextElementSibling;
            sliderContainer.classList.toggle("hidden");
        }
    });

    document.addEventListener("input", function(event) {
        if (event.target.classList.contains("form-range")) {
            const user_id = event.target.dataset.user;
            const volume = parseFloat(event.target.value);
            const percentageElement = event.target.nextElementSibling;
            const percentage = Math.round(volume * 100);
            percentageElement.textContent = `${percentage}%`;
            changeUserVolume(user_id, volume);
        }
    });

    // Function to toggle mute
    function toggleMuteMic(button) {
        if (!localStream) {
            console.error("No local stream available.");
            return;
        }

        const audioTrack = localStream.getAudioTracks()[0];
        if (!audioTrack) {
            console.error("No audio track found in local stream.");
            return;
        }

        // Toggle mute state
        audioTrack.enabled = !audioTrack.enabled;
        const isMuted = !audioTrack.enabled;

        // Update UI
        button.dataset.muted = isMuted;
        button.innerHTML = isMuted
            ? '<i class="bi bi-mic-mute fs-3"></i>'
            : '<i class="bi bi-mic fs-3"></i>';
    }

    // Function to toggle deafen
    function toggleDeafen(button) {
        const audioContainer = document.getElementById("remoteAudioContainer");
        if (!audioContainer) {
            console.error("Remote audio container not found.");
            return;
        }

        const audioElements = audioContainer.querySelectorAll("audio");
        if (audioElements.length === 0) {
            console.error("No audio elements found in remote audio container.");
            return;
        }

        let isDeafened = button.dataset.deafened === "true";
        isDeafened = !isDeafened; // Toggle state

        audioElements.forEach(audio => {
            audio.muted = isDeafened;
        });

        // Store state properly and update button icon
        button.dataset.deafened = isDeafened;
        button.innerHTML = isDeafened
            ? '<i class="bi bi-volume-mute fs-3"></i>'
            : '<i class="bi bi-volume-up fs-3"></i>';
    }

    function updateTalkingStatus(username, isTalking) {
        const statusCircle = document.getElementById(`status-${username}`);
        if (statusCircle) {
            statusCircle.classList.toggle('talking', isTalking);
        }
    }

    function monitorUserVoice(stream, username) {
        const audioContext = new AudioContext();
        const analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        let lastState = false;

        function checkVolume() {
            analyser.getByteFrequencyData(dataArray);
            const volume = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;

            let isTalking = volume > 10;

            if (isTalking !== lastState) {
                lastState = isTalking;
                socket.send(JSON.stringify({
                    type: "voice_status",
                    username: username,
                    is_talking: isTalking
                }));
            }

            requestAnimationFrame(checkVolume);
        }

        checkVolume();
    }

    function changeUserVolume(userId, volume) {
        const audioElement = document.getElementById(`remoteAudio_${userId}`);
        if (audioElement) {
            audioElement.volume = volume;
        }
    }

    function initializeVolumeControls() {
        const audioContainer = document.getElementById("remoteAudioContainer");
        const audioElements = audioContainer.querySelectorAll("audio");

        audioElements.forEach(audio => {
            const username = audio.id.replace("remoteAudio_", "");
            const volumeSlider = document.querySelector(`.form-range[data-username="${username}"]`);
            const volumePercentage = volumeSlider.nextElementSibling;

            if (volumeSlider) {
                volumeSlider.value = audio.volume;
                const percentage = Math.round(audio.volume * 100);
                volumePercentage.textContent = `${percentage}%`;
            }
        });
    }
});
