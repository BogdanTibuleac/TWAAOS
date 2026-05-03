const API = (window.location.protocol === "file:" || window.location.port !== "8000")
    ? "http://localhost:8000"
    : "";

const elements = {
    authSection: document.getElementById("sectiune-auth"),
    tasksSection: document.getElementById("sectiune-sarcini"),
    userInfo: document.getElementById("info-utilizator"),
    userEmail: document.getElementById("email-utilizator"),
    logoutButton: document.getElementById("btn-deconectare"),
    registerForm: document.getElementById("form-inregistrare"),
    loginForm: document.getElementById("form-autentificare"),
    registerError: document.getElementById("eroare-inregistrare"),
    registerSuccess: document.getElementById("succes-inregistrare"),
    loginError: document.getElementById("eroare-autentificare"),
    taskForm: document.getElementById("formular-sarcina"),
    taskTitle: document.getElementById("sarcina-titlu"),
    taskDescription: document.getElementById("sarcina-descriere"),
    taskList: document.getElementById("lista-sarcini"),
    reloadButton: document.getElementById("btn-reincarca"),
    totalStat: document.getElementById("stat-total"),
    activeStat: document.getElementById("stat-active"),
    doneStat: document.getElementById("stat-done"),
};

function saveToken(token) {
    localStorage.setItem("token", token);
}

function getToken() {
    return localStorage.getItem("token");
}

function logout() {
    localStorage.removeItem("token");
    updateUI();
}

function parseUserEmail(token) {
    try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        return payload.sub || "";
    } catch {
        return "";
    }
}

function setAlert(element, message, isVisible = true) {
    element.textContent = message;
    element.classList.toggle("d-none", !isVisible);
}

function clearAuthAlerts() {
    setAlert(elements.registerError, "", false);
    setAlert(elements.registerSuccess, "", false);
    setAlert(elements.loginError, "", false);
}

function toggleAuthForm() {
    clearAuthAlerts();
    elements.registerForm.classList.toggle("d-none");
    elements.loginForm.classList.toggle("d-none");
}

function updateUI() {
    const token = getToken();
    const isLoggedIn = Boolean(token);

    elements.authSection.classList.toggle("d-none", isLoggedIn);
    elements.tasksSection.classList.toggle("d-none", !isLoggedIn);
    elements.userInfo.classList.toggle("d-none", !isLoggedIn);
    elements.userInfo.classList.toggle("d-flex", isLoggedIn);

    if (!isLoggedIn) {
        elements.userEmail.textContent = "";
        renderTasks([]);
        return;
    }

    elements.userEmail.textContent = parseUserEmail(token);
    loadTasks();
}

async function apiFetch(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API}${path}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        logout();
        throw new Error("Sesiunea a expirat. Autentifica-te din nou.");
    }

    return response;
}

async function readError(response, fallback) {
    try {
        const error = await response.json();
        if (typeof error.detail === "string") {
            return error.detail;
        }
        if (error.detail) {
            return JSON.stringify(error.detail);
        }
    } catch {
        return fallback;
    }
    return fallback;
}

async function handleRegister(event) {
    event.preventDefault();
    setAlert(elements.registerError, "", false);
    setAlert(elements.registerSuccess, "", false);

    const email = document.getElementById("reg-email").value.trim();
    const parola = document.getElementById("reg-parola").value;

    if (!email || !email.includes("@")) {
        setAlert(elements.registerError, "Introdu un email valid.");
        return;
    }

    if (parola.length < 8) {
        setAlert(elements.registerError, "Parola trebuie sa aiba cel putin 8 caractere.");
        return;
    }

    try {
        const response = await apiFetch("/inregistrare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, parola }),
        });

        if (!response.ok) {
            setAlert(elements.registerError, await readError(response, "Eroare la inregistrare."));
            return;
        }

        elements.registerForm.reset();
        setAlert(elements.registerSuccess, "Cont creat. Te poti autentifica acum.");
        setTimeout(toggleAuthForm, 900);
    } catch (error) {
        setAlert(elements.registerError, `Nu se poate contacta serverul: ${error.message}`);
    }
}

async function handleLogin(event) {
    event.preventDefault();
    setAlert(elements.loginError, "", false);

    const email = document.getElementById("auth-email").value.trim();
    const parola = document.getElementById("auth-parola").value;

    if (!email || !parola) {
        setAlert(elements.loginError, "Email si parola sunt obligatorii.");
        return;
    }

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", parola);

    try {
        const response = await fetch(`${API}/autentificare`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            setAlert(elements.loginError, "Email sau parola incorecte.");
            return;
        }

        const data = await response.json();
        saveToken(data.access_token);
        elements.loginForm.reset();
        updateUI();
    } catch (error) {
        setAlert(elements.loginError, `Nu se poate contacta serverul: ${error.message}`);
    }
}

