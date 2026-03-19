const state = {
    token: localStorage.getItem("booking.token") || "",
    user: loadStoredUser(),
    activeModal: null,
};

const elements = {
    landingView: document.getElementById("landingView"),
    cabinetView: document.getElementById("cabinetView"),
    cabinetTitle: document.getElementById("cabinetTitle"),
    cabinetSubtitle: document.getElementById("cabinetSubtitle"),
    sessionState: document.getElementById("sessionState"),
    sessionMeta: document.getElementById("sessionMeta"),
    logoutButton: document.getElementById("logoutButton"),
    modalBackdrop: document.getElementById("modalBackdrop"),
    registerModal: document.getElementById("registerModal"),
    loginModal: document.getElementById("loginModal"),
    registerForm: document.getElementById("registerForm"),
    loginForm: document.getElementById("loginForm"),
    filtersForm: document.getElementById("filtersForm"),
    createRoomForm: document.getElementById("createRoomForm"),
    bookingForm: document.getElementById("bookingForm"),
    roomsList: document.getElementById("roomsList"),
    adminRoomsList: document.getElementById("adminRoomsList"),
    bookingsList: document.getElementById("bookingsList"),
    refreshRoomsButton: document.getElementById("refreshRoomsButton"),
    refreshAdminRoomsButton: document.getElementById("refreshAdminRoomsButton"),
    refreshBookingsButton: document.getElementById("refreshBookingsButton"),
    resetFiltersButton: document.getElementById("resetFiltersButton"),
    toast: document.getElementById("toast"),
};

const roleSections = {
    client: document.querySelectorAll(".client-only"),
    admin: document.querySelectorAll(".admin-only"),
};

init();

function init() {
    bindEvents();
    seedBookingDates();
    syncView();
    if (isAuthenticated()) {
        showCabinet();
        void loadCabinetData();
    }
}

function bindEvents() {
    document.getElementById("openRegisterModalButton").addEventListener("click", () => openModal("registerModal"));
    document.getElementById("openLoginModalButton").addEventListener("click", () => openModal("loginModal"));
    elements.modalBackdrop.addEventListener("click", closeActiveModal);
    document.querySelectorAll("[data-close-modal]").forEach((button) => {
        button.addEventListener("click", closeActiveModal);
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeActiveModal();
        }
    });

    elements.registerForm.addEventListener("submit", handleRegister);
    elements.loginForm.addEventListener("submit", handleLogin);
    elements.logoutButton.addEventListener("click", logout);
    elements.filtersForm.addEventListener("submit", handleClientRoomSearch);
    elements.createRoomForm.addEventListener("submit", handleCreateRoom);
    elements.bookingForm.addEventListener("submit", handleCreateBooking);
    elements.refreshRoomsButton.addEventListener("click", () => void fetchClientRooms(buildRoomQuery()));
    elements.refreshAdminRoomsButton.addEventListener("click", () => void fetchAdminRooms());
    elements.refreshBookingsButton.addEventListener("click", () => void fetchMyBookings());
    elements.resetFiltersButton.addEventListener("click", handleFiltersReset);
}

function loadStoredUser() {
    try {
        return JSON.parse(localStorage.getItem("booking.user") || "null");
    } catch {
        return null;
    }
}

function isAuthenticated() {
    return Boolean(state.token && state.user);
}

function syncView() {
    const authenticated = isAuthenticated();
    if (!authenticated) {
        showLanding();
        closeActiveModal();
        return;
    }

    showCabinet();

    const isAdmin = state.user.role === "admin";
    elements.cabinetTitle.textContent = isAdmin ? "Кабинет администратора" : "Кабинет клиента";
    elements.cabinetSubtitle.textContent = isAdmin
        ? "Администратор управляет списком комнат и контролирует структуру сервиса."
        : "Клиент может искать комнаты, бронировать их и управлять своими бронями.";
    elements.sessionState.textContent = isAdmin ? "Роль: администратор" : "Роль: клиент";
    elements.sessionMeta.textContent = `${state.user.email} · id ${state.user.user_id}`;

    roleSections.client.forEach((section) => section.classList.toggle("hidden", isAdmin));
    roleSections.admin.forEach((section) => section.classList.toggle("hidden", !isAdmin));
}

function showLanding() {
    elements.landingView.classList.remove("hidden");
    elements.cabinetView.classList.add("hidden");
    if (window.location.hash === "#cabinet") {
        history.replaceState(null, "", window.location.pathname);
    }
}

