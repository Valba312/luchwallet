const API_BASE = ""; // тот же домен/порт, что и backend

let employeeAuth = null; // { login, password }

/* ===== утилиты ===== */

function splitLines(value) {
  if (!value) return [];
  return value
    .split(/\r?\n/)
    .map(v => v.trim())
    .filter(Boolean);
}

/* ===== DOM ===== */

const loginCard = document.getElementById("login-card");
const loginInput = document.getElementById("login-input");
const passwordInput = document.getElementById("password-input");
const loginBtn = document.getElementById("login-btn");
const loginError = document.getElementById("login-error");

const employeeCard = document.getElementById("employee-card");
const cardFullName = document.getElementById("card-fullname");
const cardPosition = document.getElementById("card-position");
const cardDepartment = document.getElementById("card-department");
const cardWarehouse = document.getElementById("card-warehouse");
const cardShiftRole = document.getElementById("card-shift-role");
const cardRate = document.getElementById("card-rate");
const cardExperience = document.getElementById("card-experience");
const cardSchedule = document.getElementById("card-schedule");
const cardCurrentStatus = document.getElementById("card-current-status");
const cardLastStatusChange = document.getElementById("card-last-status-change");
const cardStatusInput = document.getElementById("card-status-input");

const cardResponsibilitiesInput = document.getElementById("card-responsibilities-input");
const cardSkillsInput = document.getElementById("card-skills-input");
const cardRolesInput = document.getElementById("card-roles-input");
const cardHistoryList = document.getElementById("card-history-list");

const cardModeTag = document.getElementById("card-mode-tag");
const cardEditBtn = document.getElementById("card-edit-btn");
const cardSaveBtn = document.getElementById("card-save-btn");
const cardCancelBtn = document.getElementById("card-cancel-btn");

/* ===== режим карточки ===== */

function setEmployeeCardMode(mode) {
  const isEdit = mode === "edit";

  if (cardModeTag) cardModeTag.textContent = isEdit ? "Редактирование" : "Просмотр";

  [cardStatusInput, cardResponsibilitiesInput, cardSkillsInput, cardRolesInput].forEach(el => {
    if (!el) return;
    el.disabled = !isEdit;
  });

  if (cardEditBtn) cardEditBtn.style.display = isEdit ? "none" : "inline-flex";
  if (cardSaveBtn) cardSaveBtn.style.display = isEdit ? "inline-flex" : "none";
  if (cardCancelBtn) cardCancelBtn.style.display = isEdit ? "inline-flex" : "none";
}

/* ===== рендер истории ===== */

function renderEmployeeCardHistory(history) {
  if (!cardHistoryList) return;

  cardHistoryList.innerHTML = "";

  if (!history || history.length === 0) {
    const li = document.createElement("li");
    li.className = "history-empty";
    li.textContent = "Изменения пока не зафиксированы";
    cardHistoryList.appendChild(li);
    return;
  }

  history
    .slice()
    .reverse()
    .forEach(item => {
      const li = document.createElement("li");
      const ts = item.timestamp || "";
      const field = item.field || "";
      const oldVal = item.old ?? "—";
      const newVal = item.new ?? "—";

      li.innerHTML =
        `<div><strong>${ts}</strong></div>` +
        `<div>Поле: <strong>${field}</strong></div>` +
        `<div>Было: ${oldVal}</div>` +
        `<div>Стало: ${newVal}</div>`;

      cardHistoryList.appendChild(li);
    });
}

/* ===== рендер карточки ===== */

function applyEmployeeCard(card) {
  if (!card) return;

  if (cardFullName) cardFullName.textContent = card.full_name || card.name || "";
  if (cardPosition) cardPosition.textContent = card.position || "";
  if (cardDepartment) cardDepartment.textContent = card.department || "—";
  if (cardWarehouse) cardWarehouse.textContent = card.warehouse || "—";
  if (cardShiftRole) cardShiftRole.textContent = card.shift_role || "—";
  if (cardRate) cardRate.textContent = card.rate || "—";
  if (cardExperience) cardExperience.textContent = card.experience || "—";

  if (cardSchedule && !card.schedule) {
    cardSchedule.textContent = "По данным системы";
  }
  if (cardCurrentStatus) cardCurrentStatus.textContent = card.status || "—";
  if (cardStatusInput) cardStatusInput.value = card.status || "";

  if (cardLastStatusChange) {
    const lastHistory = (card.history || []).slice(-1)[0];
    cardLastStatusChange.textContent = lastHistory?.timestamp || "—";
  }

  if (cardResponsibilitiesInput) {
    cardResponsibilitiesInput.value = (card.responsibilities || []).join("\n");
  }
  if (cardSkillsInput) {
    cardSkillsInput.value = (card.skills || []).join("\n");
  }
  if (cardRolesInput) {
    cardRolesInput.value = (card.roles || []).join("\n");
  }

  renderEmployeeCardHistory(card.history || []);
  setEmployeeCardMode("view");
}

/* ===== API ===== */

async function loginEmployee() {
  loginError.textContent = "";

  const login = (loginInput.value || "").trim();
  const password = passwordInput.value || "";

  if (!login || !password) {
    loginError.textContent = "Введите логин и пароль.";
    return;
  }

try{
    const resp = await fetch(`${API_BASE}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: "employee",
        login,
        password,
      }),
    });

    if (!resp.ok) {
      loginError.textContent = "Неверный логин или пароль.";
      return;
    }

    const data = await resp.json();

    employeeAuth = { login, password };

    // прячем форму логина, показываем карточку
    loginCard.style.display = "none";
    employeeCard.style.display = "block";

    await loadEmployeeCardSelf();
  } catch (e) {
    console.error(e);
    loginError.textContent = "Ошибка связи с сервером.";
  }
}

async function loadEmployeeCardSelf() {
  if (!employeeAuth) return;

  try {
    const resp = await fetch(`${API_BASE}/api/employee/card`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(employeeAuth),
    });

    if (!resp.ok) {
      console.error("card load error", await resp.text());
      return;
    }

    const card = await resp.json();
    applyEmployeeCard(card);
  } catch (e) {
    console.error("Ошибка загрузки карточки:", e);
  }
}

async function saveEmployeeCard() {
  if (!employeeAuth) return;

  const responsibilities = splitLines(cardResponsibilitiesInput?.value || "");
  const skills = splitLines(cardSkillsInput?.value || "");
  const roles = splitLines(cardRolesInput?.value || "");
  const status = (cardStatusInput?.value || "").trim() || null;

  cardSaveBtn.disabled = true;

  try {
    const resp = await fetch(`${API_BASE}/api/employee/card/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...employeeAuth,
        responsibilities,
        skills,
        roles,
        status,
      }),
    });

    if (!resp.ok) {
      alert("Не удалось сохранить карточку.");
      return;
    }

    const card = await resp.json();
    applyEmployeeCard(card);
  } catch (e) {
    console.error("Ошибка сохранения карточки:", e);
    alert("Ошибка сохранения карточки.");
  } finally {
    cardSaveBtn.disabled = false;
  }
}

/* ===== события ===== */

loginBtn.addEventListener("click", loginEmployee);
passwordInput.addEventListener("keydown", e => {
  if (e.key === "Enter") loginEmployee();
});

cardEditBtn.addEventListener("click", () => setEmployeeCardMode("edit"));
cardCancelBtn.addEventListener("click", () => {
  setEmployeeCardMode("view");
  loadEmployeeCardSelf();
});
cardSaveBtn.addEventListener("click", saveEmployeeCard);
