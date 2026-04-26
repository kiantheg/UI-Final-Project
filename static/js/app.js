// Small shared entry point for later UI behavior.
document.addEventListener("DOMContentLoaded", () => {
  document.body.dataset.jsReady = "true";

  const dialogueBubbles = document.querySelectorAll("[data-typewriter]");

  dialogueBubbles.forEach((bubble) => {
    const fullText = bubble.dataset.typewriter || bubble.textContent.trim();

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      bubble.textContent = fullText;
      return;
    }

    bubble.textContent = "";

    let index = 0;
    const tick = () => {
      bubble.textContent = fullText.slice(0, index);
      index += 1;

      if (index <= fullText.length) {
        window.setTimeout(tick, 22);
      }
    };

    tick();
  });

  const sliders = document.querySelectorAll("[data-level-slider]");

  sliders.forEach((slider) => {
    const levels = JSON.parse(slider.dataset.levels || "[]");
    const target = slider.dataset.target;
    const hidden = document.querySelector(`[data-slider-hidden-for="${target}"]`);
    const output = document.querySelector(`[data-slider-output-for="${target}"]`);
    const labels = document.querySelectorAll(`[data-slider-label-for="${target}"]`);

    function syncSlider() {
      const index = Number(slider.value);
      const level = levels[index] || levels[0];

      if (hidden) {
        hidden.value = level;
      }

      if (output) {
        output.textContent = level.charAt(0).toUpperCase() + level.slice(1);
      }

      labels.forEach((label) => {
        label.classList.toggle("is-active", label.dataset.level === level);
      });
    }

    slider.addEventListener("input", syncSlider);
    slider.addEventListener("change", syncSlider);
    syncSlider();
  });
});
