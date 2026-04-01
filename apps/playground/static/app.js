/**
 * SDR Agent Playground - JavaScript
 */

// ============================================
// CONFIG
// ============================================

const API_BASE_URL = 'http://127.0.0.1:8000';

// ============================================
// STATE
// ============================================

let sessionId = generateSessionId();
let currentLead = { name: '', email: '' };
let messageHistory = [];

// ============================================
// INIT
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initializeSession();
    setupEventListeners();
});

function initializeSession() {
    // Carregar sessão do localStorage se existir
    const savedSession = localStorage.getItem('sdr_session_id');
    if (savedSession) {
        sessionId = savedSession;
    } else {
        localStorage.setItem('sdr_session_id', sessionId);
    }

    document.getElementById('session-id').textContent = `Session: ${sessionId.slice(0, 8)}...`;
}

function setupEventListeners() {
    // Send button
    document.getElementById('send-button').addEventListener('click', sendMessage);

    // Enter para enviar (Shift+Enter para nova linha)
    document.getElementById('message-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Clear button
    document.getElementById('clear-button').addEventListener('click', clearConversation);

    // New session button
    document.getElementById('new-session-button').addEventListener('click', newSession);

    // Radio buttons para tipo de mensagem
    document.querySelectorAll('input[name="message-type"]').forEach((radio) => {
        radio.addEventListener('change', handleMediaTypeChange);
    });

    // Lead info
    document.getElementById('lead-name').addEventListener('blur', (e) => {
        currentLead.name = e.target.value;
    });
    document.getElementById('lead-email').addEventListener('blur', (e) => {
        currentLead.email = e.target.value;
    });
}

// ============================================
// MESSAGE HANDLING
// ============================================

async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const mediaUrlInput = document.getElementById('media-url');
    const sendButton = document.getElementById('send-button');

    const messageType = document.querySelector('input[name="message-type"]:checked').value;
    const message = messageInput.value.trim();
    const mediaUrl = mediaUrlInput.value.trim();

    // Validação
    if (!message && !mediaUrl) {
        alert('Digite uma mensagem ou cole uma URL de mídia');
        return;
    }

    if (messageType !== 'text' && !mediaUrl) {
        alert('Cole a URL da mídia para enviar');
        return;
    }

    // Disable button durante envio
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="loading"></span> Enviando...';

    try {
        // Adicionar mensagem do usuário ao chat
        addMessageToChat('user', message, mediaUrl, messageType);

        // Preparar request
        const requestBody = {
            session_id: sessionId,
            message: messageType === 'text' ? message : null,
            message_type: messageType,
            media_url: mediaUrl || null,
            lead_name: currentLead.name || null,
            lead_email: currentLead.email || null,
            metadata: {},
        };

        // Chamar API
        const response = await fetch(`${API_BASE_URL}/chat/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro na API');
        }

        const data = await response.json();

        // Adicionar resposta ao chat
        // Extrair lista de mídia do metadata
        const mediaList = data.metadata?.media || [];
        addMessageToChat('assistant', data.reply, null, 'text', mediaList);

        // Atualizar estado
        updateStateIndicator(data.state);
        updateSessionInfo(data);

        // Salvar no histórico
        messageHistory.push({
            role: 'user',
            content: message,
            media_url: mediaUrl,
            media_type: messageType,
        });
        messageHistory.push({
            role: 'assistant',
            content: data.reply,
            media: mediaList,
        });

        // Limpar inputs
        messageInput.value = '';
        mediaUrlInput.value = '';

    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        addMessageToChat('system', `Erro: ${error.message}`);
    } finally {
        // Re-enable button
        sendButton.disabled = false;
        sendButton.innerHTML = 'Enviar ➤';
    }
}

function handleMediaTypeChange() {
    const messageType = document.querySelector('input[name="message-type"]:checked').value;
    const mediaUrlContainer = document.getElementById('media-url-container');
    const messageInputContainer = document.getElementById('message-input-container');

    if (messageType === 'text') {
        mediaUrlContainer.style.display = 'none';
    } else {
        mediaUrlContainer.style.display = 'block';
        mediaUrlInput.placeholder = `Cole a URL do ${messageType === 'audio' ? 'áudio' : 'imagem'} (CDN)`;
    }
}

// ============================================
// CHAT UI
// ============================================

function addMessageToChat(role, content, mediaUrl = null, mediaType = 'text', mediaList = []) {
    const messagesContainer = document.getElementById('messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    let contentHtml = '';

    // Texto
    if (content) {
        contentHtml = `<div class="message-content">${escapeHtml(content)}</div>`;
    }

    // Mídia (lista do backend)
    if (mediaList && mediaList.length > 0) {
        mediaList.forEach(media => {
            if (media.type === 'audio') {
                contentHtml += `
                    <div class="message-media">
                        <audio controls style="width: 100%; margin-top: 8px;">
                            <source src="${escapeHtml(media.url)}" type="audio/mp4">
                            Seu navegador não suporta áudio.
                        </audio>
                        <div style="font-size: 0.75rem; color: #666; margin-top: 4px;">
                            🎵 Áudio
                        </div>
                    </div>
                `;
            } else if (media.type === 'image') {
                contentHtml += `
                    <div class="message-media">
                        <img src="${escapeHtml(media.url)}" alt="Imagem" style="max-width: 100%; border-radius: 8px; margin-top: 8px;">
                        <div style="font-size: 0.75rem; color: #666; margin-top: 4px;">
                            🖼️ Imagem
                        </div>
                    </div>
                `;
            }
        });
    } else if (mediaUrl) {
        // Fallback para URL única
        if (mediaType === 'audio') {
            contentHtml += `
                <div class="message-media">
                    <audio controls style="width: 100%; margin-top: 8px;">
                        <source src="${escapeHtml(mediaUrl)}" type="audio/mp4">
                        Seu navegador não suporta áudio.
                    </audio>
                </div>
            `;
        } else if (mediaType === 'image') {
            contentHtml += `
                <div class="message-media">
                    <img src="${escapeHtml(mediaUrl)}" alt="Imagem" style="max-width: 100%; border-radius: 8px; margin-top: 8px;">
                </div>
            `;
        }
    }

    messageDiv.innerHTML = contentHtml;
    messagesContainer.appendChild(messageDiv);

    // Scroll para o final
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// STATE & INFO
// ============================================

function updateStateIndicator(state) {
    const indicator = document.getElementById('state-indicator');
    indicator.textContent = `Estado: ${state}`;
    indicator.className = `state-indicator state-${state}`;
}

function updateSessionInfo(data) {
    const infoContainer = document.getElementById('session-info');

    const metadata = data.metadata || {};

    infoContainer.innerHTML = `
        <p><strong>Lead ID:</strong> ${data.lead_id ? data.lead_id.slice(0, 8) + '...' : 'N/A'}</p>
        <p><strong>Conversation ID:</strong> ${data.conversation_id ? data.conversation_id.slice(0, 8) + '...' : 'N/A'}</p>
        <p><strong>Estado:</strong> ${data.state}</p>
        <p><strong>Ações:</strong> ${data.actions?.length > 0 ? data.actions.join(', ') : 'Nenhuma'}</p>
        ${metadata.latency_ms ? `<p><strong>Latência:</strong> ${metadata.latency_ms}ms</p>` : ''}
        ${metadata.model_used ? `<p><strong>Modelo:</strong> ${metadata.model_used}</p>` : ''}
        ${metadata.state_before ? `<p><strong>Estado anterior:</strong> ${metadata.state_before}</p>` : ''}
    `;
}

// ============================================
// UTILS
// ============================================

function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substring(2, 10) + 
           Math.random().toString(36).substring(2, 10);
}

function clearConversation() {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = `
        <div class="message system-message">
            <div class="message-content">
                Conversa limpa. Inicie uma nova mensagem.
            </div>
        </div>
    `;
    messageHistory = [];
}

function newSession() {
    sessionId = generateSessionId();
    localStorage.setItem('sdr_session_id', sessionId);
    document.getElementById('session-id').textContent = `Session: ${sessionId.slice(0, 8)}...`;
    
    clearConversation();
    updateStateIndicator('NEW');
    document.getElementById('session-info').innerHTML = '<p>Nenhuma informação disponível ainda.</p>';
    
    addMessageToChat('system', 'Nova sessão iniciada!');
}
