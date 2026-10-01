(() => {
  const nav = document.getElementById("nav");
  const toggle = document.getElementById("navToggle");
  const progressBar = document.getElementById("progressBar");
  const header = document.querySelector(".site-header");
  const mobileCta = document.getElementById("mobileCta");
  const FORM_URL =
    "https://docs.google.com/forms/d/e/1FAIpQLSfhcioxkbEsuFzJdh6Y6_9OJ4WNXc0jF4H0DJFr2zky8aZArA/viewform?usp=header";

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });

    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });

    document.addEventListener("click", (e) => {
      if (!nav.classList.contains("is-open")) return;
      if (nav.contains(e.target) || toggle.contains(e.target)) return;
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  const onScroll = () => {
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    const pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
    if (progressBar) progressBar.style.width = `${pct}%`;
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 12);
    if (mobileCta) mobileCta.classList.toggle("is-show", window.scrollY > 280);
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -36px 0px" }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  }

  if ("requestIdleCallback" in window) {
    requestIdleCallback(() => {
      const link = document.createElement("link");
      link.rel = "prefetch";
      link.href = FORM_URL;
      document.head.appendChild(link);
    });
  }

  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());
})();
