const implementation = import(`/local/rtrfm-episode-card-impl.js?cache=${Date.now()}`);

class RtrfmEpisodeCardLoader extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._loadImplementation();
  }

  set hass(hass) {
    this._hass = hass;
    this._loadImplementation();
  }

  getCardSize() {
    return this._implementation?.getCardSize?.() || 4;
  }

  async _loadImplementation() {
    if (!this._config || !this._hass) return;
    try {
      const { default: Card } = await implementation;
      if (!this._implementation) {
        this._implementation = new Card();
        this.appendChild(this._implementation);
      }
      this._implementation.setConfig(this._config);
      this._implementation.hass = this._hass;
    } catch (error) {
      this.textContent = `Could not load RTRFM card: ${error.message}`;
    }
  }
}

customElements.define("rtrfm-episode-card", RtrfmEpisodeCardLoader);
