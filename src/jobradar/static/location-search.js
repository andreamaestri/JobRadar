const locationInput = document.querySelector("#location");
const suggestions = document.querySelector("#location-suggestions");
const searchForm = document.querySelector("#job-search-form");
const downloadButton = document.querySelector("#download-button");
const downloadProgress = document.querySelector("#download-progress");
let timer;
let controller;

function closeSuggestions() {
  suggestions.classList.add("d-none");
  locationInput.setAttribute("aria-expanded", "false");
}

function showSuggestions(items) {
  suggestions.replaceChildren();
  items.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "list-group-item list-group-item-action";
    button.setAttribute("role", "option");
    button.id = `location-option-${index}`;
    button.textContent = item.label;
    button.addEventListener("click", () => {
      locationInput.value = item.value;
      closeSuggestions();
      locationInput.focus();
    });
    suggestions.appendChild(button);
  });
  suggestions.classList.toggle("d-none", items.length === 0);
  locationInput.setAttribute("aria-expanded", String(items.length > 0));
}

async function searchLocations() {
  const query = locationInput.value.trim();
  if (query.length < 2) {
    closeSuggestions();
    return;
  }
  controller?.abort();
  controller = new AbortController();
  try {
    const response = await fetch(`/api/geocode?query=${encodeURIComponent(query)}`, { signal: controller.signal });
    if (!response.ok) throw new Error("Suggestions unavailable");
    showSuggestions(await response.json());
  } catch (error) {
    if (error.name !== "AbortError") closeSuggestions();
  }
}

locationInput.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(searchLocations, 250);
});

locationInput.addEventListener("keydown", event => {
  if (event.key === "Escape") closeSuggestions();
  if (event.key === "ArrowDown") {
    event.preventDefault();
    suggestions.querySelector("button")?.focus();
  }
});

locationInput.addEventListener("focus", () => {
  if (suggestions.children.length) suggestions.classList.remove("d-none");
});
document.addEventListener("click", event => {
  if (!event.target.closest(".location-search")) closeSuggestions();
});

searchForm.addEventListener("submit", () => {
  downloadButton.disabled = true;
  downloadButton.textContent = "Downloading…";
  downloadProgress.classList.remove("d-none");
});
