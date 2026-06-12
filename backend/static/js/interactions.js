/* ════════════════════════════════════════════════════════
   PYPI — Count-up & Magnetic Tilt
════════════════════════════════════════════════════════ */

/* ── Count-up animation (Cred bar) ──────────────────── */
(function initCountUp() {
  function countUp(el, target, duration) {
    const start = performance.now();
    (function step(now) {
      const p    = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(ease * target);
      if (p < 1) requestAnimationFrame(step);
    })(start);
  }

  const obs = new IntersectionObserver(
    entries => entries.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.querySelectorAll('[data-count]').forEach(el => {
        countUp(el, parseInt(el.dataset.count, 10), 1600);
      });
      obs.unobserve(e.target);
    }),
    { threshold: 0.5 }
  );

  document.querySelectorAll('.lf-cred').forEach(el => obs.observe(el));
})();

/* ── Magnetic tilt (Feature & Team cards) ────────────── */
(function initMagneticTilt() {
  document.querySelectorAll('.lf-feat, .lf-member').forEach(card => {
    card.addEventListener('mousemove', e => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left)  / r.width  - 0.5;
      const y = (e.clientY - r.top)   / r.height - 0.5;
      card.style.transform  = `perspective(600px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) scale(1.02)`;
      card.style.transition = 'transform .1s ease';
      card.style.zIndex     = '2';
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform  = '';
      card.style.transition = 'transform .4s ease, background .25s';
      card.style.zIndex     = '';
    });
  });
})();
