-- Podcast player shortcode.
--
-- Emits the markup that _include/js/podcast-player.js upgrades into the
-- custom transport, so that a post has one shortcode instead of a block of
-- raw HTML. Returning a single RawBlock also means the markup never runs
-- through the Markdown parser, so blank lines inside it cannot split the
-- block and escaped tags cannot appear in the output.
--
-- Usage:
--   {{< podcast src="https://example.com/episode.mp3"
--       episode="725"
--       title="Danny Yang and Sam Goldman on Pyrefly" >}}
--
-- Arguments:
--   src      required, the audio file
--   title    required, the episode title
--   episode  optional, used to build the kicker line
--   show     optional, defaults to Software Engineering Radio
--   label    optional, replaces the whole kicker line
--   download optional, defaults to src

local DEFAULT_SHOW = "Software Engineering Radio"

-- Read a shortcode keyword argument as a string, treating an empty value as
-- absent so that defaults behave as an author would expect.
local function field(kwargs, name)
  local value = kwargs[name]
  if value == nil then
    return nil
  end
  local text = pandoc.utils.stringify(value)
  if text == "" then
    return nil
  end
  return text
end

-- Escape text destined for an HTML attribute or element.
local function escape(text)
  text = text:gsub("&", "&amp;")
  text = text:gsub("<", "&lt;")
  text = text:gsub(">", "&gt;")
  text = text:gsub('"', "&quot;")
  return text
end

-- The kicker is the small line above the title, for example
-- "Software Engineering Radio · Episode 725".
local function kicker_for(kwargs)
  local label = field(kwargs, "label")
  if label ~= nil then
    return label
  end
  local show = field(kwargs, "show") or DEFAULT_SHOW
  local episode = field(kwargs, "episode")
  if episode ~= nil then
    return show .. " · Episode " .. episode
  end
  return show
end

local TEMPLATE = [[
<div class="pp" data-pp>
  <audio preload="metadata" src="%s"></audio>
  <p class="pp-kicker">%s</p>
  <p class="pp-title">%s</p>

  <div class="pp-row">
    <button class="pp-play" type="button" data-pp-play
      aria-label="Play episode">
      <svg class="pp-ico pp-ico-play" viewBox="0 0 24 24"
        aria-hidden="true" focusable="false">
        <path d="M8 5v14l11-7z"></path>
      </svg>
      <svg class="pp-ico pp-ico-pause" viewBox="0 0 24 24"
        aria-hidden="true" focusable="false">
        <path d="M6 5h4v14H6zm8 0h4v14h-4z"></path>
      </svg>
    </button>

    <div class="pp-body">
      <input class="pp-range" type="range" min="0" max="100"
        step="0.1" value="0" data-pp-range
        aria-label="Seek within the episode">

      <div class="pp-meta">
        <span class="pp-time">
          <span data-pp-current>0:00</span>
          <span class="pp-sep">/</span>
          <span data-pp-duration>--:--</span>
        </span>

        <span class="pp-tools">
          <button class="pp-tool" type="button" data-pp-skip="-15"
            aria-label="Rewind 15 seconds">
            <svg viewBox="0 0 24 24" aria-hidden="true"
              focusable="false">
              <path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"></path>
            </svg>
          </button>
          <button class="pp-tool" type="button" data-pp-skip="30"
            aria-label="Fast forward 30 seconds">
            <svg viewBox="0 0 24 24" aria-hidden="true"
              focusable="false">
              <path d="M13 6v12l8.5-6L13 6zM4 18l8.5-6L4 6v12z"></path>
            </svg>
          </button>
          <button class="pp-tool" type="button" data-pp-rate
            aria-label="Change playback speed">1&times;</button>
          <a class="pp-tool" download href="%s"
            aria-label="Download the MP3 episode"
            title="Download the MP3 episode">
            <svg viewBox="0 0 384 512" aria-hidden="true" focusable="false">
              <path d="M64 0C28.7 0 0 28.7 0 64v384c0 35.3 28.7 64 64
              64h256c35.3 0 64-28.7 64-64V160H256c-17.7 0-32-14.3-32-32V0zm192
              0v128h128zm2 226.3c37.1 22.4 62 63.1 62 109.7s-24.9 87.3-62
              109.7c-7.6 4.6-17.4 2.1-22-5.4s-2.1-17.4 5.4-22c28-16.8 46.6-47.4
              46.6-82.3s-18.6-65.5-46.5-82.3c-7.6-4.6-10-14.4-5.4-22s14.4-10
              22-5.4zm-91.9 30.9c6 2.5 9.9 8.3 9.9 14.8v128c0 6.5-3.9 12.3-9.9
              14.8s-12.9 1.1-17.4-3.5L113.4 376H80c-8.8 0-16-7.2-16-16v-48c0-8.8
              7.2-16 16-16h33.4l35.3-35.3c4.6-4.6 11.5-5.9 17.4-3.5m51
              34.9c6.6-5.9 16.7-5.3 22.6 1.3c10.1 11.2 16.3 26.2 16.3 42.6s-6.2
              31.4-16.3 42.7c-5.9 6.6-16 7.1-22.6 1.3s-7.1-16-1.3-22.6c5.1-5.7
              8.1-13.1 8.1-21.3s-3.1-15.7-8.1-21.3c-5.9-6.6-5.3-16.7
              1.3-22.6z"></path>
            </svg>
          </a>
        </span>
      </div>
    </div>
  </div>
</div>
]]

return {
  ["podcast"] = function(args, kwargs)
    local src = field(kwargs, "src")
    if src == nil then
      error("podcast: the 'src' argument is required")
    end
    local title = field(kwargs, "title")
    if title == nil then
      error("podcast: the 'title' argument is required")
    end
    local download = field(kwargs, "download") or src
    local html = string.format(
      TEMPLATE,
      escape(src),
      escape(kicker_for(kwargs)),
      escape(title),
      escape(download)
    )
    return pandoc.RawBlock("html", html)
  end,
}
