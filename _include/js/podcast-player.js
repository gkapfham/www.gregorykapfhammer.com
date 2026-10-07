<script>
/*
 * Podcast player.
 *
 * Upgrades the markup in [data-pp] blocks into a custom transport for the
 * <audio> element inside them. The native player is kept for playback and
 * hidden, because a real <audio> is more reliable than reimplementing
 * streaming, buffering, and format support in JavaScript, while its UI is
 * impossible to style. This script owns only the presentation layer.
 *
 * Everything is looked up defensively so that a malformed block degrades to
 * an inert player instead of breaking the rest of the page.
 */
(function () {
  "use strict";

  var RATES = [1, 1.25, 1.5, 2];
  var REWIND_SECONDS = 15;
  var FORWARD_SECONDS = 30;

  /* Render seconds as m:ss, or h:mm:ss for long episodes. */
  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) {
      return "--:--";
    }
    var whole = Math.floor(seconds);
    var hours = Math.floor(whole / 3600);
    var minutes = Math.floor((whole % 3600) / 60);
    var secs = whole % 60;
    var pad = function (value) {
      return (value < 10 ? "0" : "") + value;
    };
    if (hours > 0) {
      return hours + ":" + pad(minutes) + ":" + pad(secs);
    }
    return minutes + ":" + pad(secs);
  }

  function setup(root) {
    var audio = root.querySelector("audio");
    if (!audio) {
      return;
    }

    var playButton = root.querySelector("[data-pp-play]");
    var range = root.querySelector("[data-pp-range]");
    var elapsed = root.querySelector("[data-pp-current]");
    var total = root.querySelector("[data-pp-duration]");
    var rateButton = root.querySelector("[data-pp-rate]");

    /* True while the listener is dragging, which suppresses timeupdate so
       that the two do not fight over the slider position. */
    var dragging = false;

    function paintFill(percent) {
      if (range) {
        range.style.setProperty("--pp-fill", percent + "%");
      }
    }

    function duration() {
      var value = audio.duration;
      return isFinite(value) && value > 0 ? value : 0;
    }

    function setPlaying(isPlaying) {
      root.classList.toggle("pp-playing", isPlaying);
      if (!playButton) {
        return;
      }
      playButton.setAttribute(
        "aria-label",
        isPlaying ? "Pause episode" : "Play episode"
      );
      playButton.setAttribute("aria-pressed", isPlaying ? "true" : "false");
    }

    function syncProgress() {
      if (elapsed) {
        elapsed.textContent = formatTime(audio.currentTime);
      }
      var length = duration();
      if (length && total) {
        total.textContent = formatTime(length);
      }
      if (length && range && !dragging) {
        var percent = (audio.currentTime / length) * 100;
        range.value = String(percent);
        paintFill(percent);
      }
    }

    if (playButton) {
      playButton.addEventListener("click", function () {
        if (audio.paused) {
          audio.play();
        } else {
          audio.pause();
        }
      });
    }

    audio.addEventListener("play", function () {
      setPlaying(true);
    });
    audio.addEventListener("pause", function () {
      setPlaying(false);
    });
    audio.addEventListener("ended", function () {
      setPlaying(false);
      syncProgress();
    });
    audio.addEventListener("loadedmetadata", syncProgress);
    audio.addEventListener("durationchange", syncProgress);
    audio.addEventListener("timeupdate", syncProgress);

    if (range) {
      range.addEventListener("pointerdown", function () {
        dragging = true;
      });
      range.addEventListener("input", function () {
        var length = duration();
        var preview = (Number(range.value) / 100) * length;
        if (length && elapsed) {
          elapsed.textContent = formatTime(preview);
        }
        paintFill(Number(range.value));
      });
      /* change fires when the pointer is released, and again on some
         browsers for keyboard interaction, so seeking is idempotent. */
      range.addEventListener("change", function () {
        var length = duration();
        if (length) {
          audio.currentTime = (Number(range.value) / 100) * length;
        }
        dragging = false;
      });
    }

    var skips = root.querySelectorAll("[data-pp-skip]");
    for (var i = 0; i < skips.length; i++) {
      skips[i].addEventListener("click", function () {
        var delta = Number(this.getAttribute("data-pp-skip"));
        if (!isFinite(delta)) {
          return;
        }
        var target = audio.currentTime + delta;
        var length = duration();
        if (length) {
          target = Math.min(target, length);
        }
        audio.currentTime = Math.max(0, target);
      });
    }

    if (rateButton) {
      rateButton.addEventListener("click", function () {
        var index = RATES.indexOf(audio.playbackRate);
        var next = RATES[(index + 1) % RATES.length];
        audio.playbackRate = next;
        rateButton.textContent = next + "\u00d7";
        rateButton.setAttribute(
          "aria-label",
          "Playback speed " + next + " times"
        );
      });
    }

    /* Mark the block as enhanced so the stylesheet swaps the native control
       for the custom transport. */
    root.classList.add("pp-ready");
    setPlaying(false);
    syncProgress();
  }

  function init() {
    var players = window.document.querySelectorAll("[data-pp]");
    for (var i = 0; i < players.length; i++) {
      setup(players[i]);
    }
  }

  window.document.addEventListener("DOMContentLoaded", init);
})();
</script>
