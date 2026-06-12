/* ════════════════════════════════════════════════════════
   AI AGENT & PRIOR ART MODAL LOGIC
════════════════════════════════════════════════════════ */

let claimAbortController = null;

// 1. 터미널 로깅 헬퍼
function appendTerminalLog(type, text, data = null) {
    const terminal = document.getElementById('live-terminal');
    if(!terminal) return;
    const time = new Date().toLocaleTimeString();
    
    let html = `
        <div class="lf-log-line">
            <span class="lf-log-time">[${time}]</span>
            <span class="lf-log-${type}">> ${text}</span>
        </div>`;
    
    if (data) {
        html += `<div class="lf-log-data">${data}</div>`;
    }
    terminal.insertAdjacentHTML('beforeend', html);
    terminal.scrollTop = terminal.scrollHeight;
}

// 2. 노드 상태 변경 헬퍼
function updateNodeStatus(nodeId, status) {
    const node = document.getElementById(nodeId);
    if (!node) return;
    node.classList.remove('lf-node-running', 'lf-node-done', 'lf-node-error');
    if (status === 'running') node.classList.add('lf-node-running');
    if (status === 'done') node.classList.add('lf-node-done');
    if (status === 'error') node.classList.add('lf-node-error');
}

// 3. JSON 뷰어 업데이트
function updateStateViewer(stateObj) {
    const stateContent = document.getElementById('state-json-content');
    if (stateContent) {
        stateContent.textContent = JSON.stringify(stateObj, null, 2);
    }
}

