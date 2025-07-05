document.addEventListener('DOMContentLoaded', function () {
    const MODEL_LIST = [
        { label: "o4-mini", desc: "빠르고 효율적인 추론 모델", value: "o4-mini" },
        { label: "o3", desc: "가장 강력한 추론 모델", value: "o3" },
        { label: "GPT-4.5 Preview", desc: "가장 크고 강력한 모델", value: "gpt-4.5-preview" },
        { label: "GPT-4.1", desc: "복잡한 작업을 위한 Flagship 모델", value: "gpt-4.1" },
        //{ label: "GPT-4.1 Mini", desc: "지능, 속도의 균형을 갖춘 모델", value: "gpt-4.1-mini" },
        //{ label: "GPT-4.1 Nano", desc: "가장 빠른 모델", value: "gpt-4.1-nano" },
        { label: "GPT-4o", desc: "ChatGPT에 사용된 GPT-4o 모델", value: "gpt-4o" },
        //{ label: "GPT-4o Mini", desc: "빠르고 소형 특화 모델", value: "gpt-4o-mini" },
        { label: "GPT-4o Search", desc: "웹 검색용 GPT 모델", value: "gpt-4o-search-preview" },
        //{ label: "GPT-4o Mini Search", desc: "경량된 웹 검색용 GPT 모델", value: "gpt-4o-mini-search-preview" },
        //{ label: "GPT-4 Turbo", desc: "이전 세대의 고지능 GPT 모델 (할아버지)", value: "gpt-4-turbo" }
    ];

    // 여러 개의 initial prompt 후보
    const initialPrompts = [
        "무슨 작업을 하고 계세요?",
        "오늘 어떤 도움이 필요하신가요?",
        "궁금한 점을 물어보세요!",
        "AI에게 무엇이든 물어보세요.",
        "지금 하고 싶은 일은 무엇인가요?",
        "오늘의 목표는 무엇인가요?",
        "무엇을 도와드릴까요?",
        "어떤 프로젝트를 진행 중이신가요?",
        "생각나는 질문이 있으신가요?",
        "AI와 함께 시작해볼까요!"
    ];

    const chatInput = document.getElementById('chat-input');
    const sendButton = document.querySelector('.send-btn');
    const messagesContainer = document.querySelector('.chat-messages-container');
    const initialPrompt = document.querySelector('.initial-prompt');
    const newChatBtn = document.querySelector('.new-chat-btn');
    const chatListUl = document.getElementById('chat-list');
    let currentChatId = null;
    let isCreatingNewChat = false; // 새 채팅 생성 중 플래그
    let isSendingMessage = false; // 메시지 전송 중 플래그
    let selectedModel = localStorage.getItem('selectedModel') || 'gpt-4.1';

    // 사이드바 토글 관련 요소
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggleBtn = document.querySelector('.sidebar-toggle-btn');
    const sidebarCloseBtn = document.querySelector('.sidebar-close-btn');

    // 테마 토글 버튼
    const themeToggleBtn = document.getElementById('theme-toggle-btn');

    // markdown-it 인스턴스 생성
    const md = window.markdownit({
        highlight: function (str, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(str, { language: lang }).value;
                } catch (__) {}
            }
            return '';
        },
        breaks: true,
        linkify: true
    });

    // 모바일 환경 감지 함수
    function isMobile() {
        return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    // 테마 적용 함수
    function applyTheme(theme) {
        if (theme === 'dark') {
            document.body.classList.add('dark');
            themeToggleBtn.textContent = '☀️';
        } else {
            document.body.classList.remove('dark');
            themeToggleBtn.textContent = '🌙';
        }

        const hljsTheme = document.getElementById('hljs-theme');
        if (hljsTheme) {
            hljsTheme.href = theme === 'dark'
                ? "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github-dark.min.css"
                : "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css";
        }
    }

    // 저장된 테마 불러오기 (default: dark)
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);

    // 토글 버튼 이벤트
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
            // 채팅방이 없을 때 초기화
            showInitialPrompt();
        }
    });

    let autoScroll = true;

    messagesContainer.addEventListener('scroll', function() {
        const threshold = 30;
        if (messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < threshold) {
            autoScroll = true;
        } else {
            autoScroll = false;
        }
    });

    // 랜덤 initial prompt 표시 (페이지 로드 시)
    const initialPromptText = document.getElementById('initial-prompt-text');
    if (initialPromptText) {
        const randomIdx = Math.floor(Math.random() * initialPrompts.length);
        initialPromptText.textContent = initialPrompts[randomIdx];
    }

    // 사이드바 열기
    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener('click', function () {
            sidebar.classList.add('open');
        });
    }
    // 사이드바 닫기
    if (sidebarCloseBtn && sidebar) {
        sidebarCloseBtn.addEventListener('click', function () {
            sidebar.classList.remove('open');
        });
    }
    // 화면 크기 변경 시 사이드바 상태 초기화
    window.addEventListener('resize', function () {
        if (window.innerWidth > 900) {
            sidebar.classList.remove('open');
            sidebar.classList.remove('closed');
        } else {
            sidebar.classList.remove('closed');
        }
    });

    const modelSelector = document.querySelector('.model-selector');
    const modelDropdown = modelSelector.querySelector('.model-dropdown');
    const selectedModelLabel = document.getElementById('selected-model-label');

    // 드롭다운 내용 생성
    function renderModelDropdown() {
        modelDropdown.innerHTML = '';
        MODEL_LIST.forEach(model => {
            const opt = document.createElement('div');
            opt.className = 'model-option' + (model.value === selectedModel ? ' selected' : '');
            opt.dataset.value = model.value;
            opt.innerHTML = `<span class="model-name">${model.label}</span>
                            <span class="model-desc">${model.desc}</span>`;
            opt.addEventListener('click', function(e) {
                selectedModel = model.value;
                localStorage.setItem('selectedModel', selectedModel);
                selectedModelLabel.textContent = model.label;
                renderModelDropdown();
                modelDropdown.style.display = 'none';
            });
            modelDropdown.appendChild(opt);
        });
    }

    // 드롭다운 토글
    modelSelector.addEventListener('click', function(e) {
        e.stopPropagation();
        if (modelDropdown.style.display === 'none' || !modelDropdown.style.display) {
            renderModelDropdown();
            modelDropdown.style.display = 'block';
        } else {
            modelDropdown.style.display = 'none';
        }
    });

    // 바깥 클릭시 닫기
    document.addEventListener('click', function() {
        modelDropdown.style.display = 'none';
    });

    // 초기 라벨 세팅
    function setInitialModelLabel() {
        const found = MODEL_LIST.find(m => m.value === selectedModel);
        selectedModelLabel.textContent = found ? found.label : 'GPT-4.1';
    }
    setInitialModelLabel();


    // 채팅 리스트에서 활성 상태 업데이트
    function updateChatListActiveState(activeChatId) {
        const chatItems = chatListUl.querySelectorAll('li');
        chatItems.forEach(item => {
            if (item.dataset.chatId === activeChatId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    // 채팅 리스트 불러오기
    function loadChatList() {
        fetch('/get-chat-list')
            .then(res => res.json())
            .then(data => {
                chatListUl.innerHTML = '';
                data.chats.forEach(chat => {
                    const li = document.createElement('li');
                    li.textContent = chat.title || '새 채팅';
                    li.dataset.chatId = chat.chat_id;
                    
                    // 현재 선택된 채팅이면 active 클래스 추가
                    if (chat.chat_id === currentChatId) {
                        li.classList.add('active');
                    }
                    
                    li.addEventListener('click', function() {
                        if (currentChatId === chat.chat_id) return;
                        selectChat(chat.chat_id);
                    });
                    chatListUl.appendChild(li);
                });
            })
            .catch(err => {
                console.error('채팅 리스트 로드 오류:', err);
            });
    }

    // 채팅 선택시 해당 채팅 불러오기
    function selectChat(chatId) {
        currentChatId = chatId;
        updateChatListActiveState(chatId);
    
        // URL 변경
        history.pushState({chatId: chatId}, '', `/c/${chatId}`);
    
        fetch(`/get-chat-history?chat_id=${chatId}`)
            .then(res => res.json())
            .then(data => {
                messagesContainer.innerHTML = '';
                messagesContainer.style.justifyContent = 'flex-start';
                messagesContainer.style.alignItems = 'stretch';
    
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        addMessage(msg.role === 'user' ? 'user' : 'ai', msg.content, false);
                    });
                } else {
                    showInitialPrompt();
                }
    
                if (window.innerWidth <= 900) {
                    sidebar.classList.remove('open');
                }
            })
            .catch(err => {
                console.error('채팅 히스토리 로드 오류:', err);
            });
    }

    // 초기 프롬프트 표시 함수
    function showInitialPrompt() {
        const randomIdx = Math.floor(Math.random() * initialPrompts.length);
        messagesContainer.innerHTML = `
            <div class="initial-prompt">
                <h1 id="initial-prompt-text">${initialPrompts[randomIdx]}</h1>
            </div>
        `;
        messagesContainer.style.justifyContent = 'center';
        messagesContainer.style.alignItems = 'center';
    }

    // 현재 채팅이 빈 채팅인지 확인하는 함수
    function isCurrentChatEmpty() {
        const messages = messagesContainer.querySelectorAll('.chat-message');
        return messages.length === 0 || messagesContainer.querySelector('.initial-prompt');
    }

    // 새 채팅 버튼 - 서버에서 빈 채팅 중복 생성 방지
    newChatBtn.addEventListener('click', function() {
        // 이미 새 채팅 생성 중이면 무시
        if (isCreatingNewChat) {
            return;
        }

        // 새 채팅 생성 시작
        isCreatingNewChat = true;
        newChatBtn.disabled = true; // 버튼 비활성화
        
        fetch('/new-chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        })
        .then(res => res.json())
        .then(data => {
            if (data.chat_id) {
                // 새로운 채팅 ID로 전환 (기존 채팅이든 새 채팅이든)
                currentChatId = data.chat_id;
                showInitialPrompt();
                loadChatList();
                
                // 모바일에서 새 채팅 생성 후 사이드바 닫기
                if (window.innerWidth <= 900) {
                    sidebar.classList.remove('open');
                }
            }
        })
        .catch(err => {
            console.error('새 채팅 생성 오류:', err);
        })
        .finally(() => {
            // 새 채팅 생성 완료
            isCreatingNewChat = false;
            newChatBtn.disabled = false; // 버튼 재활성화
        });
    });

    // Textarea 높이 자동 조절
    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';

        if (this.value.trim() !== '') {
            sendButton.classList.add('active');
        } else {
            sendButton.classList.remove('active');
        }
    });

    // 엔터로 전송 (Shift+Enter 줄바꿈) - 모바일에서는 엔터로 전송하지 않음
    chatInput.addEventListener('keydown', function(event) {
        if (isMobile()) return;

        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    // 버튼으로 전송 (PC/모바일 모두)
    sendButton.addEventListener('click', function() {
        if (chatInput.value.trim() !== '' && !isSendingMessage) {
            sendMessage();
        }
    });

    function addMessage(role, content, isStreaming = false) {
        const currentInitialPrompt = document.querySelector('.initial-prompt');
        if (currentInitialPrompt) currentInitialPrompt.style.display = 'none';

        // 메시지 추가 시 중앙 정렬 해제
        messagesContainer.style.justifyContent = 'flex-start';
        messagesContainer.style.alignItems = 'stretch';

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
                messageEl.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
                if (window.MathJax) MathJax.typesetPromise([messageEl]);
            }

            msgDiv.appendChild(messageEl);
        }

        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        if (isStreaming) {
            return document.getElementById('ai-streaming-message');
        }
    }

    function sendMessage() {
        // 이미 메시지 전송 중이면 무시
        if (isSendingMessage) {
            return;
        }

        const userMsg = chatInput.value.trim();
        if (!userMsg) return;

        // 메시지 전송 시작
        isSendingMessage = true;
        sendButton.disabled = true; // 전송 버튼 비활성화
    
        addMessage('user', userMsg);
    
        chatInput.value = '';
        chatInput.style.height = 'auto';
        sendButton.classList.remove('active');
    
        const aiMessageEl = addMessage('ai', '', true);
    
        const url = '/send-message';
        const body = new URLSearchParams({message: userMsg});
        if (currentChatId) body.append('chat_id', currentChatId);
        body.append('model', selectedModel); 
    
        fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: body
        }).then(response => {
            const newChatId = response.headers.get('X-Chat-Id');
            if (newChatId && newChatId !== currentChatId) {
                currentChatId = newChatId;
                // 새 채팅이 생성된 경우에만 리스트 새로고침
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
                        aiMessageEl.querySelectorAll('pre code').forEach((block) => {
                            hljs.highlightElement(block);
                        });
                        if (window.MathJax) MathJax.typesetPromise([aiMessageEl]);
                        aiMessageEl.id = '';
                        // 자동 스크롤 (맨 아래에 있을 때만)
                        if (autoScroll) {
                            messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        }

                        // AI 응답 완료 후 서버에 저장 요청
                        fetch('/save-ai-response', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({response: aiText, chat_id: currentChatId})
                        }).then(() => {
                            // 제목 생성 요청
                            fetch('/generate-title', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({chat_id: currentChatId})
                            }).then(res => res.json()).then(titleData => {
                                if (titleData.status === 'success') {
                                    loadChatList();
                                }
                            });
                        }).finally(() => {
                            isSendingMessage = false;
                            sendButton.disabled = false;
                        });

                        return;
                    }

                    const chunk = decoder.decode(value);
                    aiText += chunk;

                    aiMessageEl.innerHTML = md.render(aiText);
                    aiMessageEl.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                    if (window.MathJax) MathJax.typesetPromise([aiMessageEl]);
                    // 자동 스크롤 (맨 아래에 있을 때만)
                    if (autoScroll) {
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }

                    read();
                });
            }
            read();
        }).catch(err => {
            aiMessageEl.innerHTML = md.render("[AI 응답 오류]");
            console.error('메시지 전송 오류:', err);
        }).finally(() => {
            // 에러 발생 시에도 메시지 전송 상태 해제
            isSendingMessage = false;
            sendButton.disabled = false;
        });
    }

    // 페이지 로드시 초기화
    function initializePage() {
        loadChatList();
        if (window.INITIAL_CHAT_ID && window.INITIAL_CHAT_ID.length > 0) {
            selectChat(window.INITIAL_CHAT_ID);
        } else {
            showInitialPrompt();
        }
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    // 페이지 로드시 실행
    initializePage();
});