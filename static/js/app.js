document.addEventListener("DOMContentLoaded", () => {
  const canTrackPointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (canTrackPointer && !reduceMotion) {
    const glow = document.createElement("div");
    glow.className = "cursor-glow";
    glow.setAttribute("aria-hidden", "true");
    document.body.append(glow);

    let activeTarget = null;
    document.addEventListener("pointermove", (event) => {
      document.documentElement.style.setProperty("--pointer-x", `${event.clientX}px`);
      document.documentElement.style.setProperty("--pointer-y", `${event.clientY}px`);
      glow.classList.add("cursor-glow-visible");
    }, { passive: true });

    document.addEventListener("pointerover", (event) => {
      const target = event.target instanceof Element
        ? event.target.closest(".button, .feature-card, .question-card, .test-card, .problem-card, .quick-links > a, .side-link, .option-row, .recommendation-card")
        : null;
      if (target === activeTarget) return;
      activeTarget?.classList.remove("cursor-vibrate", "cursor-vibrate-card");
      activeTarget = target;
      if (activeTarget) {
        activeTarget.classList.add(
          activeTarget.matches(".feature-card, .question-card, .test-card, .problem-card, .recommendation-card")
            ? "cursor-vibrate-card"
            : "cursor-vibrate",
        );
      }
    });

    document.addEventListener("pointerout", (event) => {
      if (event.relatedTarget) return;
      glow.classList.remove("cursor-glow-visible");
      activeTarget?.classList.remove("cursor-vibrate", "cursor-vibrate-card");
      activeTarget = null;
    });
  }

  const menuToggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".main-nav");
  if (menuToggle && nav) {
    menuToggle.addEventListener("click", () => {
      const open = nav.classList.toggle("nav-open");
      menuToggle.setAttribute("aria-expanded", String(open));
    });
  }

  const revealItems = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries, instance) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          instance.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealItems.forEach((item) => observer.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add("is-visible"));
  }

  document.querySelectorAll(".toast").forEach((toast) => {
    window.setTimeout(() => toast.classList.add("toast-hide"), 5000);
    toast.addEventListener("click", () => toast.classList.add("toast-hide"));
  });

  document.querySelectorAll("[data-confirm]").forEach((button) => {
    button.closest("form")?.addEventListener("submit", (event) => {
      if (!window.confirm(button.dataset.confirm)) event.preventDefault();
    });
  });

  const cards = [...document.querySelectorAll(".test-question")];
  if (cards.length) {
    let active = 0;
    const show = (index) => {
      active = Math.max(0, Math.min(index, cards.length - 1));
      cards.forEach((card, i) => card.classList.toggle("current-question", i === active));
      cards[active].scrollIntoView({ behavior: "smooth", block: "start" });
    };
    document.querySelectorAll(".test-question [data-step]").forEach((button) => {
      button.addEventListener("click", () => show(active + Number(button.dataset.step)));
    });
    cards.forEach((card) => {
      card.querySelectorAll('input[type="radio"]').forEach((input) => input.addEventListener("change", updateQuestionCounts));
      const review = card.querySelector(".review-toggle");
      review?.addEventListener("click", () => {
        const marked = review.getAttribute("aria-pressed") !== "true";
        review.setAttribute("aria-pressed", String(marked));
        review.textContent = marked ? "★ Marked for review" : "☆ Mark for review";
        card.classList.toggle("marked-review", marked);
        updateQuestionCounts();
      });
    });
    show(0);
    updateQuestionCounts();

    const timer = document.querySelector(".timer-card");
    const countdown = document.getElementById("countdown");
    if (timer && countdown) {
      let remaining = Number(timer.dataset.countdown);
      const form = document.getElementById("test-form");
      const updateTimer = () => {
        const mins = Math.floor(Math.max(remaining, 0) / 60);
        const secs = Math.max(remaining, 0) % 60;
        countdown.textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
        if (remaining <= 60) timer.classList.add("timer-warning");
        if (remaining <= 0) {
          form?.requestSubmit();
          return;
        }
        remaining -= 1;
      };
      updateTimer();
      window.setInterval(updateTimer, 1000);
    }

    function updateQuestionCounts() {
      const answered = cards.filter((card) => card.querySelector('input[type="radio"]:checked')).length;
      const reviews = cards.filter((card) => card.classList.contains("marked-review")).length;
      document.getElementById("answered-count").textContent = String(answered);
      document.getElementById("unanswered-count").textContent = String(cards.length - answered);
      document.getElementById("review-count").textContent = String(reviews);
    }
  }

  const hrCards = [...document.querySelectorAll(".hr-card")];
  if (hrCards.length) {
    let active = 0;
    const showHr = (index) => {
      active = Math.max(0, Math.min(index, hrCards.length - 1));
      hrCards.forEach((card, i) => card.classList.toggle("hidden", i !== active));
      document.querySelectorAll("[data-hr-select]").forEach((item, i) => item.classList.toggle("active", i === active));
    };
    document.querySelectorAll("[data-hr-select]").forEach((button) => {
      button.addEventListener("click", () => showHr(Number(button.dataset.hrSelect)));
    });
    document.querySelectorAll("[data-hr-step]").forEach((button) => {
      button.addEventListener("click", () => showHr(active + Number(button.dataset.hrStep)));
    });
  }

  const chartData = document.getElementById("subject-data");
  const canvas = document.getElementById("subjectChart");
  if (chartData && canvas && window.Chart) {
    const scores = JSON.parse(chartData.textContent);
    new Chart(canvas, {
      type: "bar",
      data: {
        labels: scores.map((item) => item.name),
        datasets: [{
          label: "Measured score",
          data: scores.map((item) => item.score),
          backgroundColor: ["#7367f0", "#29b6d1", "#fb7185", "#10b981", "#f7b84b", "#9b8cff"],
          borderRadius: 9,
          maxBarThickness: 30,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 850, easing: "easeOutQuart" },
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, max: 100, grid: { color: "#edf0f7" }, ticks: { callback: (v) => `${v}%` } },
          x: { grid: { display: false }, ticks: { color: "#7c8195" } },
        },
      },
    });
  }

  const timelineData = document.getElementById("timeline-data");
  const timelineCanvas = document.getElementById("timelineChart");
  if (timelineData && timelineCanvas && window.Chart) {
    const values = JSON.parse(timelineData.textContent);
    new Chart(timelineCanvas, {
      type: "line",
      data: {
        labels: values.map((_value, index) => `Test ${index + 1}`),
        datasets: [{
          label: "Score",
          data: values,
          borderColor: "#6d63e9",
          backgroundColor: "#7166f022",
          pointBackgroundColor: "#6d63e9",
          pointRadius: 4,
          fill: true,
          tension: 0.35,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 850, easing: "easeOutQuart" },
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, max: 100, grid: { color: "#edf0f7" }, ticks: { callback: (v) => `${v}%` } },
          x: { grid: { display: false }, ticks: { color: "#7c8195" } },
        },
      },
    });
  }
});