// 4. 선행기술조사 모달 렌더링 함수
window.openPriorArtModal = function(paData) {
    const existing = document.getElementById('pa-result-modal');
    if(existing) existing.remove();

    let riskClass = 'lf-risk-low';
    if(paData.overall_risk.level === 'high') riskClass = 'lf-risk-high';
    if(paData.overall_risk.level === 'medium') riskClass = 'lf-risk-medium';

    let cardsHtml = '';
    paData.candidates.forEach(cand => {
        let candRiskColor = cand.risk_level === 'high' ? '#ef4444' : (cand.risk_level === 'medium' ? 'var(--lf-gold)' : '#059669');
        
        cardsHtml += `
            <div class="lf-pa-card">
                <h4 class="lf-pa-card-title">[${cand.rank}위] ${cand.title}</h4>
                <div class="lf-pa-tags">
                    <span class="lf-pa-tag">출원번호: ${cand.register_number}</span>
                    <span class="lf-pa-tag">유사도: ${(cand.score * 100).toFixed(1)}%</span>
                    <span class="lf-pa-tag" style="color:${candRiskColor}; border-color:${candRiskColor};">리스크: ${cand.risk_level.toUpperCase()}</span>
                </div>
                <div class="lf-pa-summary">
                    <strong>💡 AI 핵심 요약:</strong><br>${cand.summary}
                </div>
                <div style="text-align: right;">
                    ${cand.pdf_s3_url 
                        ? `<a href="${cand.pdf_s3_url}" target="_blank" class="lf-btn-action lf-btn-action--primary">📄 원문 PDF 열기</a>` 
                        : `<span class="lf-pa-tag">🚫 PDF 원문 미제공</span>`
                    }
                </div>
            </div>
        `;
    });

    const modalHtml = `
    <div id="pa-result-modal" class="lf-pa-modal">
        <div class="lf-pa-window">
            <div class="lf-pa-hd">
                <h2 class="lf-pa-title">AI 선행기술조사 리포트</h2>
                <button class="lf-modal-close" onclick="document.getElementById('pa-result-modal').remove()">&times;</button>
            </div>
            <div class="lf-pa-body">
                <div class="lf-risk-box ${riskClass}">
                    <h3>종합 평가: ${paData.overall_risk.summary}</h3>
                    <p>${paData.analysis_summary}</p>
                </div>
                <h3 style="font-family:var(--lf-serif); font-size:18px; margin-bottom:16px;">검색된 주요 선행문헌 (Top ${paData.candidates.length})</h3>
                ${cardsHtml}
            </div>
        </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
};

document.addEventListener('DOMContentLoaded', function() {
    const cfg = window.WS_CONFIG;
    if(!cfg) return;

    const generateClaimsBtn = document.getElementById('generate-claims-btn');
    const agentModal = document.getElementById('ai-agent-modal');
    const terminal = document.getElementById('live-terminal');
    const rewriteNode = document.getElementById('node-rewrite');
    
    // 관제 센터 구동 (청구항 작성 버튼 클릭)
    if (generateClaimsBtn && agentModal) {
        generateClaimsBtn.addEventListener('click', async function() {
            // UI 초기화
            terminal.innerHTML = '<div class="lf-log-line"><span class="lf-log-info">> 시스템 연결 완료. 에이전트 작업을 대기합니다...</span></div>';
            document.querySelectorAll('.lf-agent-node').forEach(n => n.classList.remove('lf-node-running', 'lf-node-done', 'lf-node-error'));
            rewriteNode.style.display = 'none';
            
            agentModal.style.display = 'flex';
            claimAbortController = new AbortController();

            try {
                appendTerminalLog('info', 'Graph 구동 시작...');
                updateNodeStatus('node-summary', 'running');

                const response = await fetch(cfg.urls.generateClaimsApi, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': cfg.csrfToken },
                    signal: claimAbortController.signal
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break; 

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split("\n");
                    buffer = lines.pop(); 

                    for (const line of lines) {
                        if (!line.trim()) continue; 
                        const data = JSON.parse(line); 

                        if (data.step === 'log_and_state') {
                            appendTerminalLog('info', data.log_msg);
                            if (data.state_data) updateStateViewer(data.state_data);
                        }
                        else if (data.step === 'summary') {
                            updateNodeStatus('node-summary', 'done');
                            appendTerminalLog('success', data.message);
                            appendTerminalLog('info', 'Claim Agent로 제어권 전환...');
                            updateNodeStatus('node-claim', 'running');
                        } 
                        else if (data.step === 'claim') {
                            updateNodeStatus('node-claim', 'done');
                            appendTerminalLog('success', data.message);
                            appendTerminalLog('info', 'Examiner Agent로 1차 초안 전송 중...');
                            updateNodeStatus('node-examiner', 'running');
                        } 
                        else if (data.step === 'examiner') {
                            updateNodeStatus('node-examiner', 'done');
                            appendTerminalLog('success', '✅ ' + data.message);
                            rewriteNode.style.display = 'none';
                        } 
                        else if (data.step === 'rewrite') {
                            updateNodeStatus('node-examiner', 'error');
                            appendTerminalLog('error', '❌ 심사관 거절 사유 발견!');
                            appendTerminalLog('warning', 'Rewrite Agent 가동. 보정 루프 진입...', data.message);
                            
                            rewriteNode.style.display = 'block';
                            updateNodeStatus('node-rewrite', 'running');
                            document.getElementById('rewrite-status').innerText = data.message;
                        }
                        else if (data.step === 'rewrite_done') {
                            updateNodeStatus('node-rewrite', 'done');
                            appendTerminalLog('info', '보정 완료. 심사관에게 재심사 요청 중...');
                            updateNodeStatus('node-examiner', 'running');
                        }
                        else if (data.step === 'prior_art_start') {
                            updateNodeStatus('node-prior-art', 'running');
                            appendTerminalLog('info', '[PRIOR_ART] AWS RDS 벡터DB 연결 및 선행기술 검색 가동...');
                        }
                        else if (data.step === 'prior_art_done') {
                            updateNodeStatus('node-prior-art', 'done');
                            appendTerminalLog('success', '[PRIOR_ART] 유사 특허 후보 분석 완료 및 리스크 평가 종료');
                            if (data.prior_art_data) {
                                updateStateViewer({ "prior_art_result": data.prior_art_data });
                                window.latestPriorArtData = data.prior_art_data;
                            }
                        }
                        else if (data.step === 'error') {
                            appendTerminalLog('error', '에러 발생: ' + data.message);
                        }
                        else if (data.step === 'done') {
                            appendTerminalLog('success', '최종 청구항 발행 완료!');
                            
                            const mainPaBtn = document.getElementById('main-pa-report-btn');
                            if (mainPaBtn && window.latestPriorArtData) {
                                mainPaBtn.style.display = 'flex';
                                mainPaBtn.classList.add('lf-btn-action--gold');
                                mainPaBtn.onclick = () => window.openPriorArtModal(window.latestPriorArtData);
                            }
                            
                            // 👇 대망의 "저장해럇!" 버튼 로직 👇
                            setTimeout(() => {
                                // 1. 모달 닫기
                                agentModal.style.display = 'none';
                                
                                // 2. 채팅창에 AI 완성 메시지 추가
                                const chatBox = document.getElementById('chat-box');
                                const msgDiv = document.createElement('div');
                                msgDiv.className = 'lf-msg lf-msg-ai';
                                msgDiv.innerText = data.message_content || '청구항 작성이 성공적으로 완료되었습니다.';
                                chatBox.appendChild(msgDiv);
                                
                                // 3. 귀여운 버튼 생성
                                const saveBtnId = 'save-claim-btn-' + Date.now();
                                const btnHtml = `
                                <div style="text-align: right; margin-top: -10px; margin-bottom: 24px;">
                                    <button id="${saveBtnId}" class="lf-btn-action lf-btn-action--primary" style="padding: 12px 24px; font-size: 12px;">
                                        이 청구항 맘에 들면 저장해럇! 💾
                                    </button>
                                </div>`;
                                
                                chatBox.insertAdjacentHTML('beforeend', btnHtml);
                                chatBox.scrollTop = chatBox.scrollHeight;
                                
                                // 4. 버튼 클릭 이벤트
                                document.getElementById(saveBtnId).addEventListener('click', function() {
                                    const btn = this;
                                    btn.innerText = "저장 중...";
                                    btn.disabled = true;

                                    fetch(cfg.urls.saveClaimsApi, {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json',
                                            'X-CSRFToken': cfg.csrfToken
                                        },
                                        body: JSON.stringify({ claims: data.claims })
                                    })
                                    .then(res => res.json())
                                    .then(saveData => {
                                        if (saveData.status === 'success') {
                                            btn.innerText = "저장 완료! 🎉";
                                            btn.classList.remove('lf-btn-action--primary');
                                            btn.classList.add('lf-btn-action--gold'); 
                                        } else {
                                            alert("저장 실패: " + saveData.message);
                                            btn.innerText = "다시 시도";
                                            btn.disabled = false;
                                        }
                                    })
                                    .catch(err => {
                                        console.error(err);
                                        alert("통신 에러가 발생했습니다.");
                                        btn.innerText = "다시 시도";
                                        btn.disabled = false;
                                    });
                                });

                            }, 1500); 
                        }
                    }
                }
            } catch (error) {
                if (error.name === 'AbortError') {
                    appendTerminalLog('warning', '사용자에 의해 작업이 강제 취소되었습니다.');
                } else {
                    appendTerminalLog('error', '통신 중 오류가 발생했습니다: ' + error.message);
                }
            }
        });
    }

    const minimizeBtn = document.getElementById('modal-minimize-btn');
    if (minimizeBtn) {
        minimizeBtn.addEventListener('click', () => agentModal.style.display = 'none');
    }

    const cancelBtn = document.getElementById('modal-cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            if (claimAbortController) claimAbortController.abort();
            agentModal.style.display = 'none';
            alert('에이전트 파이프라인이 중단되었습니다.');
        });
    }
});