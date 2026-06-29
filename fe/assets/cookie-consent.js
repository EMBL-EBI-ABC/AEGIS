/* ==========================================================================
   AEGIS Data Portal — Cookie-consent banner

   Gates Google Analytics (GA4) behind explicit consent, as required by the
   portal privacy notice. Consent defaults to "denied" in the gtag bootstrap
   (see app.py); this script shows a first-visit banner and flips
   analytics_storage to "granted" only when the visitor accepts.

   Plain vanilla JS, auto-served by Dash from assets/. Deliberately decoupled
   from Dash callbacks so it runs before Dash hydrates and needs no server
   round-trip. State lives in localStorage under "aegis-cookie-consent"
   ("granted" | "denied" | unset).
   ========================================================================== */
(function () {
  "use strict";

  var STORAGE_KEY = "aegis-cookie-consent";
  var BANNER_ID = "aegis-cookie-banner";
  var PRIVACY_NOTICE_URL = "/assets/privacy-notice.pdf";

  function getChoice() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function setChoice(value) {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch (e) {
      /* storage unavailable (private mode etc.) — banner just won't persist */
    }
  }

  function removeBanner() {
    var el = document.getElementById(BANNER_ID);
    if (el && el.parentNode) {
      el.parentNode.removeChild(el);
    }
  }

  function accept() {
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", { analytics_storage: "granted" });
    }
    setChoice("granted");
    removeBanner();
  }

  function reject() {
    // Consent already defaults to denied in the gtag bootstrap; just record the
    // choice so the banner doesn't reappear, and make sure it's denied if the
    // visitor is changing a prior "granted" choice within this page load.
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", { analytics_storage: "denied" });
    }
    setChoice("denied");
    removeBanner();
  }

  function buildBanner() {
    var banner = document.createElement("div");
    banner.id = BANNER_ID;
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-label", "Cookie consent");
    banner.setAttribute("aria-live", "polite");

    var text = document.createElement("p");
    text.className = "aegis-cookie-text";
    text.appendChild(
      document.createTextNode(
        "We use Google Analytics cookies to understand how the portal is used " +
          "and improve it. They are only set if you accept. See our "
      )
    );

    var link = document.createElement("a");
    link.className = "aegis-cookie-link";
    link.href = PRIVACY_NOTICE_URL;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "privacy notice ↗";
    text.appendChild(link);
    text.appendChild(document.createTextNode("."));

    var actions = document.createElement("div");
    actions.className = "aegis-cookie-actions";

    var rejectBtn = document.createElement("button");
    rejectBtn.type = "button";
    rejectBtn.className = "aegis-cookie-btn aegis-cookie-btn--reject";
    rejectBtn.textContent = "Reject";
    rejectBtn.addEventListener("click", reject);

    var acceptBtn = document.createElement("button");
    acceptBtn.type = "button";
    acceptBtn.className = "aegis-cookie-btn aegis-cookie-btn--accept";
    acceptBtn.textContent = "Accept";
    acceptBtn.addEventListener("click", accept);

    actions.appendChild(rejectBtn);
    actions.appendChild(acceptBtn);

    banner.appendChild(text);
    banner.appendChild(actions);
    return banner;
  }

  function showBanner() {
    if (document.getElementById(BANNER_ID)) {
      return; // already visible
    }
    document.body.appendChild(buildBanner());
  }

  // Re-open the banner regardless of any stored choice. Used by the footer
  // "Cookie preferences" link so visitors can change or withdraw consent.
  window.aegisShowCookieBanner = function () {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {}
    showBanner();
  };

  function init() {
    if (!getChoice()) {
      showBanner();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // The footer link is rendered by Dash, which hydrates after this script runs,
  // so use event delegation rather than binding the element directly.
  document.addEventListener("click", function (event) {
    var target = event.target;
    if (target && target.id === "cookie-preferences-link") {
      event.preventDefault();
      window.aegisShowCookieBanner();
    }
  });
})();
