<script>
/*
 * Theme picker: a Light / Dark / System menu in the Quarto navbar.
 *
 * Quarto ships only a binary toggle, so this script adds a menu that can
 * select a mode explicitly. It drives Quarto's own colour-scheme
 * machinery rather than reimplementing it, so the styling, the syntax
 * highlighting, and the persistence all stay consistent.
 *
 * Quarto records the choice in localStorage under "quarto-color-scheme"
 * using the values "default" (light) and "alternate" (dark). An absent
 * key means "no explicit choice", which makes Quarto follow the
 * operating system because this site sets respect-user-color-scheme.
 *
 * Note on scope: Quarto's inlined "quarto-html-before-body" script
 * declares toggleColorMode with a top-level `const`. That puts it in the
 * global lexical scope, so it is reachable here as a bare identifier but
 * is deliberately not a property of window. If it is ever unavailable we
 * fall back to storing the choice and reloading, so the menu still works.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "quarto-color-scheme";
  var DARK_VALUE = "alternate";
  var LIGHT_VALUE = "default";
  var ITEM_SELECTOR = [
    '.dropdown-item[href$="#light"]',
    '.dropdown-item[href$="#dark"]',
    '.dropdown-item[href$="#system"]',
  ].join(",");

  /* Does the operating system currently ask for a dark scheme? */
  function prefersDark() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  /* The user's stored choice: "light", "dark", or "system". */
  function readMode() {
    var stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === null) {
      return "system";
    }
    return stored === DARK_VALUE ? "dark" : "light";
  }

  /*
   * Record the choice, then repaint. Repainting goes through Quarto's
   * toggleColorMode so that stylesheets, the body class, and the built-in
   * toggle all stay in sync without a page reload. If that function is
   * not reachable we reload instead, which applies the stored choice
   * during startup.
   */
  function applyMode(mode) {
    if (mode === "system") {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(
        STORAGE_KEY,
        mode === "dark" ? DARK_VALUE : LIGHT_VALUE
      );
    }

    var alternate = mode === "system" ? prefersDark() : mode === "dark";
    try {
      toggleColorMode(alternate);
    } catch (error) {
      window.location.reload();
    }
  }

  /* Mark the menu entry that matches the active mode. */
  function markActive(items, mode) {
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var active = item.getAttribute("href").split("#")[1] === mode;
      item.classList.toggle("active", active);
      if (active) {
        item.setAttribute("aria-current", "true");
      } else {
        item.removeAttribute("aria-current");
      }
    }
  }

  /*
   * The entries are anchors whose navigation we cancel, so Bootstrap does
   * not reliably dismiss the menu on its own. Close it explicitly, and
   * tolerate a missing Bootstrap API: the mode has already been applied, so
   * the worst case is a menu that stays open.
   */
  function closeMenu(item) {
    var navItem = item.closest(".nav-item");
    var toggle = navItem && navItem.querySelector(".dropdown-toggle");
    if (!toggle || !window.bootstrap || !window.bootstrap.Dropdown) {
      return;
    }
    try {
      window.bootstrap.Dropdown.getOrCreateInstance(toggle).hide();
    } catch (error) {
      // the menu stays open; the mode change has already been applied
    }
  }

  function init() {
    var items = window.document.querySelectorAll(ITEM_SELECTOR);
    if (items.length === 0) {
      return;
    }

    for (var i = 0; i < items.length; i++) {
      items[i].addEventListener("click", function (event) {
        event.preventDefault();
        var mode = this.getAttribute("href").split("#")[1];
        applyMode(mode);
        markActive(items, readMode());
        closeMenu(this);
      });
    }

    markActive(items, readMode());
  }

  window.document.addEventListener("DOMContentLoaded", init);
})();
</script>
