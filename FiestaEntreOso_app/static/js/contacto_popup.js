// Manejo del menú móvil
(function () {
  var btn = document.getElementById("navToggle");
  var links = document.getElementById("navLinks");
  if (btn && links) {
    function setExpanded(expanded) {
      btn.setAttribute("aria-expanded", expanded ? "true" : "false");
    }

    btn.addEventListener("click", function () {
      document.body.classList.toggle("nav-open");
      setExpanded(document.body.classList.contains("nav-open"));
    });

    links.addEventListener("click", function (e) {
      var target = e.target;
      if (target && target.tagName === "A") {
        document.body.classList.remove("nav-open");
        setExpanded(false);
      }
    });
  }
})();

// Pop-up de contacto
(function () {
  var openBtns = [
    document.getElementById("openContacto"),
    document.getElementById("openContactoHero"),
  ].filter(Boolean);
  var modal = document.getElementById("contactoModal");
  var closeBtn = document.getElementById("closeContacto");
  var form = document.getElementById("contactoForm");
  var feedback = document.getElementById("contactoFeedback");

  function openModal() {
    if (!modal) return;
    modal.classList.remove("hidden");
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.add("hidden");
  }

  openBtns.forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      openModal();
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      closeModal();
    });
  }

  if (modal) {
    modal.addEventListener("click", function (e) {
      if (e.target === modal) {
        closeModal();
      }
    });
  }

  if (form && feedback) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      feedback.textContent = "";

      var url = form.getAttribute("action") || "";
      var formData = new FormData(form);

      fetch(url, {
        method: "POST",
        body: formData,
      })
        .then(function (response) {
          if (!response.ok) return response.json().then(Promise.reject);
          return response.json();
        })
        .then(function (data) {
          if (data && data.ok) {
            feedback.style.color = "#16a34a";
            feedback.textContent = "¡Gracias! Te contactaremos pronto.";
            form.reset();
          } else {
            feedback.style.color = "#b91c1c";
            feedback.textContent =
              (data && data.error) ||
              "No pudimos enviar tu mensaje. Intenta nuevamente.";
          }
        })
        .catch(function (err) {
          var msg =
            (err && err.error) ||
            "Ocurrió un error al enviar tu mensaje. Inténtalo de nuevo.";
          feedback.style.color = "#b91c1c";
          feedback.textContent = msg;
        });
    });
  }
})();

