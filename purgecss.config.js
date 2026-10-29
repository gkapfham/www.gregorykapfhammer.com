/**
 * PurgeCSS configuration for the Bootstrap stylesheets.
 *
 * The purge step in scripts/purge-bootstrap-css-simple.py scans every HTML
 * and JavaScript file in _site and removes selectors that never appear
 * there. Two families of selectors are invisible to that scan because
 * Bootstrap and Popper write them at run time, after the page has loaded:
 *
 *   - data-bs-popper: Bootstrap's dropdown plugin sets this attribute on an
 *     open menu. The rule `.dropdown-menu-end[data-bs-popper]` carries
 *     `right: 0; left: auto`, and without it a right-aligned menu renders
 *     off the right edge of the window instead of under its toggle. This is
 *     what made the Light / Dark / System picker render in the corner,
 *     clipped and too narrow, but only in the built site.
 *   - data-bs-theme / data-popper-placement: the colour-scheme attribute and
 *     the attribute Popper puts on tooltip and popover arrows.
 *
 * The dropdown-menu family is kept as a whole so that the responsive
 * variants (`dropdown-menu-lg-end`, ...) survive as well; Quarto picks one
 * of them depending on the navbar configuration, and they cost well under a
 * kilobyte together.
 *
 * Everything else keeps the default PurgeCSS behaviour, so the purge still
 * removes the thousands of Bootstrap rules that this site never uses.
 */
module.exports = {
  safelist: {
    standard: [
      /^data-bs-popper$/,
      /^data-popper-placement$/,
      /^data-bs-theme$/,
      /^dropdown-menu/,
    ],
  },
};
