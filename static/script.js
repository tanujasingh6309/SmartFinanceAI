/* ==========================================================
   SmartFinanceAI — shared front-end behavior (single source)
   Loaded on every page via base.html. Do NOT duplicate any of
   this logic inside individual templates.
   ========================================================== */

document.addEventListener("DOMContentLoaded", function () {

    /* ----------------------------------------------------------
       Theme toggle
       - html + body already carry "light-mode" (if applicable)
         from the two blocking inline scripts in base.html.
       - Here we just sync the switch position on load, and keep
         html + body + localStorage in sync whenever it changes.
    ---------------------------------------------------------- */
    (function () {
        const toggle = document.getElementById("themeToggle");
        if (!toggle) return;

        function isLight() {
            return document.body.classList.contains("light-mode");
        }

        function syncToggleWithTheme() {
            // checked = Dark Mode ON, unchecked = Light Mode ON
            toggle.checked = !isLight();
        }

        // Reflect whatever theme was restored from localStorage,
        // on every page, every time — fixes the switch showing the
        // wrong position after navigating/refreshing on some pages.
        syncToggleWithTheme();

        toggle.addEventListener("change", function () {
            if (toggle.checked) {
                document.body.classList.remove("light-mode");
                document.documentElement.classList.remove("light-mode");
            } else {
                document.body.classList.add("light-mode");
                document.documentElement.classList.add("light-mode");
            }

            try {
                localStorage.setItem(
                    "sfai-theme",
                    isLight() ? "light" : "dark"
                );
            } catch (e) {}
        });
    })();

    /* ----------------------------------------------------------
       Dynamic time-of-day greeting (dashboard only — no-op
       elsewhere since the element won't exist)
    ---------------------------------------------------------- */
    (function () {
        const el = document.getElementById("welcomeGreeting");
        if (!el) return;
        const hour = new Date().getHours();
        let greeting = "Good Evening";
        let icon = "bi-moon-stars-fill";
        if (hour < 12) {
            greeting = "Good Morning";
            icon = "bi-brightness-high-fill";
        } else if (hour < 17) {
            greeting = "Good Afternoon";
            icon = "bi-sun-fill";
        }
        el.innerHTML = '<i class="bi ' + icon + '"></i> ' + greeting;
    })();

    /* ----------------------------------------------------------
       Sidebar active link highlight based on current path
    ---------------------------------------------------------- */
    (function () {
        const links = document.querySelectorAll(".sidebar a[data-nav]");
        const path = window.location.pathname;
        links.forEach(function (link) {
            const target = link.getAttribute("data-nav");
            if (target === path || (target !== "/" && path.startsWith(target))) {
                link.classList.add("active");
            } else if (target === "/" && path === "/") {
                link.classList.add("active");
            }
        });
    })();

    /* ----------------------------------------------------------
       Mobile sidebar open/close
    ---------------------------------------------------------- */
    (function () {
        const sidebar = document.querySelector(".sidebar");
        const toggleBtn = document.getElementById("sidebarToggleBtn");
        const backdrop = document.getElementById("sidebarBackdrop");
        if (!sidebar || !toggleBtn || !backdrop) return;

        function closeSidebar() {
            sidebar.classList.remove("open");
            backdrop.classList.remove("show");
        }

        function openSidebar() {
            sidebar.classList.add("open");
            backdrop.classList.add("show");
        }

        toggleBtn.addEventListener("click", function () {
            sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
        });

        backdrop.addEventListener("click", closeSidebar);

        document.querySelectorAll(".sidebar a[data-nav]").forEach(function (a) {
            a.addEventListener("click", closeSidebar);
        });
    })();

    /* ----------------------------------------------------------
       Scroll reveal animation
    ---------------------------------------------------------- */
    (function () {
        const reveals = document.querySelectorAll(".reveal");
        if (!reveals.length) return;
        const observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12 }
        );
        reveals.forEach(function (el) {
            observer.observe(el);
        });
    })();

    /* ----------------------------------------------------------
       Profile dropdown
    ---------------------------------------------------------- */
    (function () {
        const profileBtn = document.getElementById("profileBtn");
        const profileMenu = document.getElementById("profileMenu");
        if (!profileBtn || !profileMenu) return;

        profileBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            profileMenu.classList.toggle("show");
        });

        profileMenu.addEventListener("click", function (e) {
            e.stopPropagation();
        });

        document.addEventListener("click", function () {
            profileMenu.classList.remove("show");
        });
    })();

    /* ----------------------------------------------------------
       Notification dropdown
    ---------------------------------------------------------- */
    (function () {
        const notificationBtn = document.getElementById("notificationBtn");
        const notificationMenu = document.getElementById("notificationMenu");
        if (!notificationBtn || !notificationMenu) return;

        notificationBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            notificationMenu.classList.toggle("show");

            fetch("/mark_notifications_read").then(function () {
                const badge = document.querySelector(".notification-count");
                if (badge) {
                    badge.style.display = "none";
                }
            });
        });

        document.addEventListener("click", function () {
            notificationMenu.classList.remove("show");
        });
    })();

    /* ----------------------------------------------------------
       KPI counter animation ([data-counter] — used on dashboard,
       income, expense, and any future page)
    ---------------------------------------------------------- */
    (function () {
        const counters = document.querySelectorAll("[data-counter]");
        if (!counters.length) return;

        function animateCounter(el) {
            const target = parseFloat(el.getAttribute("data-counter"));
            if (isNaN(target)) return;
            const suffix = el.getAttribute("data-suffix") || "";
            const duration = 900;
            const start = performance.now();

            function tick(now) {
                const progress = Math.min((now - start) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const value = Math.round(target * eased);
                el.textContent = value.toLocaleString("en-IN") + suffix;
                if (progress < 1) requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        }

        counters.forEach(function (el) {
            const observer = new IntersectionObserver(
                function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            animateCounter(entry.target);
                            observer.unobserve(entry.target);
                        }
                    });
                },
                { threshold: 0.3 }
            );
            observer.observe(el);
        });
    })();

    /* ----------------------------------------------------------
       Chart loading skeleton (only present on pages with charts)
    ---------------------------------------------------------- */
    (function () {
        const skeletons = document.querySelectorAll(".chart-skeleton");
        if (!skeletons.length) return;
        skeletons.forEach(function (el) {
            setTimeout(function () {
                el.classList.add("hide");
            }, 700);
        });
    })();

});