function showCabinet() {
    elements.landingView.classList.add("hidden");
    elements.cabinetView.classList.remove("hidden");
    if (window.location.hash !== "#cabinet") {
        history.replaceState(null, "", `${window.location.pathname}#cabinet`);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadCabinetData() {
    try {
        if (state.user.role === "admin") {
            await fetchAdminRooms();
            return;
        }

        await Promise.all([
            fetchClientRooms(buildRoomQuery()),
            fetchMyBookings(),
        ]);
    } catch (error) {
        console.error("Failed to load cabinet data", error);
    }
}

function openModal(modalId) {
    state.activeModal = modalId;
    elements.modalBackdrop.classList.remove("hidden");
    [elements.registerModal, elements.loginModal].forEach((modal) => {
        modal.classList.add("hidden");
        modal.setAttribute("aria-hidden", "true");
    });

    const modal = elements[modalId];
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
}

function closeActiveModal() {
    state.activeModal = null;
    elements.modalBackdrop.classList.add("hidden");
    [elements.registerModal, elements.loginModal].forEach((modal) => {
        modal.classList.add("hidden");
        modal.setAttribute("aria-hidden", "true");
    });
}

async function handleRegister(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = Object.fromEntries(formData.entries());

    await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
    });

    closeActiveModal();
    event.currentTarget.reset();
    showToast("Регистрация завершена. Теперь войдите в аккаунт.", "success");
}

// async function handleLogin(event) {
//     event.preventDefault();
//     const formData = new FormData(event.currentTarget);
//     const payload = Object.fromEntries(formData.entries());
//     const tokenResponse = await apiRequest("/auth/login", {
//         method: "POST",
//         body: JSON.stringify(payload),
//     });
//
//     const decoded = parseJwt(tokenResponse.access_token);
//     state.token = tokenResponse.access_token;
//     state.user = {
//         email: payload.email,
//         role: decoded.role || "user",
//         user_id: decoded.user_id || "?",
//     };
//
//     localStorage.setItem("booking.token", state.token);
//     localStorage.setItem("booking.user", JSON.stringify(state.user));
//
//     closeActiveModal();
//     event.currentTarget.reset();
//     window.location.hash = "cabinet";
//     window.location.reload();
// }

async function handleLogin(event) {
    event.preventDefault();

    const form = event.currentTarget;

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    const tokenResponse = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
    });

    const decoded = parseJwt(tokenResponse.access_token);
    state.token = tokenResponse.access_token;
    state.user = {
        email: payload.email,
        role: decoded.role || "user",
        user_id: decoded.user_id || "?",
    };

    localStorage.setItem("booking.token", state.token);
    localStorage.setItem("booking.user", JSON.stringify(state.user));

    form.reset();
    closeActiveModal();
    window.location.hash = "cabinet";
    window.location.reload();
}

function logout() {
    state.token = "";
    state.user = null;
    localStorage.removeItem("booking.token");
    localStorage.removeItem("booking.user");
    elements.filtersForm.reset();
    elements.createRoomForm.reset();
    elements.bookingForm.reset();
    seedBookingDates();
    renderClientRooms([]);
    renderAdminRooms([]);
    renderBookings([]);
    syncView();
    showToast("Вы вышли из аккаунта.", "success");
}

function seedBookingDates() {
    const start = new Date();
    start.setMinutes(0, 0, 0);
    start.setHours(start.getHours() + 1);
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    elements.bookingForm.start_time.value = toLocalInputValue(start);
    elements.bookingForm.end_time.value = toLocalInputValue(end);
}

async function handleClientRoomSearch(event) {
    event.preventDefault();
    await fetchClientRooms(buildRoomQuery());
}

function handleFiltersReset() {
    elements.filtersForm.reset();
    void fetchClientRooms({ query: "", availability: false });
}

async function fetchClientRooms(filters = { query: "", availability: false }) {
    const path = filters.availability ? `/rooms/available${filters.query}` : `/rooms/${filters.query}`;
    const rooms = await apiRequest(path);
    renderClientRooms(rooms);
}

async function fetchAdminRooms() {
    const rooms = await apiRequest("/rooms/");
    renderAdminRooms(rooms);
}

function renderClientRooms(rooms) {
    if (!rooms.length) {
        elements.roomsList.innerHTML = '<div class="empty-state">Подходящие комнаты не найдены.</div>';
        return;
    }

    elements.roomsList.innerHTML = rooms.map((room) => `
        <article class="room-card">
            <div>
                <div class="badge">ID ${room.id}</div>
                <h3>${escapeHtml(room.name)}</h3>
            </div>
            <div class="meta-row">
                <span>Вместимость: ${room.capacity}</span>
                <span>Локация: ${escapeHtml(room.location)}</span>
            </div>
            <div class="inline-actions">
                <button type="button" data-room-id="${room.id}" class="use-room-button">Выбрать для брони</button>
            </div>
        </article>
    `).join("");

    elements.roomsList.querySelectorAll(".use-room-button").forEach((button) => {
        button.addEventListener("click", () => {
            elements.bookingForm.room_id.value = button.dataset.roomId;
            elements.bookingForm.scrollIntoView({ behavior: "smooth", block: "center" });
        });
    });
}

