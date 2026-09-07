(function () {
  "use strict";

  // ---- Nav: reveal past the banner, and highlight the current section ----
  // Works for the side rail and for the top bar if it is switched back on.
  var navs = [document.getElementById("sidenav"), document.getElementById("topnav")].filter(Boolean);
  var hero = document.querySelector(".hero");
  var links = [];
  navs.forEach(function (n) {
    links = links.concat(Array.prototype.slice.call(n.querySelectorAll("a[href^='#']")));
  });
  var sections = links
    .map(function (a) { return document.querySelector(a.getAttribute("href")); })
    .filter(Boolean);

  function onScroll() {
    // reveal once the banner is mostly behind us
    if (hero) {
      var past = window.scrollY > hero.offsetHeight - 120;
      navs.forEach(function (n) { n.classList.toggle("revealed", past); });
    }
    // scroll-spy: last section whose top has passed the marker line
    var marker = window.scrollY + Math.min(220, window.innerHeight * 0.3);
    var current = null;
    sections.forEach(function (s) { if (s.offsetTop <= marker) current = s; });
    // near the very bottom the last section wins even if it is short
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 4) {
      current = sections[sections.length - 1];
    }
    links.forEach(function (a) {
      a.classList.toggle("active", !!current && a.getAttribute("href") === "#" + current.id);
    });
  }

  var ticking = false;
  window.addEventListener("scroll", function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { onScroll(); ticking = false; });
  }, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
  onScroll();

  // ---- Tabs (results ND/WD/ED) ----
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = group.querySelectorAll(".tab");
    var panels = group.querySelectorAll(".tabpanel");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        tabs.forEach(function (t) { t.setAttribute("aria-selected", "false"); });
        panels.forEach(function (p) { p.classList.remove("active"); });
        tab.setAttribute("aria-selected", "true");
        var target = group.querySelector('[data-panel="' + tab.dataset.tab + '"]');
        if (target) target.classList.add("active");
      });
    });
  });

  // ---- BibTeX copy ----
  var copyBtn = document.querySelector(".copy-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var text = document.querySelector("#bibtex-src").textContent;
      navigator.clipboard.writeText(text.trim()).then(function () {
        var original = copyBtn.textContent;
        copyBtn.textContent = "copied";
        setTimeout(function () { copyBtn.textContent = original; }, 1600);
      });
    });
  }

  // ---- Theme toggle ----
  var toggle = document.querySelector(".theme-toggle");
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem("roboreel-theme"); } catch (e) {}
  if (stored === "light" || stored === "dark") root.setAttribute("data-theme", stored);

  function currentIsDark() {
    var attr = root.getAttribute("data-theme");
    if (attr === "dark") return true;
    if (attr === "light") return false;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function paintIcon() {
    if (!toggle) return;
    toggle.textContent = currentIsDark() ? "☀" : "☾";
  }
  paintIcon();
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = currentIsDark() ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("roboreel-theme", next); } catch (e) {}
      paintIcon();
    });
  }
})();
