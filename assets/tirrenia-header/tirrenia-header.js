class TirreniaHeader extends HTMLElement {
  static get observedAttributes() {
    return ["locale"];
  }

  constructor() {
    super();
    this.languageOrder = ["en", "it", "nl"];
    this.copy = {
      it: {
        currentLanguage: "Italiano",
        events: "Eventi",
      },
      en: {
        currentLanguage: "English (Standard)",
        events: "Events",
      },
      nl: {
        currentLanguage: "Nederlands",
        events: "Events",
      },
    };
    this.handleScroll = this.handleScroll.bind(this);
  }

  connectedCallback() {
    this.render();
    this.bindEvents();
    this.syncLocale();
    this.handleScroll();
    window.addEventListener("scroll", this.handleScroll, { passive: true });
  }

  disconnectedCallback() {
    window.removeEventListener("scroll", this.handleScroll);
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "locale" && oldValue !== newValue && this.isConnected) {
      this.syncLocale();
    }
  }

  get locale() {
    const locale = this.getAttribute("locale") || "en";
    return this.languageOrder.includes(locale) ? locale : "en";
  }

  set locale(value) {
    this.setAttribute("locale", value);
  }

  render() {
    const homeHref = this.getAttribute("home-href") || "#top";
    const eventsHref = this.getAttribute("events-href") || "#story";
    const logoSrc = this.getAttribute("logo-src") || "assets/tirrenia-eu-logo.webp";
    const social = {
      facebook: this.getAttribute("facebook-href") || "/website/social/facebook",
      instagram: this.getAttribute("instagram-href") || "/website/social/instagram",
      youtube: this.getAttribute("youtube-href") || "/website/social/youtube",
      tiktok: this.getAttribute("tiktok-href") || "/website/social/tiktok",
    };

    this.innerHTML = `
      <header class="site-header">
        <nav class="desktop-nav navbar navbar-expand-lg navbar-light o_colored_level o_cc d-none d-lg-block pt-3 shadow-sm" aria-label="Main">
          <div id="o_main_nav" class="header-container o_main_nav flex-wrap container">
            <div class="desktop-top-row o_header_hide_on_scroll d-grid align-items-center w-100 o_grid_header_3_cols pb-3">
              <ul class="navbar-nav align-items-center gap-1">
                <li>
                  <div class="o_header_social_links">
                    <div class="social-links s_social_media o_not_editable oe_unmovable oe_unremovable" aria-label="Social links" data-snippet="s_social_media" data-name="Social Media">
                      <h5 class="s_social_media_title d-none">Follow us</h5>
                      <a href="${social.facebook}" class="s_social_media_facebook o_nav-link_secondary nav-link m-0 p-0 text-decoration-none" target="_blank" aria-label="Facebook" style="color: rgb(59, 89, 153)">
                        <i class="fa fa-facebook fa-stack p-1 o_editable_media" aria-hidden="true"></i>
                      </a>
                      <a href="${social.instagram}" class="s_social_media_instagram o_nav-link_secondary nav-link m-0 p-0 text-decoration-none" target="_blank" aria-label="Instagram" style="color: rgb(207, 40, 114)">
                        <i class="fa fa-instagram fa-stack p-1 o_editable_media" aria-hidden="true"></i>
                      </a>
                      <a href="${social.youtube}" class="o_nav-link_secondary nav-link m-0 p-0 text-decoration-none s_social_media_youtube" target="_blank" aria-label="YouTube" style="color: rgb(255, 0, 0)">
                        <i class="fa fa-stack p-1 o_editable_media fa-youtube-play" aria-hidden="true"></i>
                      </a>
                      <a href="${social.tiktok}" class="o_nav-link_secondary nav-link m-0 p-0 text-decoration-none s_social_media_tiktok" target="_blank" aria-label="TikTok" style="color: rgb(0, 0, 0)">
                        <i class="fa fa-stack p-1 o_editable_media fa-tiktok" aria-hidden="true"></i>
                      </a>
                    </div>
                  </div>
                </li>
              </ul>
              <a class="brand-lockup navbar-brand logo mx-auto mw-100" href="${homeHref}" aria-label="Tirrenia home">
                <span role="img" aria-label="Logo of Tirrenia" title="Tirrenia">
                  <img class="img img-fluid" src="${logoSrc}" width="95" height="40" alt="Tirrenia" />
                </span>
              </a>
              <ul class="navbar-nav align-items-center gap-1 flex-wrap justify-content-end ms-auto">
                <li data-name="Language Selector" class="o_header_language_selector">
                  <div class="language-holder js_language_selector dropdown d-print-none">
                    <button class="language-pill border-0 dropdown-toggle o_navlink_background btn text-reset" type="button" data-language-pill>
                      <span data-header-i18n="currentLanguage"></span>
                    </button>
                  </div>
                </li>
              </ul>
            </div>
            <div class="d-flex w-100 justify-content-start">
              <ul role="menu" id="top_menu" class="main-menu nav navbar-nav top_menu pb-0">
                <li role="presentation" class="nav-item">
                  <a role="menuitem" href="${eventsHref}" class="nav-link" data-header-i18n="events"></a>
                </li>
              </ul>
            </div>
          </div>
        </nav>
        <nav class="mobile-nav" aria-label="Mobile">
          <div class="mobile-container">
            <div class="mobile-main">
              <a class="mobile-brand" href="${homeHref}" aria-label="Tirrenia home">
                <img src="${logoSrc}" alt="Tirrenia" />
              </a>
            </div>
            <button class="mobile-toggle" type="button" aria-label="Toggle navigation" data-mobile-toggle>
              <span class="navbar-toggler-icon"></span>
            </button>
          </div>
          <div class="mobile-drawer" data-mobile-drawer>
            <button class="mobile-close" type="button" aria-label="Close" data-mobile-close>&times;</button>
            <a class="drawer-link" href="${eventsHref}" data-header-i18n="events"></a>
            <div class="social-links" aria-label="Mobile social links">
              <a href="${social.facebook}" aria-label="Facebook" target="_blank" style="color: rgb(59, 89, 153)">
                <i class="fa fa-facebook fa-stack p-1 o_editable_media" aria-hidden="true"></i>
              </a>
              <a href="${social.instagram}" aria-label="Instagram" target="_blank" style="color: rgb(207, 40, 114)">
                <i class="fa fa-instagram fa-stack p-1 o_editable_media" aria-hidden="true"></i>
              </a>
              <a href="${social.youtube}" aria-label="YouTube" target="_blank" style="color: rgb(255, 0, 0)">
                <i class="fa fa-stack p-1 o_editable_media fa-youtube-play" aria-hidden="true"></i>
              </a>
              <a href="${social.tiktok}" aria-label="TikTok" target="_blank" style="color: rgb(0, 0, 0)">
                <i class="fa fa-stack p-1 o_editable_media fa-tiktok" aria-hidden="true"></i>
              </a>
            </div>
            <button class="language-pill" type="button" data-language-pill-mobile>
              <span data-header-i18n="currentLanguage"></span>
            </button>
          </div>
        </nav>
      </header>
    `;
  }

  bindEvents() {
    this.querySelectorAll("[data-language-pill], [data-language-pill-mobile]").forEach((button) => {
      button.addEventListener("click", () => this.cycleLocale());
    });

    const mobileDrawer = this.querySelector("[data-mobile-drawer]");
    this.querySelector("[data-mobile-toggle]")?.addEventListener("click", () => {
      mobileDrawer?.classList.add("is-open");
    });
    this.querySelector("[data-mobile-close]")?.addEventListener("click", () => {
      mobileDrawer?.classList.remove("is-open");
    });
    mobileDrawer?.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => mobileDrawer.classList.remove("is-open"));
    });
  }

  cycleLocale() {
    const nextIndex = (this.languageOrder.indexOf(this.locale) + 1) % this.languageOrder.length;
    const locale = this.languageOrder[nextIndex];
    this.locale = locale;
    this.dispatchEvent(
      new CustomEvent("tirrenia:localechange", {
        bubbles: true,
        detail: { locale },
      }),
    );
  }

  syncLocale() {
    const copy = this.copy[this.locale] || this.copy.en;
    this.querySelectorAll("[data-header-i18n]").forEach((node) => {
      const key = node.getAttribute("data-header-i18n");
      node.textContent = copy[key] || "";
    });
  }

  handleScroll() {
    this.querySelector(".site-header")?.classList.toggle("is-compact", window.scrollY > 80);
  }
}

customElements.define("tirrenia-header", TirreniaHeader);
