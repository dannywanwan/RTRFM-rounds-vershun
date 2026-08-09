class RtrfmEpisodeCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._episodes = [];
    this._loading = false;
    this._error = "";
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("RTRFM Episodes card requires a media_player entity");
    }
    this._config = {
      title: "The Rounds",
      entity: config.entity,
      roots: ["media-source://media_source", "media-source://media_source/local"],
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._loaded) {
      this._loaded = true;
      this._loadEpisodes();
    }
    this._render();
  }

  getCardSize() {
    return Math.max(3, Math.min(8, (this._episodes.length || 3) + 2));
  }

  async _loadEpisodes() {
    if (!this._hass || !this._config || this._loading) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const items = [];
      const visit = async (media_content_id, depth, inRoundsFolder = false, inQnapFolder = false) => {
        let result;
        try {
          result = await this._hass.callWS({
            type: "media_source/browse_media",
            media_content_id,
          });
        } catch (error) {
          return;
        }
        for (const item of result.children || []) {
          const name = String(item.title || item.media_content_id || "");
          const branch = `${name} ${item.media_content_id || ""}`.toLowerCase();
          const roundsHere = inRoundsFolder || /the rounds/.test(name.toLowerCase());
          const qnapHere = inQnapFolder || /qnap/.test(branch);
          if (/\.(mp3|m4a|mp4|aac|wav|ogg|flac)$/i.test(name)) {
            if (roundsHere && !qnapHere) items.push(item);
          } else if (depth < 6 && item.media_content_id && (item.can_expand || item.media_class === "directory")) {
            await visit(item.media_content_id, depth + 1, roundsHere, qnapHere);
          }
        }
      };
      await Promise.all(this._config.roots.map((root) => visit(root, 0)));
      const audio = items.filter((item) => {
        const name = String(item.title || item.media_content_id || "").toLowerCase();
        return /\.(mp3|m4a|mp4|aac|wav|ogg|flac)$/.test(name);
      });
      const unique = new Map(audio.map((item) => [item.media_content_id, item]));
      this._episodes = [...unique.values()].sort((a, b) => {
        const aLatest = /latest/i.test(a.title || "");
        const bLatest = /latest/i.test(b.title || "");
        if (aLatest !== bLatest) return aLatest ? -1 : 1;
        return String(b.title || "").localeCompare(String(a.title || ""), undefined, {
          numeric: true,
        });
      });
    } catch (error) {
      this._error = error?.message || "Could not load episodes";
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _play(episode) {
    if (!this._hass) return;
    try {
      const resolved = await this._hass.callWS({
        type: "media_source/resolve_media",
        media_content_id: episode.media_content_id,
        expires: 3600,
      });
      const mediaUrl = resolved.url?.startsWith("/")
        ? `${window.location.origin}${resolved.url}`
        : resolved.url;
      await this._hass.callService("media_player", "play_media", {
        entity_id: this._config.entity,
        media_content_id: mediaUrl || episode.media_content_id,
        media_content_type: resolved.mime_type || episode.media_content_type || "audio/mpeg",
      });
    } catch (error) {
      this._error = error?.message || "Could not play episode";
      this._render();
    }
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;
    const rows = this._episodes.length
      ? this._episodes.map((episode) => `
          <button class="episode" data-id="${this._escape(episode.media_content_id)}" title="Play ${this._escape(episode.title)}">
            <span class="play" aria-hidden="true">▶</span>
            <span class="name">${this._escape(episode.title || "Untitled episode")}</span>
          </button>`).join("")
      : `<div class="message">${this._loading ? "Loading episodes..." : "No episodes found"}</div>`;

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; }
        .header { align-items: center; display: flex; justify-content: space-between; padding: 16px 16px 10px; }
        .title { color: var(--primary-text-color); font-size: 1.1rem; font-weight: 500; }
        .refresh { background: none; border: 0; color: var(--secondary-text-color); cursor: pointer; font-size: 1.25rem; height: 36px; width: 36px; }
        .refresh:hover { color: var(--primary-color); }
        .list { display: grid; gap: 1px; padding: 0 8px 8px; }
        .episode { align-items: center; background: var(--card-background-color); border: 0; border-radius: 4px; color: var(--primary-text-color); cursor: pointer; display: flex; font: inherit; gap: 12px; min-height: 48px; padding: 8px; text-align: left; width: 100%; }
        .episode:hover { background: var(--secondary-background-color); }
        .play { color: var(--primary-color); font-size: .9rem; width: 18px; }
        .name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .message { color: var(--secondary-text-color); padding: 12px 16px 18px; }
        .error { color: var(--error-color); padding: 0 16px 14px; }
      </style>
      <ha-card>
        <div class="header">
          <div class="title">${this._escape(this._config.title)}</div>
          <button class="refresh" title="Refresh episodes" aria-label="Refresh episodes">↻</button>
        </div>
        <div class="list">${rows}</div>
        ${this._error ? `<div class="error">${this._escape(this._error)}</div>` : ""}
      </ha-card>`;

    this.shadowRoot.querySelector(".refresh")?.addEventListener("click", () => this._loadEpisodes());
    this.shadowRoot.querySelectorAll(".episode").forEach((button) => {
      button.addEventListener("click", () => {
        const episode = this._episodes.find((item) => item.media_content_id === button.dataset.id);
        if (episode) this._play(episode);
      });
    });
  }

  _escape(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
}

customElements.define("rtrfm-episode-card", RtrfmEpisodeCard);
