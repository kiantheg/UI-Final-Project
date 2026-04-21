// Small shared entry point for later UI behavior.
$(function () {
  $("body").attr("data-js-ready", "true");

  $("[data-level-slider]").each(function () {
    const $slider = $(this);
    const levels = $slider.data("levels");
    const target = $slider.data("target");
    const $hidden = $(`[data-slider-hidden-for="${target}"]`);
    const $output = $(`[data-slider-output-for="${target}"]`);
    const $labels = $(`[data-slider-label-for="${target}"]`);

    function syncSlider() {
      const index = Number($slider.val());
      const level = levels[index] || levels[0];

      $hidden.val(level);
      $output.text(level.charAt(0).toUpperCase() + level.slice(1));
      $labels.removeClass("is-active");
      $labels.filter(`[data-level="${level}"]`).addClass("is-active");
    }

    $slider.on("input change", syncSlider);
    syncSlider();
  });
});
