/* ════════════════════════════════════════════════════════
   PYPI — Parallax & Scroll Reveal
════════════════════════════════════════════════════════ */

/* ── Parallax scroll ─────────────────────────────────── */
(function initParallax() {
  const stamp  = document.querySelector('.lf-hero-stamp');
  const deco   = document.querySelector('.lf-hero-deco');
  const floats = document.querySelector('.lf-floats');
  const body   = document.querySelector('.lf-hero-body');
  const ticker = document.querySelector('.lf-hero-ticker');

  function onScroll() {
    const y  = window.scrollY;
    const vh = window.innerHeight;
    if (y > vh) return;

    if (stamp)  stamp.style.transform  = `translateY(${y * 0.25}px)`;
    if (deco)   deco.style.transform   = `translateY(-50%) translateY(${y * -0.12}px)`;
    if (floats) floats.style.transform = `translateY(${y * 0.18}px)`;
    if (body)   body.style.transform   = `translateY(${y * 0.06}px)`;
    if (ticker) ticker.style.transform = `translateY(${y * 0.3}px)`;
  }

  window.addEventListener('scroll', onScroll, { passive: true });
})();

/* ── Scroll reveal (IntersectionObserver) ────────────── */
(function initReveal() {
  const io = new IntersectionObserver(
    entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
    }),
    { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
  );
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
})();
