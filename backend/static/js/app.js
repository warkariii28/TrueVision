document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.querySelector(".tv-navbar");
  const revealItems = document.querySelectorAll(".tv-reveal");
  const rotatingWords = document.querySelectorAll("[data-rotate-words]");
  const countItems = document.querySelectorAll("[data-count-to]");
  const tiltCards = document.querySelectorAll("[data-tilt-card]");
  const canUseHoverTilt =
    window.matchMedia &&
    window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  if (navbar) {
    const syncNavbarState = () => {
      navbar.classList.toggle("scrolled", window.scrollY > 40);
    };

    syncNavbarState();
    window.addEventListener("scroll", syncNavbarState, { passive: true });
  }

  if (!revealItems.length) {
    return;
  }

  if (!("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }

        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    {
      threshold: 0.12,
      rootMargin: "0px 0px -30px 0px",
    }
  );

  revealItems.forEach((item) => observer.observe(item));

  rotatingWords.forEach((item) => {
    const words = (item.dataset.rotateWords || "")
      .split(",")
      .map((word) => word.trim())
      .filter(Boolean);

    if (words.length < 2) {
      return;
    }

    let index = 0;
    let isAnimating = false;

    item.classList.add("is-settled");

    const animateWordChange = () => {
      if (isAnimating) {
        return;
      }

      isAnimating = true;
      item.classList.remove("is-entering", "is-settled");
      item.classList.add("is-exiting");

      window.setTimeout(() => {
        index = (index + 1) % words.length;
        item.textContent = words[index];
        item.classList.remove("is-exiting");
        item.classList.add("is-entering");

        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            item.classList.remove("is-entering");
            item.classList.add("is-settled");
          });
        });

        window.setTimeout(() => {
          isAnimating = false;
        }, 440);
      }, 240);
    };

    window.setInterval(animateWordChange, 2200);
  });

  countItems.forEach((item) => {
    const target = Number(item.dataset.countTo || 0);
    if (!Number.isFinite(target) || target <= 0) {
      return;
    }

    const duration = 1200;
    const start = performance.now();

    const tick = (timestamp) => {
      const progress = Math.min((timestamp - start) / duration, 1);
      item.textContent = Math.round(target * progress);
      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    };

    requestAnimationFrame(tick);
  });

  if (!canUseHoverTilt) {
    tiltCards.forEach((card) => {
      card.removeAttribute("data-tilt-card");
    });
    return;
  }

  tiltCards.forEach((card) => {
    card.addEventListener("mousemove", (event) => {
      const rect = card.getBoundingClientRect();
      const rotateY = ((event.clientX - rect.left) / rect.width - 0.5) * 8;
      const rotateX = ((event.clientY - rect.top) / rect.height - 0.5) * -8;
      card.style.transform = `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });
});
