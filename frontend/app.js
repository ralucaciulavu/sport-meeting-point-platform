const fallbackCoordinates = [44.4268, 26.1025];

const form = document.getElementById("registration-form");
const submitButton = document.getElementById("submit-button");
const submitStatus = document.getElementById("submit-status");
const locationStatus = document.getElementById("location-status");
const coordinatesPreview = document.getElementById("coordinates-preview");
const registrationsList = document.getElementById("registrations-list");
const dateInput = document.getElementById("available-date-input");
const addDateButton = document.getElementById("add-date-button");
const selectedDatesContainer = document.getElementById("selected-dates");

let selectedCoordinates = {
  lat: fallbackCoordinates[0],
  lng: fallbackCoordinates[1],
};
let selectedDates = [];

// Initialize the map with a safe fallback so the UI still works without geolocation.
const map = L.map("map", {
  zoomControl: false,
}).setView(fallbackCoordinates, 13);

L.control.zoom({ position: "bottomright" }).addTo(map);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const marker = L.marker(fallbackCoordinates, {
  draggable: true,
}).addTo(map);

function updateCoordinatePreview(lat, lng) {
  coordinatesPreview.textContent = `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`;
}

function setSelectedCoordinates(lat, lng, shouldPan = false) {
  selectedCoordinates = { lat, lng };
  marker.setLatLng([lat, lng]);
  updateCoordinatePreview(lat, lng);

  // Recenter only when the browser provides a location, not on every manual adjustment.
  if (shouldPan) {
    map.setView([lat, lng], 15, { animate: true });
  }
}

setSelectedCoordinates(fallbackCoordinates[0], fallbackCoordinates[1], false);

marker.on("dragend", (event) => {
  const { lat, lng } = event.target.getLatLng();
  setSelectedCoordinates(lat, lng, false);
  locationStatus.textContent = "Pin-ul a fost mutat manual. Aceasta locatie va fi trimisa.";
});

map.on("click", (event) => {
  const { lat, lng } = event.latlng;
  setSelectedCoordinates(lat, lng, false);
  locationStatus.textContent = "Locatia a fost actualizata din harta.";
});

function requestBrowserLocation() {
  if (!navigator.geolocation) {
    locationStatus.textContent = "Browserul nu suporta geolocatie. Folosim o locatie implicita.";
    return;
  }

  // Use a single location lookup on load to prefill the initial marker.
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      setSelectedCoordinates(latitude, longitude, true);
      locationStatus.textContent = "Locatia curenta a fost detectata. Poti muta pin-ul daca vrei alt punct.";
    },
    () => {
      locationStatus.textContent = "Accesul la locatie a fost refuzat sau indisponibil. Poti muta pin-ul manual.";
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
    }
  );
}

function formatDateLabel(dateValue) {
  return new Intl.DateTimeFormat("ro-RO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(`${dateValue}T00:00:00`));
}

function renderSelectedDates() {
  if (!selectedDates.length) {
    selectedDatesContainer.innerHTML = '<p class="empty-state compact">Nu ai selectat inca nicio data.</p>';
    return;
  }

  selectedDatesContainer.innerHTML = selectedDates
    .map((dateValue) => `
      <div class="date-chip">
        <span>${formatDateLabel(dateValue)}</span>
        <button type="button" class="chip-remove" data-date="${dateValue}">×</button>
      </div>
    `)
    .join("");
}

function addSelectedDate() {
  const value = dateInput.value;
  if (!value) {
    submitStatus.textContent = "Selecteaza o data din calendar.";
    return;
  }

  if (!selectedDates.includes(value)) {
    selectedDates = [...selectedDates, value].sort();
    renderSelectedDates();
  }

  submitStatus.textContent = "";
  dateInput.value = "";
}

function registrationCardTemplate(entry) {
  const visibleDates = entry.available_dates
    .map((dateValue) => formatDateLabel(dateValue))
    .join(", ");

  return `
    <article class="registration-card">
      <h3>${entry.display_name}</h3>
      <p><strong>Sport:</strong> ${entry.favorite_sport}</p>
      <p><strong>Date:</strong> ${visibleDates}</p>
      <p><strong>Interval:</strong> ${entry.available_from.slice(0, 5)} - ${entry.available_to.slice(0, 5)}</p>
    </article>
  `;
}

async function loadRegistrations() {
  try {
    const response = await fetch("/api/registrations");
    if (!response.ok) {
      throw new Error("Nu am putut incarca inscrierile.");
    }

    const entries = await response.json();
    if (!entries.length) {
      registrationsList.innerHTML = '<p class="empty-state">Inca nu exista inscrieri.</p>';
      return;
    }

    registrationsList.innerHTML = entries
      .slice(0, 6)
      .map((entry) => registrationCardTemplate(entry))
      .join("");
  } catch (error) {
    registrationsList.innerHTML = `<p class="empty-state">${error.message}</p>`;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  submitStatus.textContent = "Trimitem datele...";

  const formData = new FormData(form);
  if (!selectedDates.length) {
    submitStatus.textContent = "Selecteaza cel putin o data disponibila.";
    submitButton.disabled = false;
    return;
  }

  // Always send the latest coordinates chosen on the map.
  const payload = {
    first_name: formData.get("first_name"),
    last_name: formData.get("last_name"),
    phone_number: formData.get("phone_number"),
    favorite_sport: formData.get("favorite_sport"),
    available_dates: selectedDates,
    available_from: formData.get("available_from"),
    available_to: formData.get("available_to"),
    whatsapp_opt_in: formData.get("whatsapp_opt_in") === "on",
    lat: selectedCoordinates.lat,
    lng: selectedCoordinates.lng,
  };

  try {
    const response = await fetch("/api/registrations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!response.ok) {
      const detail = typeof result.detail === "string"
        ? result.detail
        : "Nu am putut salva inscrierea.";
      throw new Error(detail);
    }

    submitStatus.textContent = "Inscriere salvata. Utilizatorul poate fi folosit ulterior la matching.";
    form.reset();
    selectedDates = [];
    renderSelectedDates();
    await loadRegistrations();
  } catch (error) {
    submitStatus.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});

addDateButton.addEventListener("click", addSelectedDate);

dateInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addSelectedDate();
  }
});

selectedDatesContainer.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }

  const dateValue = target.dataset.date;
  if (!dateValue) {
    return;
  }

  selectedDates = selectedDates.filter((value) => value !== dateValue);
  renderSelectedDates();
});

dateInput.min = new Date().toISOString().split("T")[0];
renderSelectedDates();
requestBrowserLocation();
loadRegistrations();
