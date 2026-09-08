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

  // ---- Tasks: click a card to swap the filmstrip for that task's videos ----
  // File paths are derived from the card's data-task slug, so re-running
  // tools/build_task_videos.sh with a new source clip is all it takes to change
  // what plays here — no markup edit needed.
  var taskCards = document.querySelectorAll(".task-card[data-task]");
  var filmstrip = document.getElementById("task-filmstrip");
  var player = document.getElementById("task-player");
  if (taskCards.length && filmstrip && player) {
    var playerTitle = document.getElementById("task-player-title");
    var humanVid = document.getElementById("task-video-human");
    var robotVid = document.getElementById("task-video-robot");
    var selected = null;

    function labelOf(card) {
      // the card text minus its leading letter badge
      var clone = card.cloneNode(true);
      var badge = clone.querySelector(".letter");
      if (badge) badge.parentNode.removeChild(badge);
      return clone.textContent.trim();
    }

    function showFilmstrip() {
      selected = null;
      taskCards.forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
      [humanVid, robotVid].forEach(function (v) {
        v.pause();
        v.removeAttribute("src");
        v.load();            // drop the buffered clip so it stops downloading
      });
      player.hidden = true;
      filmstrip.hidden = false;
    }

    function showTask(card) {
      var slug = card.dataset.task;
      selected = slug;
      taskCards.forEach(function (c) {
        c.setAttribute("aria-pressed", String(c.dataset.task === slug));
      });
      playerTitle.textContent = labelOf(card);
      humanVid.src = "assets/video/tasks/" + slug + "-human.mp4";
      robotVid.src = "assets/video/tasks/" + slug + "-robot.mp4";
      [humanVid, robotVid].forEach(function (v) {
        v.load();
        var p = v.play();
        if (p && p.catch) p.catch(function () {});   // autoplay blocked: leave it paused
      });
      filmstrip.hidden = true;
      player.hidden = false;
    }

    taskCards.forEach(function (card) {
      card.addEventListener("click", function () {
        if (selected === card.dataset.task) showFilmstrip();
        else showTask(card);
      });
    });

    var closeBtn = document.getElementById("task-player-close");
    if (closeBtn) closeBtn.addEventListener("click", showFilmstrip);
  }

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
