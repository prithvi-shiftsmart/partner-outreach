/**
 * Click-to-copy functionality for partner IDs and other copyable elements.
 */

export function initClipboard() {
  document.body.addEventListener('click', async (e) => {
    const el = e.target.closest('[data-copy]');
    if (!el) return;

    const text = el.dataset.copy;
    try {
      await navigator.clipboard.writeText(text);
      // Visual feedback
      const original = el.textContent;
      el.classList.add('copied');
      el.textContent = 'Copied!';
      setTimeout(() => {
        el.classList.remove('copied');
        el.textContent = original;
      }, 1500);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  });
}
