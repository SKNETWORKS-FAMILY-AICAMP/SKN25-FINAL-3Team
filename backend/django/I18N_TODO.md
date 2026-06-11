# 전체 페이지 i18n (KO/EN/JA/ZH) 작업 현황

## 완료
- [x] `accounts/chat.html` — lang-switcher + data-i18n 태그 + `pmT()`/`pm:i18n` 동적 처리
- [x] `accounts/login.html` — lang-switcher + data-i18n 태그
- [x] `accounts/signup.html` — lang-switcher + data-i18n 태그
- [x] `accounts/dashboard.html` — lang-switcher + data-i18n 태그 (nav_dashboard_label, nav_pipeline_label, nav_ai_dashboard 신규 키 포함, zh 누락분도 추가 완료)
- [x] `accounts/pipeline.html` — lang-switcher + data-i18n 태그 + `pmT('pipe_running')` 동적 처리, 신규 키 33개(pipe_eyebrow/rerun/running/step_*/card_label/ph1-5/loading_*/r_*/status_*/tip_*) ko/en/ja/zh 4개 언어 모두 PM_I18N에 추가 완료

- [x] `accounts/drawing.html` — lang-switcher + data-i18n 태그 + `pmT('drawing_running')` 동적 처리, 신규 키 15개(nav_drawing_label, drawing_*) ko/en/ja/zh 4개 언어 모두 PM_I18N에 추가 완료
  - ⚠️ 참고: 이 템플릿 내 `{% url 'accounts:drawing' %}` 은 어떤 view/urls.py에서도 매칭되지 않는 기존(pre-existing) 깨진 링크입니다. `accounts/drawing.html`을 렌더링하는 view 자체가 없어 이 페이지는 현재 어디서도 호출되지 않는 것으로 보입니다 (i18n 작업과 무관한 기존 이슈, 수정하지 않음).

## 남은 작업
- [ ] `pages/about.html`, `pages/features.html`, `pages/team.html` — i18n 누락분 보완
- [ ] `pages/qna.html` — data-i18n 태그 추가 (한글 텍스트 다수)
- [ ] `pages/insights.html` — data-i18n 태그 추가
- [ ] `pages/agents_overview.html`, `pages/agent_detail.html` — data-i18n 태그 추가
  - `agent_detail.html`은 `accounts/views.py`의 `_AGENT_PAGES` dict에서 동적 렌더링되므로 별도 처리 전략 필요
- [ ] `pages/team_member.html`, `pages/drawing_gallery.html` — data-i18n 태그 추가
- [ ] `accounts/landing.html` — 미태깅 섹션 전수 점검 (현재 nav만 적용)
- [ ] 위 작업에서 새로 생기는 번역 키를 `base.html`의 `PM_I18N` (ko/en/ja/zh)에 추가

## 참고 — i18n 인프라 (base.html)
- `window.PM_I18N = {ko:{...}, en:{...}, ja:{...}, zh:{...}}`
- `window.pmApplyI18n(code)` — 언어 적용. `data-i18n="key"` 텍스트, `data-i18n-attr="속성명"` 속성, `placeholder` 자동 처리, `data-i18n-html`로 innerHTML 처리
- `window.pmT(key)` — 현재 언어 문자열 반환 (JS 동적 텍스트용)
- `pm:i18n` 커스텀 이벤트 — 언어 전환 시 발생, 동적 렌더링 함수 재호출에 사용
- `.lang-switcher` / `.lang-btn` / `.lang-dropdown` / `.lang-option[data-lang]` 마크업 재사용
- 라이트 테마 페이지(login/signup 등)는 `.lf-auth-lang` 같은 별도 색상 오버라이드 필요
