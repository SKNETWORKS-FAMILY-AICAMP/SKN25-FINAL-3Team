/* ════════════════════════════════════════════════════════
   WORKSTATION LOGIC (API & Interactions)
════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function() {
    // 0. 장고 템플릿 변수 (HTML에서 선언된 window.WS_CONFIG 사용)
    const cfg = window.WS_CONFIG;
    if(!cfg) { console.error("WS_CONFIG가 정의되지 않았습니다."); return; }

    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');
    const fileBtn = document.getElementById('file-btn');
    const fileInput = document.getElementById('file-upload');

    // 스크롤 하단 고정
    function scrollToBottom() { if (chatBox) chatBox.scrollTop = chatBox.scrollHeight; }
    scrollToBottom();

    // 로딩 인디케이터
    function showLoading() {
        const div = document.createElement('div');
        div.id = 'ai-loading'; div.className = 'lf-msg lf-msg-ai';
        div.innerHTML = `
            <div style="display: flex; align-items: center;">
                <span style="color: var(--lf-navy); font-size: 13px; font-weight: 500;">AI 변리사가 분석 중입니다</span>
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>`;
        chatBox.appendChild(div); scrollToBottom();
    }
    function removeLoading() {
        const loadingDiv = document.getElementById('ai-loading');
        if (loadingDiv) loadingDiv.remove();
    }
    function addMessage(role, text) {
        const div = document.createElement('div');
        div.className = 'lf-msg ' + (role === 'assistant' ? 'lf-msg-ai' : 'lf-msg-user');
        div.innerText = text; // XSS 방지를 위해 innerText 사용
        chatBox.appendChild(div); scrollToBottom();
    }

    // 1. 웰컴 메시지 (최초 진입 시)
    if (cfg.messageCount === 0) {
        showLoading();
        fetch(cfg.urls.welcomeApi, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': cfg.csrfToken }
        })
        .then(res => res.json())
        .then(data => {
            removeLoading();
            if (data.status === 'success') {
                addMessage('assistant', data.ai_message);
                updateAiSummary(data.extracted_data);
            }
        }).catch(err => { removeLoading(); console.error(err); });
    }

    // 2. 채팅 전송
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            addMessage('user', message);
            chatInput.value = ''; showLoading();

            fetch(cfg.urls.chatApi, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': cfg.csrfToken },
                body: JSON.stringify({ 'message': message })
            })
            .then(res => res.json())
            .then(data => {
                removeLoading();
                if (data.status === 'success') {
                    addMessage('assistant', data.ai_message);
                    updateAiSummary(data.extracted_data);
                } else alert("오류 발생: " + data.message);
            }).catch(err => { removeLoading(); alert("통신 중 문제가 발생했습니다."); });
        });
    }

    // 3. 파일 업로드
    if (fileBtn && fileInput) {
        fileBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;

            addMessage('user', `📎 [파일 업로드] ${file.name}`);
            showLoading();
            
            const formData = new FormData();
            formData.append('file', file);

            fetch(cfg.urls.uploadApi, {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                removeLoading(); 
                if (data.status === 'success') {
                    addMessage('assistant', data.ai_message);
                    updateAiSummary(data.extracted_data);
                } else alert("파일 처리 실패: " + data.message);
            }).catch(err => { removeLoading(); alert("업로드 중 문제가 발생했습니다."); });
            this.value = '';
        });
    }

    function updateAiSummary(ext) {
        if (!ext) return;
        if (ext.problem) document.getElementById('ext-problem').innerText = ext.problem;
        if (ext.solution) document.getElementById('ext-solution').innerText = ext.solution;
        if (ext.differentiation) document.getElementById('ext-differentiation').innerText = ext.differentiation;
        if (ext.effect) document.getElementById('ext-effect').innerText = ext.effect;
    }

    // 4. 모달 스크립트 (청구항 수정)
    const editBtn = document.getElementById('edit-claims-btn');
    const claimModal = document.getElementById('claim-edit-modal');
    if(editBtn && claimModal) {
        const closeBtn = document.getElementById('close-claim-modal');
        const saveBtn = document.getElementById('modal-save-btn');
        const container = document.getElementById('modal-claims-container');

        editBtn.addEventListener('click', () => {
            claimModal.style.display = 'flex';
            container.innerHTML = '<p style="text-align:center;">데이터를 불러오는 중...</p>';
            
            fetch(cfg.urls.claimsApi)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'empty') {
                    container.innerHTML = `<p style="color:red; text-align:center;">${data.message}</p>`;
                    saveBtn.style.display = 'none';
                } else if (data.status === 'success') {
                    saveBtn.style.display = 'inline-block';
                    container.innerHTML = '';
                    data.claims.forEach(c => {
                        const badge = c.is_dependent ? '[종속항]' : '[독립항]';
                        container.insertAdjacentHTML('beforeend', `
                            <div class="claim-edit-box" data-id="${c.id}" style="background:#fff; padding:15px; border:1px solid #ddd; border-radius:4px;">
                                <h4 style="margin:0 0 10px 0; color:#12100e; font-size:14px;">청구항 ${c.claim_no} <span style="color:#b8935a; font-size:11px;">${badge}</span></h4>
                                <textarea class="claim-content-input" style="width:100%; height:100px; padding:10px; border:1px solid #ddd; outline:none; resize:vertical;">${c.content}</textarea>
                            </div>
                        `);
                    });
                }
            });
        });
        closeBtn.addEventListener('click', () => claimModal.style.display = 'none');
        
        saveBtn.addEventListener('click', () => {
            const originalText = saveBtn.innerText;
            saveBtn.innerText = '저장 중...'; saveBtn.disabled = true;
            const updatedClaims = Array.from(document.querySelectorAll('.claim-edit-box')).map(box => ({
                id: box.getAttribute('data-id'),
                content: box.querySelector('.claim-content-input').value
            }));

            fetch(cfg.urls.claimsApi, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': cfg.csrfToken },
                body: JSON.stringify({ claims: updatedClaims })
            }).then(res=>res.json()).then(data => {
                if(data.status==='success') { alert('저장 완료'); claimModal.style.display='none'; }
                else alert('저장 실패: ' + data.message);
            }).finally(() => { saveBtn.innerText = originalText; saveBtn.disabled = false; });
        });
    }

    // 5. 파이프라인 모달
    const mapModal = document.getElementById('process-map-modal');
    const viewMapBtn = document.getElementById('view-process-btn');
    if(viewMapBtn && mapModal) {
        viewMapBtn.addEventListener('click', () => {
            let currentStep = cfg.hasClaims ? 3 : 2; // 간단한 로직 예시
            renderGraph(currentStep);
            mapModal.style.display = 'flex';
        });
        document.getElementById('close-process-modal').addEventListener('click', () => mapModal.style.display = 'none');
    }

    function renderGraph(currentStep) {
        const steps = [
            { id: 1, name: 'AI 상담', icon: '💬' }, { id: 2, name: '청구항 작성', icon: '📜' },
            { id: 3, name: '도면 작성', icon: '📐' }, { id: 4, name: '발명의 설명', icon: '📝' },
            { id: 5, name: '최종 명세서', icon: '✨' }
        ];
        const container = document.getElementById('dag-container');
        container.innerHTML = '';
        steps.forEach((s, idx) => {
            let nClass = s.id < currentStep ? 'active' : (s.id === currentStep ? 'current' : '');
            container.insertAdjacentHTML('beforeend', `
                <div class="lf-node-wrap">
                    <div class="lf-node ${nClass}">${s.icon}</div>
                    <div class="lf-node-label ${nClass}">${s.name}</div>
                </div>
            `);
            if (idx < steps.length - 1) {
                container.insertAdjacentHTML('beforeend', `<div class="lf-edge ${s.id < currentStep ? 'active' : ''}"></div>`);
            }
        });
    }

    // 모달 배경 클릭 닫기 공통
    window.addEventListener('click', (e) => {
        if(e.target === claimModal) claimModal.style.display = 'none';
        if(e.target === mapModal) mapModal.style.display = 'none';
    });

    const drawBtn = document.getElementById('generate-drawing-btn');
    if (drawBtn) {
        drawBtn.addEventListener('click', function() {
            showLoading(); // "AI가 분석 중입니다..." 애니메이션
            
            fetch(cfg.urls.drawingsApi, {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken }
            })
            .then(res => res.json())
            .then(data => {
                removeLoading();
                if(data.status === 'success') {
                    // 안내 텍스트 출력
                    addMessage('assistant', data.message);
                    
                    // 채팅창에 <img> 태그로 도면 깔끔하게 렌더링 (새로운 라이트 테마 적용)
                    data.drawings.forEach(dwg => {
                        const imgHtml = `
                            <div style="margin-bottom: 15px; text-align: center; background: #fff; padding: 16px; border-radius: 8px; border: 1px solid var(--lf-border); box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                                <strong style="color: var(--lf-navy); display: block; margin-bottom: 12px; font-size: 14px; font-family: var(--lf-serif);">${dwg.title}</strong>
                                <img src="${dwg.url}" alt="${dwg.title}" style="max-width: 100%; border: 1px solid var(--lf-border); border-radius: 4px;">
                            </div>
                        `;
                        chatBox.insertAdjacentHTML('beforeend', imgHtml);
                    });
                    scrollToBottom();
                } else {
                    alert("오류: " + data.message);
                }
            })
            .catch(err => {
                removeLoading();
                console.error(err);
                alert("통신 중 오류가 발생했습니다.");
            });
        });
    }

    // 7. 명세서 작성 버튼 로직
    const specBtn = document.getElementById('generate-spec-btn');
    if (specBtn) {
        specBtn.addEventListener('click', function() {
            showLoading(); 
            
            fetch(cfg.urls.specApi, {
                method: 'POST',
                headers: { 'X-CSRFToken': cfg.csrfToken }
            })
            .then(res => res.json())
            .then(data => {
                removeLoading();
                if(data.status === 'success') {
                    addMessage('assistant', data.message);
                    
                    // 마크다운 내용을 보기 좋게 렌더링 (어두운 색 -> 라이트 문서 테마로 변경)
                    const mdHtml = `
                        <div style="background: #fff; padding: 30px 40px; border-radius: 8px; border: 1px solid var(--lf-border); margin-bottom: 15px; color: var(--lf-body); font-family: 'Malgun Gothic', var(--lf-sans); white-space: pre-wrap; font-size: 14px; min-height: 400px; max-height: 70vh; overflow-y: auto; line-height: 1.8; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                            ${data.markdown}
                        </div>
                    `;
                    chatBox.insertAdjacentHTML('beforeend', mdHtml);
                    scrollToBottom();
                } else {
                    alert("명세서 생성 오류: " + data.message);
                }
            })
            .catch(err => {
                removeLoading();
                console.error(err);
                alert("통신 중 오류가 발생했습니다.");
            });
        });
    }
    
    const mainPaBtn = document.getElementById('main-pa-report-btn');
    
    // 백엔드에서 넘겨준 선기조 데이터가 존재하는 경우
    if (cfg.priorArtJson && cfg.priorArtJson !== 'null' && cfg.priorArtJson.trim() !== '') {
        try {
            window.latestPriorArtData = JSON.parse(cfg.priorArtJson); // 전역 변수에 저장
            
            if (mainPaBtn && window.latestPriorArtData) {
                mainPaBtn.style.display = 'inline-flex'; // 숨겨진 버튼 나타나게 함
                
                mainPaBtn.addEventListener('click', () => {
                    // agent_modal.js 에 선언된 모달 열기 함수 호출
                    if (typeof window.openPriorArtModal === 'function') {
                        window.openPriorArtModal(window.latestPriorArtData);
                    } else {
                        alert("리포트 모듈을 불러오는 중입니다. 잠시 후 다시 시도해주세요.");
                    }
                });
            }
        } catch (e) {
            console.error("선행기술 데이터 파싱 에러:", e);
        }
    }
});