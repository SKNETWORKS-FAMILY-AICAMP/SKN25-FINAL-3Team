/* ════════════════════════════════════════════════════════
   PYPI — News Slider
════════════════════════════════════════════════════════ */
(function initNewsSlider() {
  const track   = document.getElementById('nsTrack');
  const dots    = document.querySelectorAll('.lf-ns-dot');
  const btnPrev = document.getElementById('nsArrowPrev');
  const btnNext = document.getElementById('nsArrowNext');
  if (!track) return;

  const TOTAL   = track.querySelectorAll('.lf-ns-card').length;
  const VISIBLE = getVisible();
  let current   = 0;

  function getVisible() {
    if (window.innerWidth <= 600) return 1;
    if (window.innerWidth <= 900) return 2;
    return 3;
  }

  function maxIdx() { return Math.max(0, TOTAL - getVisible()); }

  function getCardWidth() {
    const card = track.querySelector('.lf-ns-card');
    return card ? card.offsetWidth + 24 : 0;  /* gap = 24px */
  }

  function update() {
    const max = maxIdx();
    current = Math.min(current, max);
    track.style.transform = `translateX(-${current * getCardWidth()}px)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === current));
    if (btnPrev) btnPrev.disabled = current === 0;
    if (btnNext) btnNext.disabled = current === max;
  }

  if (btnPrev) btnPrev.addEventListener('click', () => { if (current > 0)        { current--; update(); } });
  if (btnNext) btnNext.addEventListener('click', () => { if (current < maxIdx()) { current++; update(); } });
  dots.forEach((d, i) => d.addEventListener('click', () => { current = i; update(); }));

  /* 터치 스와이프 */
  let touchX = 0;
  track.addEventListener('touchstart', e => { touchX = e.touches[0].clientX; }, { passive: true });
  track.addEventListener('touchend',   e => {
    const diff = touchX - e.changedTouches[0].clientX;
    if (diff >  50 && current < maxIdx()) { current++; update(); }
    if (diff < -50 && current > 0)        { current--; update(); }
  });

  update();
  window.addEventListener('resize', update);
})();