function renderAdminRooms(rooms) {
    if (!rooms.length) {
        elements.adminRoomsList.innerHTML = '<div class="empty-state">Комнаты еще не созданы.</div>';
        return;
    }

    elements.adminRoomsList.innerHTML = rooms.map((room) => `
        <article class="room-card">
            <div>
                <div class="badge">ID ${room.id}</div>
                <h3>${escapeHtml(room.name)}</h3>
            </div>
            <div class="meta-row">
                <span>Вместимость: ${room.capacity}</span>
                <span>Локация: ${escapeHtml(room.location)}</span>
            </div>
            <div class="inline-actions">
                <button type="button" data-room-id="${room.id}" class="danger-button delete-room-button">Удалить</button>
            </div>
        </article>
    `).join("");

    elements.adminRoomsList.querySelectorAll(".delete-room-button").forEach((button) => {
        button.addEventListener("click", async () => {
            if (!confirm(`Удалить комнату #${button.dataset.roomId}?`)) {
                return;
            }

            await apiRequest(`/rooms/${button.dataset.roomId}`, { method: "DELETE" }, true);
            showToast("Комната удалена.", "success");
            await fetchAdminRooms();
        });
    });
}

async function handleCreateRoom(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
        name: formData.get("name"),
        capacity: Number(formData.get("capacity")),
        location: formData.get("location"),
    };

    await apiRequest("/rooms/", {
        method: "POST",
        body: JSON.stringify(payload),
    }, true);

    event.currentTarget.reset();
    showToast("Комната создана.", "success");
    await fetchAdminRooms();
}

async function handleCreateBooking(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
        room_id: Number(formData.get("room_id")),
        start_time: toIsoString(formData.get("start_time")),
        end_time: toIsoString(formData.get("end_time")),
    };

    await apiRequest("/bookings/", {
        method: "POST",
        body: JSON.stringify(payload),
    }, true);

    showToast("Бронирование создано.", "success");
    await Promise.all([
        fetchClientRooms(buildRoomQuery()),
        fetchMyBookings(),
    ]);
}

async function fetchMyBookings() {
    const bookings = await apiRequest("/bookings/my", {}, true);
    renderBookings(bookings);
}

function renderBookings(bookings) {
    if (!bookings.length) {
        elements.bookingsList.innerHTML = '<div class="empty-state">Активных бронирований нет.</div>';
        return;
    }

    elements.bookingsList.innerHTML = bookings.map((booking) => `
        <article class="booking-card">
            <div class="badge">Бронь #${booking.id}</div>
            <h3>Комната ${booking.room_id}</h3>
            <div class="meta-row">
                <span>Начало: ${formatDateTime(booking.start_time)}</span>
                <span>Конец: ${formatDateTime(booking.end_time)}</span>
            </div>
            <div class="inline-actions">
                <button type="button" data-booking-id="${booking.id}" class="danger-button cancel-booking-button">Отменить</button>
            </div>
        </article>
    `).join("");

    elements.bookingsList.querySelectorAll(".cancel-booking-button").forEach((button) => {
        button.addEventListener("click", async () => {
            if (!confirm(`Отменить бронирование #${button.dataset.bookingId}?`)) {
                return;
            }

            await apiRequest(`/bookings/${button.dataset.bookingId}`, { method: "DELETE" }, true);
            showToast("Бронирование отменено.", "success");
            await Promise.all([
                fetchClientRooms(buildRoomQuery()),
                fetchMyBookings(),
            ]);
        });
    });
}

function buildRoomQuery() {
    const formData = new FormData(elements.filtersForm);
    const params = new URLSearchParams();
    const capacity = formData.get("capacity");
    const location = formData.get("location");
    const startTime = formData.get("start_time");
    const endTime = formData.get("end_time");

    if (capacity) {
        params.set("capacity", capacity);
    }
    if (location) {
        params.set("location", location);
    }

    if (startTime || endTime) {
        if (!startTime || !endTime) {
            showToast("Для поиска доступности укажите и начало, и конец.", "error");
            return { query: "", availability: false };
        }
        params.set("start_time", toIsoString(startTime));
        params.set("end_time", toIsoString(endTime));
        return { query: `?${params.toString()}`, availability: true };
    }

    return { query: params.size ? `?${params.toString()}` : "", availability: false };
}

async function apiRequest(path, options = {}, withAuth = false) {
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
    };

    if (withAuth) {
        if (!state.token) {
            showToast("Сначала выполните вход.", "error");
            throw new Error("Authentication required");
        }
        headers.Authorization = `Bearer ${state.token}`;
    }

    // console.log(path, options, headers)
    const response = await fetch(path, { ...options, headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const detail = Array.isArray(data.detail)
            ? data.detail.map((item) => item.msg).join("; ")
            : data.detail || "Request failed";
        showToast(detail, "error");
        throw new Error(detail);
    }
    return data;
}

function parseJwt(token) {
    try {
        const payload = token.split(".")[1];
        return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    } catch {
        return {};
    }
}

function toIsoString(value) {
    return new Date(value).toISOString();
}

function toLocalInputValue(date) {
    const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return localDate.toISOString().slice(0, 16);
}

function formatDateTime(value) {
    return new Date(value).toLocaleString("ru-RU", {
        dateStyle: "medium",
        timeStyle: "short",
    });
}

function showToast(message, type = "") {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type}`.trim();
    clearTimeout(showToast.timeoutId);
    showToast.timeoutId = setTimeout(() => {
        elements.toast.className = "toast hidden";
    }, 3200);
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}
