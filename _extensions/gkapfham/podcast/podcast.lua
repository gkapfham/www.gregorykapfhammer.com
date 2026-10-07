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
          <a class="pp-tool" download href="%s">MP3</a>
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
    local html = string.format(TEMPLATE, escape(src), escape(kicker_for(kwargs)), escape(title), escape(download))
    return pandoc.RawBlock("html", html)
  end,
}
