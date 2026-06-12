/* ════════════════════════════════════════════════════════
   PYPI — Language Switcher
════════════════════════════════════════════════════════ */
(function initLang() {
  const LANG_MAP = { ko: 'ko', en: 'en', ja: 'ja', zh: 'zh-Hans' };

  function applyLang(code) {
    const display = document.querySelector('[data-lang-display]');
    if (display) display.textContent = code.toUpperCase();

    document.querySelectorAll('.lang-option[data-lang]').forEach(o => {
      o.classList.toggle('active', o.dataset.lang === code);
    });

    document.documentElement.lang = LANG_MAP[code] || 'ko';

    try { localStorage.setItem('pm-lang', code); } catch (_) {}
  }

  /* 버튼 클릭 → 드롭다운 토글 */
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      btn.closest('.lang-switcher').classList.toggle('open');
    });
  });

  /* 외부 클릭 → 닫기 */
  document.addEventListener('click', () => {
    document.querySelectorAll('.lang-switcher.open')
      .forEach(s => s.classList.remove('open'));
  });

  /* 언어 선택 */
  document.querySelectorAll('.lang-option[data-lang]').forEach(o => {
    o.addEventListener('click', e => {
      e.preventDefault();
      applyLang(o.dataset.lang);
      o.closest('.lang-switcher').classList.remove('open');
    });
  });

  /* 저장된 언어 복원 */
  let saved;
  try { saved = localStorage.getItem('pm-lang'); } catch (_) {}
  applyLang(saved || 'ko');
})();
