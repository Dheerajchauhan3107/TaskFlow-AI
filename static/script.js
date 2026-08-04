document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("darkModeToggle");
    const body = document.body;
    const storageKey = "taskflow_dark_mode";

    const applyTheme = function (isDark) {
        body.classList.toggle("dark", isDark);
        localStorage.setItem(storageKey, isDark ? "true" : "false");

        if (toggleButton) {
            toggleButton.setAttribute("aria-pressed", isDark ? "true" : "false");
            toggleButton.innerHTML = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
        }
    };

    const savedTheme = localStorage.getItem(storageKey);
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialDark = savedTheme === null ? prefersDark : savedTheme === "true";

    applyTheme(initialDark);

    if (toggleButton) {
        toggleButton.addEventListener("click", function () {
            const isDark = !body.classList.contains("dark");
            applyTheme(isDark);
        });
    }
});