async function loadTasks() {
    elements.taskList.innerHTML = loadingMarkup();

    try {
        const response = await apiFetch("/sarcini");
        if (!response.ok) {
            elements.taskList.innerHTML = messageMarkup("Nu am putut incarca sarcinile.");
            return;
        }

        const tasks = await response.json();
        renderTasks(tasks);
    } catch (error) {
        elements.taskList.innerHTML = messageMarkup(`Nu se poate contacta serverul: ${escapeHtml(error.message)}`);
    }
}

function renderTasks(tasks) {
    updateStats(tasks);

    if (!tasks.length) {
        elements.taskList.innerHTML = `
            <div class="empty-state">
                <div>
                    <i class="bi bi-list-check"></i>
                    <p class="mb-0">Nu exista sarcini inca.</p>
                </div>
            </div>
        `;
        return;
    }

    elements.taskList.innerHTML = tasks.map(taskMarkup).join("");
}

function updateStats(tasks) {
    const completed = tasks.filter((task) => Boolean(task.finalizata)).length;

    elements.totalStat.textContent = tasks.length;
    elements.doneStat.textContent = completed;
    elements.activeStat.textContent = tasks.length - completed;
}

function taskMarkup(task) {
    const isDone = Boolean(task.finalizata);
    const statusClass = isDone ? "done" : "active";
    const statusIcon = isDone ? "bi-check-circle-fill" : "bi-clock";
    const statusText = isDone ? "Finalizata" : "In progres";

    return `
        <article class="task-item ${isDone ? "is-done" : ""}">
            <div>
                <div class="task-title-row">
                    <h3 class="task-title">${escapeHtml(task.titlu)}</h3>
                    <span class="status-pill ${statusClass}">
                        <i class="bi ${statusIcon}"></i>
                        ${statusText}
                    </span>
                </div>
                ${task.descriere ? `<p class="task-description">${escapeHtml(task.descriere)}</p>` : ""}
            </div>
            <div class="task-actions">
                <button class="btn btn-outline-success btn-sm btn-icon" data-complete-id="${task.id}" type="button" title="Finalizeaza" ${isDone ? "disabled" : ""}>
                    <i class="bi bi-check-lg"></i>
                </button>
                <button class="btn btn-outline-danger btn-sm btn-icon" data-delete-id="${task.id}" type="button" title="Sterge">
                    <i class="bi bi-trash3"></i>
                </button>
            </div>
        </article>
    `;
}

function loadingMarkup() {
    return `
        <div class="empty-state">
            <div>
                <div class="spinner-border text-primary mb-3" role="status"></div>
                <p class="mb-0">Se incarca sarcinile...</p>
            </div>
        </div>
    `;
}

function messageMarkup(message) {
    return `<div class="alert alert-warning mb-0">${message}</div>`;
}

async function handleTaskSubmit(event) {
    event.preventDefault();

    const titlu = elements.taskTitle.value.trim();
    const descriere = elements.taskDescription.value.trim();

    if (!titlu) {
        elements.taskTitle.focus();
        return;
    }

    try {
        const response = await apiFetch("/sarcini", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ titlu, descriere }),
        });

        if (!response.ok) {
            elements.taskList.innerHTML = messageMarkup(await readError(response, "Sarcina nu a putut fi adaugata."));
            return;
        }

        elements.taskForm.reset();
        loadTasks();
    } catch (error) {
        elements.taskList.innerHTML = messageMarkup(`Nu se poate contacta serverul: ${escapeHtml(error.message)}`);
    }
}

async function completeTask(taskId) {
    const response = await apiFetch(`/sarcini/${taskId}/finaliza`, { method: "PATCH" });
    if (response.ok) {
        loadTasks();
    }
}

async function deleteTask(taskId) {
    const response = await apiFetch(`/sarcini/${taskId}`, { method: "DELETE" });
    if (response.ok) {
        loadTasks();
    }
}

function handleTaskListClick(event) {
    const completeButton = event.target.closest("[data-complete-id]");
    const deleteButton = event.target.closest("[data-delete-id]");

    if (completeButton) {
        completeTask(completeButton.dataset.completeId);
    }

    if (deleteButton) {
        deleteTask(deleteButton.dataset.deleteId);
    }
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = String(text);
    return div.innerHTML;
}

function bindEvents() {
    elements.registerForm.addEventListener("submit", handleRegister);
    elements.loginForm.addEventListener("submit", handleLogin);
    elements.taskForm.addEventListener("submit", handleTaskSubmit);
    elements.taskList.addEventListener("click", handleTaskListClick);
    elements.reloadButton.addEventListener("click", loadTasks);
    elements.logoutButton.addEventListener("click", logout);

    document.querySelectorAll("[data-auth-toggle]").forEach((button) => {
        button.addEventListener("click", toggleAuthForm);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    updateUI();
});
