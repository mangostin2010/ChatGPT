document.addEventListener('DOMContentLoaded', function () {
    function setAppHeight() {
        const doc = document.documentElement;
        doc.style.setProperty('--app-height', `${window.innerHeight}px`);
    }
    window.addEventListener('resize', setAppHeight);
    setAppHeight();
    
    const MODEL_LIST = window.MODEL_LIST || [
        {"label": "GPT 4.1", "desc": "기본 모델", "value": "openrouter:openai/gpt-4.1"}
    ];

    const initialPrompts = [
        "무슨 작업을 하고 계세요?", "오늘 어떤 도움이 필요하신가요?", "궁금한 점을 물어보세요!",
        "AI에게 무엇이든 물어보세요.", "지금 하고 싶은 일은 무엇인가요?", "오늘의 목표는 무엇인가요?",
        "무엇을 도와드릴까요?", "어떤 프로젝트를 진행 중이신가요?", "생각나는 질문이 있으신가요?",
        "AI와 함께 시작해볼까요!"
    ];

    const chatInput = document.getElementById('chat-input');
    const sendButton = document.querySelector('.send-btn');
    const messagesContainer = document.querySelector('.chat-messages-container');
    const chatArea = document.querySelector('.chat-area');
    const chatContentWrapper = document.querySelector('.chat-content-wrapper');
    const initialPrompt = document.querySelector('.initial-prompt');
    const initialPromptTextEl = document.getElementById('initial-prompt-text');
    const newChatBtn = document.querySelector('.new-chat-btn');
    const chatListUl = document.getElementById('chat-list');
    
    let currentChatId = null;
    let isCreatingNewChat = false;
    let isSendingMessage = false;
    let selectedModel = localStorage.getItem('selectedModel') || 'openrouter:openai/gpt-4.1';

    const sidebar = document.querySelector('.sidebar');
    const sidebarToggleBtn = document.querySelector('.sidebar-toggle-btn');
    const sidebarCloseBtn = document.querySelector('.sidebar-close-btn');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');

    const md = window.markdownit({
        highlight: function (str, lang) {
            if (lang && hljs.getLanguage(lang)) { try { return hljs.highlight(str, { language: lang }).value; } catch (__) {} }
            return '';
        },
        breaks: true,
        linkify: true
    });
    
    function updateChatAreaState() {
        const hasMessages = messagesContainer.children.length > 0;
        // chatArea 대신 chatContentWrapper를 사용하도록 변경
        if (hasMessages) {
            chatContentWrapper.classList.remove('is-empty');
        } else {
            chatContentWrapper.classList.add('is-empty');
            // 랜덤 프롬프트 텍스트 설정
            const randomIdx = Math.floor(Math.random() * initialPrompts.length);
            if (initialPromptTextEl) {
                initialPromptTextEl.textContent = initialPrompts[randomIdx];
            }
        }
    }

    function isMobile() {
        return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.body.classList.add('dark');
            themeToggleBtn.innerHTML = `<svg class="theme-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="m12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`;
        } else {
            document.body.classList.remove('dark');
            themeToggleBtn.innerHTML = `<svg class="theme-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
        }
        const hljsTheme = document.getElementById('hljs-theme');
        if (hljsTheme) {
            hljsTheme.href = theme === 'dark'
                ? "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github-dark.min.css"
                : "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css";
        }
    }

    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    themeToggleBtn.addEventListener('click', function() {
        const isDark = document.body.classList.toggle('dark');
        const newTheme = isDark ? 'dark' : 'light';
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    });

    window.addEventListener('popstate', function(event) {
        const chatId = (event.state && event.state.chatId) || null;
        if (chatId) {
            selectChat(chatId);
        } else {
            showInitialPrompt();
        }
    });

    let autoScroll = true;
    messagesContainer.addEventListener('scroll', function() {
        const threshold = 30;
        autoScroll = (messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < threshold);
    });

    if (sidebarToggleBtn && sidebar) { sidebarToggleBtn.addEventListener('click', () => sidebar.classList.add('open')); }
    if (sidebarCloseBtn && sidebar) { sidebarCloseBtn.addEventListener('click', () => sidebar.classList.remove('open')); }
    window.addEventListener('resize', () => { if (window.innerWidth > 900) sidebar.classList.remove('open'); });

    const modelSelector = document.querySelector('.model-selector');
    const selectedModelLabel = document.getElementById('selected-model-label');
    const modelModal = document.getElementById('model-modal');
    const modelCloseBtn = modelModal.querySelector('.model-close-btn');
    const modelList = modelModal.querySelector('.model-list');
    const modelSearchInput = document.getElementById('model-search-input');
    let filteredModels = [...MODEL_LIST];
    
    function filterModels(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        if (!term) {
            filteredModels = [...MODEL_LIST];
        } else {
            filteredModels = MODEL_LIST.filter(model =>
                model.label.toLowerCase().includes(term) ||
                model.desc.toLowerCase().includes(term) ||
                model.value.toLowerCase().includes(term)
            );
        }
        renderModelList();
    }
    
    // [수정] renderModelList 함수 (하이라이트 기능 제거)
    function renderModelList() {
        modelList.innerHTML = '';
        
        if (filteredModels.length === 0) {
            modelList.innerHTML = `
                <div class="no-results">
                    <div class="no-results-icon">🔍</div>
                    <div>검색 결과가 없습니다</div>
                </div>
            `;
            return;
        }
        
        filteredModels.forEach(model => {
            const opt = document.createElement('div');
            opt.className = 'model-option' + (model.value === selectedModel ? ' selected' : '');
            opt.dataset.value = model.value;
            
            // 하이라이트 로직을 제거하고 원래 텍스트를 그대로 사용
            opt.innerHTML = `
                <span class="model-name">${model.label}</span>
                <span class="model-desc">${model.desc}</span>
            `;
            
            opt.addEventListener('click', function(e) {
                selectedModel = model.value;
                localStorage.setItem('selectedModel', selectedModel);
                selectedModelLabel.textContent = model.label;
                closeModelPanel();
            });
            
            modelList.appendChild(opt);
        });
    }

    function openModelPanel() {
        filteredModels = [...MODEL_LIST];
        modelSearchInput.value = '';
        renderModelList();
        modelModal.style.display = 'flex';
    }

    function closeModelPanel() {
        modelModal.style.display = 'none';
    }

    modelSearchInput.addEventListener('input', e => filterModels(e.target.value));
    modelSearchInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (filteredModels.length > 0) {
                const firstModel = filteredModels[0];
                selectedModel = firstModel.value;
                localStorage.setItem('selectedModel', selectedModel);
                selectedModelLabel.textContent = firstModel.label;
                closeModelPanel();
            }
        } else if (e.key === 'Escape') {
            closeModelPanel();
        }
    });

    modelSelector.addEventListener('click', e => { e.stopPropagation(); openModelPanel(); });
    modelCloseBtn.addEventListener('click', closeModelPanel);
    modelModal.querySelector('.modal-backdrop').addEventListener('click', closeModelPanel);
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && modelModal.style.display === 'flex') closeModelPanel(); });
    
    function setInitialModelLabel() {
        const found = MODEL_LIST.find(m => m.value === selectedModel);
        selectedModelLabel.textContent = found ? found.label : 'GPT-4.1';
    }
    setInitialModelLabel();

    function updateChatListActiveState(activeChatId) {
        chatListUl.querySelectorAll('li').forEach(item => {
            item.classList.toggle('active', item.dataset.chatId === activeChatId);
        });
    }

    function loadChatList() {
        fetch('/get-chat-list')
            .then(res => res.json())
            .then(data => {
                chatListUl.innerHTML = '';
                data.chats.forEach(chat => {
                    const li = document.createElement('li');
                    li.textContent = chat.title || '새 채팅';
                    li.dataset.chatId = chat.chat_id;
                    li.classList.toggle('active', chat.chat_id === currentChatId);
                    li.addEventListener('click', function() {
                        if (currentChatId !== chat.chat_id) selectChat(chat.chat_id);
                    });
                    chatListUl.appendChild(li);
                });
            })
            .catch(err => console.error('채팅 리스트 로드 오류:', err));
    }

    function selectChat(chatId) {
        currentChatId = chatId;
        updateChatListActiveState(chatId);
        history.pushState({chatId: chatId}, '', `/c/${chatId}`);
        fetch(`/get-chat-history?chat_id=${chatId}`)
            .then(res => res.json())
            .then(data => {
                messagesContainer.innerHTML = '';
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        addMessage(msg.role === 'user' ? 'user' : 'ai', msg.content, false);
                    });
                }
                updateChatAreaState(); 
                if (isMobile()) sidebar.classList.remove('open');
            })
            .catch(err => {
                console.error('채팅 히스토리 로드 오류:', err);
                updateChatAreaState();
            });
    }

    function showInitialPrompt() {
        messagesContainer.innerHTML = '';
        currentChatId = null;
        history.pushState({chatId: null}, '', '/');
        updateChatListActiveState(null);
        updateChatAreaState();
    }

    newChatBtn.addEventListener('click', function() {
        if (isCreatingNewChat) return;
        showInitialPrompt();
        loadChatList();
        if (isMobile()) sidebar.classList.remove('open');
    });

    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        sendButton.classList.toggle('active', this.value.trim() !== '');
    });

    chatInput.addEventListener('keydown', function(event) {
        if (isMobile()) return;
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener('click', function() {
        if (chatInput.value.trim() !== '' && !isSendingMessage) {
            sendMessage();
        }
    });

    function addMessage(role, content, isStreaming = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message ' + (role === 'user' ? 'user' : 'ai');
        if (role === 'user') {
            msgDiv.innerHTML = `<div class="message user-message">${content}</div>`;
        } else {
            const messageEl = document.createElement('div');
            messageEl.className = 'message ai-message';
            if (isStreaming) {
                messageEl.id = 'ai-streaming-message';
            } else {
                messageEl.innerHTML = md.render(content);
                messageEl.querySelectorAll('pre code').forEach(hljs.highlightElement);
                if (window.MathJax) MathJax.typesetPromise([messageEl]);
            }
            msgDiv.appendChild(messageEl);
        }
        messagesContainer.appendChild(msgDiv);
        updateChatAreaState();
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return isStreaming ? document.getElementById('ai-streaming-message') : null;
    }

    function sendMessage() {
        if (isSendingMessage) return;
        const userMsg = chatInput.value.trim();
        if (!userMsg) return;
        isSendingMessage = true;
        sendButton.disabled = true;
        addMessage('user', userMsg);
        chatInput.value = '';
        chatInput.style.height = 'auto';
        sendButton.classList.remove('active');
        const aiMessageEl = addMessage('ai', '', true);
        const body = new URLSearchParams({message: userMsg, model: selectedModel});
        if (currentChatId) {
            body.append('chat_id', currentChatId);
        }
        fetch('/send-message', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: body
        }).then(response => {
            const newChatId = response.headers.get('X-Chat-Id');
            if (newChatId && newChatId !== currentChatId) {
                currentChatId = newChatId;
                history.pushState({chatId: newChatId}, '', `/c/${newChatId}`);
                loadChatList();
            }
            if (!response.body) {
                aiMessageEl.innerHTML = md.render("[응답 본문 없음]");
                return;
            }
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiText = "";
            function read() {
                reader.read().then(({done, value}) => {
                    if (done) {
                        aiMessageEl.innerHTML = md.render(aiText);
                        aiMessageEl.querySelectorAll('pre code').forEach(hljs.highlightElement);
                        if (window.MathJax) MathJax.typesetPromise([aiMessageEl]);
                        aiMessageEl.id = '';
                        if (autoScroll) messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        fetch('/save-ai-response', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({response: aiText, chat_id: currentChatId})
                        }).then(() => {
                            fetch('/generate-title', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({chat_id: currentChatId})
                            }).then(res => res.json()).then(titleData => {
                                if (titleData.status === 'success') loadChatList();
                            });
                        }).finally(() => {
                            isSendingMessage = false;
                            sendButton.disabled = false;
                        });
                        return;
                    }
                    aiText += decoder.decode(value, {stream: true});
                    aiMessageEl.innerHTML = md.render(aiText);
                    aiMessageEl.querySelectorAll('pre code').forEach(hljs.highlightElement);
                    if (window.MathJax) MathJax.typesetPromise([aiMessageEl]);
                    if (autoScroll) messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    read();
                });
            }
            read();
        }).catch(err => {
            aiMessageEl.innerHTML = md.render("[AI 응답 오류]");
            console.error('메시지 전송 오류:', err);
            isSendingMessage = false;
            sendButton.disabled = false;
        });
    }

    function initializePage() {
        loadChatList();
        if (window.INITIAL_CHAT_ID) {
            selectChat(window.INITIAL_CHAT_ID);
        } else {
            showInitialPrompt();
        }
    }
    initializePage();

    const settingsModal = document.getElementById('settings-modal');
    const settingsSaveBtn = document.getElementById('settings-save-btn');
    const usernameInput = document.getElementById('username-input');
    document.querySelectorAll('.user-profile-sidebar, .user-profile-main').forEach(el => { el.style.cursor = 'pointer'; el.addEventListener('click', e => { e.stopPropagation(); openSettingsPanel(); }); });
    document.querySelectorAll('.user-profile-sidebar .fa-ellipsis-h').forEach(el => { el.style.cursor = 'pointer'; el.addEventListener('click', e => { e.stopPropagation(); openSettingsPanel(); }); });
    function openSettingsPanel() {
        const theme = localStorage.getItem('theme') || 'light';
        settingsModal.querySelector(`input[name="theme"][value="${theme}"]`).checked = true;
        usernameInput.value = localStorage.getItem('username') || 'User';
        settingsModal.style.display = 'flex';
    }
    function closeSettingsPanel() { settingsModal.style.display = 'none'; }
    settingsModal.querySelector('.settings-close-btn').onclick = closeSettingsPanel;
    settingsModal.querySelector('.settings-modal-backdrop').onclick = closeSettingsPanel;
    settingsSaveBtn.onclick = function() {
        const selectedTheme = settingsModal.querySelector('input[name="theme"]:checked').value;
        localStorage.setItem('theme', selectedTheme);
        applyTheme(selectedTheme);
        const username = usernameInput.value.trim() || 'User';
        localStorage.setItem('username', username);
        document.querySelectorAll('.user-avatar-small, .user-profile-main').forEach(el => { el.textContent = username[0].toUpperCase(); });
        document.querySelectorAll('.user-profile-sidebar span').forEach(el => { el.textContent = username; });
        closeSettingsPanel();
    };
    usernameInput.addEventListener('keydown', e => { if (e.key === 'Enter') settingsSaveBtn.click(); });
    (function(){
        const username = localStorage.getItem('username') || 'User';
        document.querySelectorAll('.user-avatar-small, .user-profile-main').forEach(el => { el.textContent = username[0].toUpperCase(); });
        document.querySelectorAll('.user-profile-sidebar span').forEach(el => { el.textContent = username; });
    })();
});