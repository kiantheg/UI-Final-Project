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

  const ingredientChoices = document.querySelectorAll("[data-ingredient-choice]");

  if (ingredientChoices.length) {
    const ingredientMenu = document.querySelector("[data-ingredient-menu]");
    const displayTitle = document.querySelector("[data-ingredient-display-title]");
    const displayImage = document.querySelector("[data-ingredient-display-image]");
    const displayBody = document.querySelector("[data-ingredient-display-body]");
    const displayHighlight = document.querySelector("[data-ingredient-display-highlight]");

    function clearActiveIngredient() {
      ingredientChoices.forEach((item) => {
        item.classList.remove("active");
        item.setAttribute("aria-pressed", "false");
      });

      if (displayTitle) {
        displayTitle.textContent = "Choose an Ingredient";
      }

      if (displayImage) {
        displayImage.src = "";
        displayImage.alt = "";
        displayImage.hidden = true;
      }

      if (displayBody) {
        displayBody.textContent = "Hover over an ingredient on the left to see what it does.";
      }

      if (displayHighlight) {
        displayHighlight.textContent = "";
        displayHighlight.hidden = true;
      }
    }

    function setActiveIngredient(choice) {
      ingredientChoices.forEach((item) => {
        const isActive = item === choice;
        item.classList.toggle("active", isActive);
        item.setAttribute("aria-pressed", String(isActive));
      });

      if (displayTitle) {
        displayTitle.textContent = choice.dataset.ingredientTitle || "";
      }

      if (displayImage) {
        displayImage.src = choice.dataset.ingredientImage || "";
        displayImage.alt = choice.dataset.ingredientTitle || "";
        displayImage.hidden = !choice.dataset.ingredientImage;
      }

      if (displayBody) {
        displayBody.textContent = choice.dataset.ingredientBody || "";
      }

      if (displayHighlight) {
        const highlight = choice.dataset.ingredientHighlight || "";
        displayHighlight.textContent = highlight;
        displayHighlight.hidden = !highlight;
      }
    }

    ingredientChoices.forEach((choice) => {
      choice.addEventListener("mouseenter", () => setActiveIngredient(choice));
      choice.addEventListener("focus", () => setActiveIngredient(choice));
      choice.addEventListener("click", () => setActiveIngredient(choice));
    });

    if (ingredientMenu) {
      ingredientMenu.addEventListener("mouseleave", clearActiveIngredient);
      ingredientMenu.addEventListener("focusout", (event) => {
        if (!ingredientMenu.contains(event.relatedTarget)) {
          clearActiveIngredient();
        }
      });
    }

    clearActiveIngredient();
  }
});
