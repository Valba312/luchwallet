// ===============================
//  ОБЩАЯ НАСТРОЙКА + DOM-ССЫЛКИ
// ===============================

const API_BASE =
  location.hostname === "127.0.0.1" || location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://luchwallet-backend.onrender.com";

const loginBlock = document.getElementById("login-block");
const walletPage = document.getElementById("wallet-page");

const roleSelect = document.getElementById("role");
const loginInput = document.getElementById("login");
const passwordInput = document.getElementById("password");
const loginBtn = document.getElementById("login-btn");
const loginError = document.getElementById("login-error");

const empAvatarInitials = document.getElementById("emp-avatar-initials");
const empName = document.getElementById("emp-name");
const empPosition = document.getElementById("emp-position");
const empRate = document.getElementById("emp-rate");
const empExp = document.getElementById("emp-experience");
const empStatus = document.getElementById("emp-status");
const empSalary = document.getElementById("emp-salary");
const empHours = document.getElementById("emp-hours");
const empHoursDetail = document.getElementById("emp-hours-detail");
const empPenaltiesList = document.getElementById("emp-penalties-list");
const empAbsenceList = document.getElementById("emp-absence-list");
const empErrorText = document.getElementById("emp-error");
const topUserInfo = document.getElementById("top-user-info");
const pageTitle = document.getElementById("page-title");
const pageSubtitle = document.getElementById("page-subtitle");
const companyLogoRow = document.getElementById("company-logo-row");

const headerBalanceValue = document.getElementById("header-balance-value");
const mobileBalanceHeader = document.getElementById("mobile-balance-header");
const headerDesktop = document.querySelector(".header-desktop");
const cardSalary = document.getElementById("card-salary");
const empSalaryCard = document.getElementById("emp-salary-card");
const empHoursDuplicate = document.getElementById("emp-hours-duplicate");
const empHoursDetailDuplicate = document.getElementById("emp-hours-detail-duplicate");

const employeeLayout = document.getElementById("employee-layout");
const adminLayout = document.getElementById("admin-layout");

const logoutBtn = document.getElementById("logout-btn");
const adminLogoutBtn = document.getElementById("admin-logout-btn");
const logoutBtnBottom = document.getElementById("logout-btn-bottom");
const adminRefreshBtn = document.getElementById("admin-refresh-btn");

const adminTableBody = document.getElementById("admin-table-body");
const adminFormTitle = document.getElementById("admin-form-title");
const adminFormMode = document.getElementById("admin-form-mode");

const admLogin = document.getElementById("adm-login");
const admPassword = document.getElementById("adm-password");
const admInitials = document.getElementById("adm-initials");
const admName = document.getElementById("adm-name");
const admPosition = document.getElementById("adm-position");
const admRate = document.getElementById("adm-rate");
const admExperience = document.getElementById("adm-experience");
const admStatus = document.getElementById("adm-status");
const admSalary = document.getElementById("adm-salary");
const admHours = document.getElementById("adm-hours");
const admOvertime = document.getElementById("adm-overtime");
const admNightHours = document.getElementById("adm-night-hours");
const admHoursDetail = document.getElementById("adm-hours-detail");
const admFinesCount = document.getElementById("adm-fines-count");
const admAbsentCount = document.getElementById("adm-absent-count");
const admPenaltyComment = document.getElementById("adm-penalty-comment");
const admPenalties = document.getElementById("adm-penalties");
const admAbsences = document.getElementById("adm-absences");
const admErrorText = document.getElementById("adm-error-text");
const admPhotoFile = document.getElementById("adm-photo-file");
const admPhotoUploadBtn = document.getElementById("adm-photo-upload-btn");
const admPhotoUrl = document.getElementById("adm-photo-url");
const admPhotoClearBtn = document.getElementById("adm-photo-clear-btn");

const admWarehouse = document.getElementById("adm-warehouse");
const admShiftRole = document.getElementById("adm-shift-role");
const admShiftRate = document.getElementById("adm-shift-rate");
const admOnShift = document.getElementById("adm-on-shift");

const adminSaveBtn = document.getElementById("admin-save-btn");
const adminNewBtn = document.getElementById("admin-new-btn");
const adminDeleteBtn = document.getElementById("admin-delete-btn");
const adminExportBtn = document.getElementById("admin-export-excel-btn");

// История начислений
const paymentsTableBody = document.getElementById("payments-table-body");
const payType = document.getElementById("pay-type");
const payAmount = document.getElementById("pay-amount");
const payComment = document.getElementById("pay-comment");
const payAddBtn = document.getElementById("pay-add-btn");

// Модалка истории баланса
const balanceHistoryOverlay = document.getElementById("balance-history-overlay");
const balanceHistoryClose = document.getElementById("balance-history-close");
const balanceHistoryMonthLabel = document.getElementById("balance-history-month-label");
const balanceHistoryBody = document.getElementById("balance-history-body");

// График дохода / попап
const incomeChart = document.getElementById("income-chart");
const monthPopup = document.getElementById("month-popup");
const monthPopupTitle = document.getElementById("month-popup-title");
const monthPopupSalary = document.getElementById("month-popup-salary");
const monthPopupHours = document.getElementById("month-popup-hours");
const monthPopupPenalties = document.getElementById("month-popup-penalties");
const monthPopupAbsences = document.getElementById("month-popup-absences");
const incomeActiveLabel = document.getElementById("income-active-label");
const incomeMonthSelect = document.getElementById("income-month-select");
const incomeYearSelect = document.getElementById("income-year-select");
const incomeActiveDefault = incomeActiveLabel.textContent || "—";

// Анимация карточек справа
const infoCards = document.querySelectorAll(".info-card");
const mainEmployeeCard = document.getElementById("main-employee-card");

// coarse pointer check (мобилки)
const isCoarsePointer = window.matchMedia("(pointer: coarse)").matches;

let adminAuth = null;       // { login, password }
let adminCurrentId = null;  // id выбранного сотрудника (null = новый)
let currentEmployeeMonths = []; // массив месяцев с бэка
let employeeAuth = null;    // { login, password } для сотрудника
let currentEmployeeId = null;

function formatRub(num) {
  if (num == null) return "—";
  const n = Number(num) || 0;
  return n.toLocaleString("ru-RU") + " ₽";
}

function monthNameRu(index) {
  const arr = [
    "январь","февраль","март","апрель","май","июнь",
    "июль","август","сентябрь","октябрь","ноябрь","декабрь"
  ];
  return arr[index] || "";
}

function showLogin() {
  walletPage.style.display = "none";
  loginBlock.style.display = "block";
  loginError.style.display = "none";
}
function showApp() {
  loginBlock.style.display = "none";
  walletPage.style.display = "block";
}

function switchToEmployeeView() {
  employeeLayout.style.display = "grid";
  adminLayout.style.display = "none";
  pageTitle.textContent = "Кошелёк сотрудника";
  pageSubtitle.textContent = "Всё о зарплате, времени и дисциплине.";
  if (companyLogoRow) companyLogoRow.style.display = "flex";
}

function switchToAdminView() {
  if (employeeLayout) {
    employeeLayout.style.display = "none";
  }

  if (adminLayout) {
    adminLayout.style.display = "block";
    adminLayout.style.border = "none";
    adminLayout.style.minHeight = "auto";
    adminLayout.style.marginTop = "24px";
  }

  pageTitle.textContent = "Панель администратора";
  pageSubtitle.textContent = "Управление сотрудниками, начислениями и штрафами.";

  if (companyLogoRow) companyLogoRow.style.display = "none";

  if (headerDesktop) headerDesktop.style.display = "block";
  if (mobileBalanceHeader) mobileBalanceHeader.style.display = "none";

  showApp();
}

function doLogout() {
  localStorage.removeItem("lw_user");
  adminAuth = null;
  adminCurrentId = null;
  employeeAuth = null;
  currentEmployeeId = null;
  showLogin();
}

if (logoutBtn) logoutBtn.addEventListener("click", doLogout);
if (adminLogoutBtn) adminLogoutBtn.addEventListener("click", doLogout);
if (logoutBtnBottom) logoutBtnBottom.addEventListener("click", doLogout);

if (loginBtn) {
  loginBtn.addEventListener("click", (e) => {
    e.preventDefault();
    handleLogin();
  });
}

if (passwordInput) {
  passwordInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleLogin();
    }
  });
}

// автологин только для сотрудников
document.addEventListener("DOMContentLoaded", () => {
  const stored = localStorage.getItem("lw_user");
  if (!stored) return;
  try {
    const user = JSON.parse(stored);
    if (user.role === "employee") {
      if (user.password) {
        employeeAuth = { login: user.login, password: user.password };
      }
      applyEmployee(user.data, user.login);
    }
  } catch (e) {
    console.warn("Ошибка чтения сохранённого пользователя", e);
  }
});

// ===============================
//            LOGIN
// ===============================

async function handleLogin() {
  const role = roleSelect.value; // employee | admin
  const login = loginInput.value.trim().toLowerCase();
  const password = passwordInput.value;

  if (!login || !password) {
    showError("Введите логин и пароль");
    return;
  }

  loginBtn.disabled = true;
  const prevText = loginBtn.textContent;
  loginBtn.textContent = "Входим...";

  try {
    const resp = await fetch(`${API_BASE}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, login, password }),
    });

    if (!resp.ok) {
      if (resp.status === 401) {
        showError("Неверный логин или пароль");
      } else {
        showError("Ошибка авторизации");
      }
      return;
    }

    const json = await resp.json();

    if (json.role === "employee") {
      employeeAuth = { login, password };
      const stored = { ...json, password };
      localStorage.setItem("lw_user", JSON.stringify(stored));
      applyEmployee(json.data, json.login);
    } else if (json.role === "admin") {
      applyAdmin(json.login, password);
    }
    loginError.style.display = "none";
  } catch (e) {
    console.error("Ошибка логина:", e);
    showError("Не удалось связаться с сервером");
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = prevText;
  }
}

function showError(text) {
  loginError.textContent = text;
  loginError.style.display = "block";
}

// ===============================
//     WALLET / СОТРУДНИК
// ===============================

function renderIncomeChart() {
  if (!incomeChart) return;
  incomeChart.innerHTML = "";

  if (!currentEmployeeMonths || currentEmployeeMonths.length === 0) {
    incomeActiveLabel.textContent = "—";
    monthPopup.style.display = "none";
    return;
  }

  const selectedYear = parseInt(incomeYearSelect.value || "0", 10) || null;
  const selectedMonth = parseInt(incomeMonthSelect.value || "0", 10) || null;

  let startIndex = currentEmployeeMonths.findIndex(
    m => m.year === selectedYear && m.month === selectedMonth
  );

  if (startIndex === -1) {
    startIndex = Math.max(0, currentEmployeeMonths.length - 6);
  }

  const visible = currentEmployeeMonths.slice(startIndex, startIndex + 6);
  if (!visible.length) {
    incomeActiveLabel.textContent = "—";
    monthPopup.style.display = "none";
    return;
  }

  const maxIncome = Math.max(...visible.map(m => m.income || 0), 1);

  visible.forEach(m => {
    const bar = document.createElement("div");
    bar.className = "income-bar";
    const height = 30 + (m.income / maxIncome) * 60; // 30–90
    bar.style.height = `${height}%`;
    bar.dataset.label = m.short;
    bar.dataset.value = formatRub(m.income || 0);
    bar.dataset.monthKey = m.key;
    bar.dataset.year = m.year;
    bar.addEventListener(isCoarsePointer ? "click" : "mouseenter", () => {
      showMonthPopup(m, bar, true);
    });
    incomeChart.appendChild(bar);
  });

  const lastMonth = visible[visible.length - 1];
  incomeActiveLabel.textContent = lastMonth.fullName;
  const lastBar = incomeChart.lastElementChild;
  showMonthPopup(lastMonth, lastBar, false);
}

function setupIncomeSelectors() {
  if (!currentEmployeeMonths.length) return;

  const years = [...new Set(currentEmployeeMonths.map(m => m.year))].sort((a,b) => a-b);
  incomeYearSelect.innerHTML = "";
  years.forEach(y => {
    const opt = document.createElement("option");
    opt.value = String(y);
    opt.textContent = String(y);
    incomeYearSelect.appendChild(opt);
  });

  const startIndex = Math.max(0, currentEmployeeMonths.length - 6);
  const startMonthObj = currentEmployeeMonths[startIndex];

  incomeYearSelect.value = String(startMonthObj.year);

  function rebuildMonthOptions(preferredMonth) {
    const year = parseInt(incomeYearSelect.value || "0", 10);
    const monthsForYear = currentEmployeeMonths.filter(m => m.year === year);
    incomeMonthSelect.innerHTML = "";
    monthsForYear.forEach(m => {
      const opt = document.createElement("option");
      opt.value = String(m.month);
      opt.textContent = m.short;
      incomeMonthSelect.appendChild(opt);
    });
    let valueToSet = preferredMonth;
    if (
      valueToSet == null ||
      !monthsForYear.some(m => m.month === valueToSet)
    ) {
      valueToSet = monthsForYear.length ? monthsForYear[0].month : null;
    }
    if (valueToSet != null) incomeMonthSelect.value = String(valueToSet);
  }

  rebuildMonthOptions(startMonthObj.month);

  incomeYearSelect.onchange = () => {
    rebuildMonthOptions(null);
    renderIncomeChart();
  };
  incomeMonthSelect.onchange = renderIncomeChart;
}

function showMonthPopup(monthObj, barEl, animate) {
  if (!monthPopup || !monthObj) return;

  monthPopupTitle.textContent = `${monthObj.fullName} ${monthObj.year}`;
  monthPopupSalary.textContent =
    monthObj.salary != null ? formatRub(monthObj.salary) : "—";
  monthPopupHours.textContent =
    monthObj.hours != null ? `${monthObj.hours} ч` : "—";
  monthPopupPenalties.textContent =
    (monthObj.penalties || []).join("; ") || "—";
  monthPopupAbsences.textContent =
    (monthObj.absences || []).join("; ") || "—";

  monthPopup.style.display = "block";
}

function applyEmployee(user, login) {
  currentEmployeeId = user.id || user.employee_id || null;

  empAvatarInitials.textContent = user.initials || "••";
  empName.textContent = user.name || "";
  empPosition.textContent = user.position || "";
  empRate.textContent = user.rate || "";
  empExp.textContent = user.experience || "";
  empStatus.textContent = user.status || "";
  empSalary.textContent = user.salary || "";
  empHours.textContent = user.hours || "";
  empHoursDetail.textContent = user.hoursDetail || user.hours_detail || "";
  empErrorText.textContent = user.errorText || user.error_text || "";

  if (headerBalanceValue) {
    headerBalanceValue.textContent = user.salary || "—";
  }
  if (empSalaryCard) {
    empSalaryCard.textContent = user.salary || "—";
  }
  if (empHoursDuplicate) {
    empHoursDuplicate.textContent = user.hours || "—";
  }
  if (empHoursDetailDuplicate) {
    empHoursDetailDuplicate.textContent =
      user.hoursDetail || user.hours_detail || "—";
  }

  empPenaltiesList.innerHTML = "";
  (user.penalties || []).forEach(p => {
    const li = document.createElement("li");
    li.textContent = p;
    empPenaltiesList.appendChild(li);
  });

  empAbsenceList.innerHTML = "";
  (user.absences || []).forEach(a => {
    const li = document.createElement("li");
    li.textContent = a;
    empAbsenceList.appendChild(li);
  });

  topUserInfo.innerHTML = "";

  currentEmployeeMonths = Array.isArray(user.months) ? user.months.map(m => ({
    key: m.key,
    short: m.short,
    fullName: m.fullName,
    year: m.year,
    month: m.month,
    income: m.income,
    salary: m.salary,
    hours: m.hours,
    penalties: m.penalties || [],
    absences: m.absences || [],
  })) : [];

  setupIncomeSelectors();
  renderIncomeChart();
  switchToEmployeeView();
  showApp();
}

// ===============================
//   ИСТОРИЯ БАЛАНСА (модалка)
// ===============================

function openBalanceHistory() {
  if (!employeeAuth || !currentEmployeeId) return;
  balanceHistoryOverlay.style.display = "flex";

  const label = incomeActiveLabel.textContent || incomeActiveDefault || "месяц";
  balanceHistoryMonthLabel.textContent = label;

  balanceHistoryBody.innerHTML =
    `<tr><td colspan="4" class="balance-history-empty">Загрузка...</td></tr>`;

  fetch(`${API_BASE}/api/employee/payments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      login: employeeAuth.login,
      password: employeeAuth.password,
    }),
  })
    .then(async (resp) => {
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        console.error("Ошибка загрузки истории баланса", err);
        balanceHistoryBody.innerHTML =
          `<tr><td colspan="4" class="balance-history-empty">Ошибка загрузки</td></tr>`;
        return;
      }
      const list = await resp.json();
      if (!Array.isArray(list) || !list.length) {
        balanceHistoryBody.innerHTML =
          `<tr><td colspan="4" class="balance-history-empty">Операций пока нет</td></tr>`;
        return;
      }

      balanceHistoryBody.innerHTML = "";
      list.forEach((p) => {
        const tr = document.createElement("tr");
        const dt = new Date(p.created_at);
        const dateStr = dt.toLocaleString("ru-RU", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });

        const amountStr = formatRub(p.amount);
        tr.innerHTML = `
          <td>${dateStr}</td>
          <td>${p.type}</td>
          <td style="text-align:right;">${amountStr}</td>
          <td>${p.comment || ""}</td>
        `;
        balanceHistoryBody.appendChild(tr);
      });
    })
    .catch((e) => {
      console.error(e);
      balanceHistoryBody.innerHTML =
        `<tr><td colspan="4" class="balance-history-empty">Ошибка связи с сервером</td></tr>`;
    });
}

function closeBalanceHistory() {
  balanceHistoryOverlay.style.display = "none";
}

if (mobileBalanceHeader) {
  mobileBalanceHeader.addEventListener("click", openBalanceHistory);
}
if (cardSalary) {
  cardSalary.addEventListener("click", openBalanceHistory);
}
if (balanceHistoryClose) {
  balanceHistoryClose.addEventListener("click", closeBalanceHistory);
}
if (balanceHistoryOverlay) {
  balanceHistoryOverlay.addEventListener("click", (e) => {
    if (e.target === balanceHistoryOverlay) closeBalanceHistory();
  });
}

// ===============================
//       ADMIN / АДМИНКА
// ===============================

function applyAdmin(login, password) {
  adminAuth = { login, password };
  topUserInfo.innerHTML = `Вы вошли как администратор <strong>${login}</strong>`;
  adminCurrentId = null;
  clearAdminForm();
  clearPaymentsUI("Выберите сотрудника");
  adminFormTitle.textContent = "Новый сотрудник";
  adminFormMode.textContent = "создание";
  switchToAdminView();
  showApp();
  loadEmployees();
}

// служебные конвертеры
function listToTextarea(list) {
  return (list || []).join("\n");
}

function textareaToList(value) {
  return value.split("\n").map(s => s.trim()).filter(Boolean);
}

function extractNumber(str) {
  if (!str) return "";
  const digits = String(str).replace(/\D/g, "");
  return digits;
}

function digitsOnlyInput(e) {
  const digits = e.target.value.replace(/\D/g, "");
  e.target.value = digits;
}

admRate.addEventListener("input", digitsOnlyInput);
admSalary.addEventListener("input", digitsOnlyInput);
admHours.addEventListener("input", digitsOnlyInput);

function updateHoursDetail() {
  if (!admHoursDetail) return;
  const overtime = parseInt(admOvertime.value || "0", 10) || 0;
  const night = parseInt(admNightHours.value || "0", 10) || 0;
  admHoursDetail.value = `Переработка: ${overtime} ч · Ночные: ${night} ч.`;
}

if (admOvertime && admNightHours) {
  admOvertime.addEventListener("input", updateHoursDetail);
  admNightHours.addEventListener("input", updateHoursDetail);
}

if (admPhotoClearBtn && admPhotoUrl) {
  admPhotoClearBtn.addEventListener("click", () => {
    admPhotoUrl.value = "";
  });
}

if (admPhotoUploadBtn && admPhotoFile) {
  admPhotoUploadBtn.addEventListener("click", async () => {
    if (!adminAuth || adminCurrentId == null) {
      alert("Сначала выберите сотрудника и войдите как админ");
      return;
    }
    if (!admPhotoFile.files.length) {
      alert("Выберите файл для загрузки");
      return;
    }
    const formData = new FormData();
    formData.append("file", admPhotoFile.files[0]);

    try {
      const resp = await fetch(`${API_BASE}/api/employees/${adminCurrentId}/photo`, {
        method: "POST",
        headers: {
          "X-Admin-Login": adminAuth.login,
          "X-Admin-Password": adminAuth.password,
        },
        body: formData,
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        alert("Ошибка загрузки фото: " + (err.detail || resp.status));
        return;
      }

      const json = await resp.json();
      if (json.photo_url && admPhotoUrl) {
        admPhotoUrl.value = json.photo_url;
      }
      alert("Фото обновлено");
    } catch (e) {
      console.error(e);
      alert("Ошибка связи с сервером при загрузке фото");
    }
  });
}

function clearAdminForm() {
  admLogin.value = "";
  admPassword.value = "";
  admInitials.value = "";
  admName.value = "";
  admPosition.value = "";
  admRate.value = "";
  admExperience.value = "";
  admStatus.value = "Активен · Основное место";
  admSalary.value = "";
  admHours.value = "";
  admOvertime.value = "0";
  admNightHours.value = "0";
  updateHoursDetail();
  admFinesCount.value = "0";
  admAbsentCount.value = "0";
  admPenaltyComment.value = "";
  admPenalties.value = "";
  admAbsences.value = "";
  admErrorText.value = "";
  if (admPhotoUrl) admPhotoUrl.value = "";
  if (admPhotoFile) admPhotoFile.value = "";
  if (admWarehouse) admWarehouse.value = "Челябинск · Склад №1";
  if (admShiftRole) admShiftRole.value = "";
  if (admShiftRate) admShiftRate.value = "";
  if (admOnShift) admOnShift.checked = false;
}

function clearPaymentsUI(message) {
  paymentsTableBody.innerHTML =
    `<tr><td colspan="5" class="admin-table-empty">${message || "Нет операций"}</td></tr>`;
}

adminNewBtn.addEventListener("click", () => {
  adminCurrentId = null;
  clearAdminForm();
  clearPaymentsUI("Выберите сотрудника");
  adminFormTitle.textContent = "Новый сотрудник";
  adminFormMode.textContent = "создание";
});

adminRefreshBtn.addEventListener("click", () => {
  loadEmployees();
});

function parseHoursDetail(str) {
  const res = { overtime: 0, night: 0 };
  if (!str) return res;
  const o = str.match(/Переработка:\s*(\d+)/);
  const n = str.match(/Ночные:\s*(\d+)/);
  if (o) res.overtime = parseInt(o[1], 10) || 0;
  if (n) res.night = parseInt(n[1], 10) || 0;
  return res;
}

function parsePenalties(list) {
  const res = { fines: 0, absents: 0, comment: "" };
  if (!Array.isArray(list)) return res;

  list.forEach(p => {
    if (p.startsWith("Штрафов")) {
      const m = p.match(/Штрафов:\s*(\d+)/);
      if (m) res.fines = parseInt(m[1], 10) || 0;
    } else if (p.startsWith("Прогулы")) {
      const m = p.match(/Прогулы:\s*(\d+)/);
      if (m) res.absents = parseInt(m[1], 10) || 0;
    } else if (p.startsWith("Замечания")) {
      res.comment = p.replace(/^Замечания:\s*/, "");
    }
  });

  return res;
}

// Сохранение сотрудника
adminSaveBtn.addEventListener("click", async () => {
  if (!adminAuth) return;

  updateHoursDetail();

  const rateNum = admRate.value.trim();
  const salaryNum = admSalary.value.trim();
  const hoursNum = admHours.value.trim();
  const shiftRateNum = admShiftRate.value.trim();

  const fines = parseInt(admFinesCount.value || "0", 10) || 0;
  const absents = parseInt(admAbsentCount.value || "0", 10) || 0;
  const penComment = (admPenaltyComment.value || "").trim();

  const penaltiesArr = [];
  penaltiesArr.push(`Штрафов: ${fines || 0}`);
  penaltiesArr.push(`Прогулы: ${absents || 0}`);
  if (penComment) penaltiesArr.push(`Замечания: ${penComment}`);

  const payloadBase = {
    login: admLogin.value.trim().toLowerCase(),
    initials: admInitials.value.trim(),
    name: admName.value.trim(),
    position: admPosition.value.trim(),
    rate: rateNum,
    experience: admExperience.value.trim(),
    status: admStatus.value.trim(),
    salary: salaryNum,
    hours: hoursNum,
    hours_detail: admHoursDetail.value.trim(),
    penalties: penaltiesArr,
    absences: textareaToList(admAbsences.value),
    error_text: admErrorText.value.trim(),
    photo_url: admPhotoUrl.value.trim(),
    warehouse: admWarehouse ? admWarehouse.value.trim() : "",
    shift_role: admShiftRole ? admShiftRole.value : "",
    on_shift: admOnShift ? admOnShift.checked : false,
    shift_rate: shiftRateNum ? parseInt(shiftRateNum, 10) : null,
  };

  const password = admPassword.value.trim();
  if (password) {
    payloadBase.password = password;
  }

  try {
    let url = `${API_BASE}/api/employees`;
    let method = "POST";
    if (adminCurrentId != null) {
      url = `${API_BASE}/api/employees/${adminCurrentId}`;
      method = "PUT";
    } else {
      if (!payloadBase.login || !password) {
        alert("Для нового сотрудника обязательно укажите логин и пароль");
        return;
      }
    }

    const resp = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Login": adminAuth.login,
        "X-Admin-Password": adminAuth.password,
      },
      body: JSON.stringify(payloadBase),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      alert("Ошибка сохранения: " + (err.detail || resp.status));
      return;
    }

    const emp = await resp.json();
    adminCurrentId = emp.id;
    alert("Сотрудник сохранён");
    await loadEmployees();
  } catch (e) {
    console.error(e);
    alert("Ошибка связи с сервером при сохранении");
  }
});

// Экспорт в Excel
adminExportBtn.addEventListener("click", async () => {
  if (!adminAuth || adminCurrentId == null) {
    alert("Выберите сотрудника для экспорта");
    return;
  }

  try {
    const url = `${API_BASE}/api/employees/${adminCurrentId}/export`;

    const resp = await fetch(url, {
      method: "GET",
      headers: {
        "X-Admin-Login": adminAuth.login,
        "X-Admin-Password": adminAuth.password,
      },
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      alert("Ошибка экспорта: " + (err.detail || resp.status));
      return;
    }

    const blob = await resp.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = `employee_${adminCurrentId}_card.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(downloadUrl);
  } catch (e) {
    console.error(e);
    alert("Ошибка связи с сервером при экспорте");
  }
});

adminDeleteBtn.addEventListener("click", async () => {
  if (!adminAuth || adminCurrentId == null) {
    alert("Выберите сотрудника для удаления");
    return;
  }
  if (!confirm("Точно удалить этого сотрудника?")) return;

  try {
    const resp = await fetch(`${API_BASE}/api/employees/${adminCurrentId}`, {
      method: "DELETE",
      headers: {
        "X-Admin-Login": adminAuth.login,
        "X-Admin-Password": adminAuth.password,
      },
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      alert("Ошибка удаления: " + (err.detail || resp.status));
      return;
    }

    adminCurrentId = null;
    clearAdminForm();
    clearPaymentsUI("Выберите сотрудника");
    adminFormTitle.textContent = "Новый сотрудник";
    adminFormMode.textContent = "создание";
    loadEmployees();
  } catch (e) {
    console.error(e);
    alert("Ошибка связи с сервером при удалении");
  }
});

async function loadEmployees() {
  if (!adminAuth) return;
  adminTableBody.innerHTML =
    '<tr><td colspan="6" class="admin-table-empty">Загрузка...</td></tr>';

  try {
    const resp = await fetch(`${API_BASE}/api/employees`, {
      headers: {
        "X-Admin-Login": adminAuth.login,
        "X-Admin-Password": adminAuth.password,
      },
    });

    if (!resp.ok) {
      adminTableBody.innerHTML =
        '<tr><td colspan="6" class="admin-table-empty">Ошибка загрузки списка</td></tr>';
      return;
    }

    const list = await resp.json();
    if (!Array.isArray(list) || list.length === 0) {
      adminTableBody.innerHTML =
        '<tr><td colspan="6" class="admin-table-empty">Пока нет сотрудников</td></tr>';
      return;
    }

    adminTableBody.innerHTML = "";
    list.forEach(emp => {
      const tr = document.createElement("tr");
      tr.dataset.id = emp.id;

      const roleLabel =
        emp.shift_role === "receiver"
          ? "Приёмщик"
          : emp.shift_role === "loader"
          ? "Кладовщик"
          : (emp.shift_role || "—");

      const onShiftChecked = emp.on_shift ? "checked" : "";

      tr.innerHTML = `
        <td>${emp.id}</td>
        <td>${emp.login}</td>
        <td>${emp.name}</td>
        <td>${emp.position}</td>
        <td>${roleLabel}</td>
        <td class="admin-table-center">
          <input type="checkbox" class="on-shift-checkbox" ${onShiftChecked} />
        </td>
      `;

      const checkbox = tr.querySelector(".on-shift-checkbox");

      if (checkbox) {
        checkbox.addEventListener("click", (e) => e.stopPropagation());

        checkbox.addEventListener("change", async (e) => {
          const checked = e.target.checked;
          try {
            const resp = await fetch(`${API_BASE}/api/employees/${emp.id}`, {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
                "X-Admin-Login": adminAuth.login,
                "X-Admin-Password": adminAuth.password,
              },
              body: JSON.stringify({ on_shift: checked }),
            });

            if (!resp.ok) {
              const err = await resp.json().catch(() => ({}));
              alert("Не удалось обновить смену: " + (err.detail || resp.status));
              e.target.checked = !checked;
            }
          } catch (err) {
            console.error(err);
            alert("Ошибка связи с сервером");
            e.target.checked = !checked;
          }
        });
      }

      tr.addEventListener("click", () => {
        adminCurrentId = emp.id;
        loadEmployeeDetails(emp.id);
      });
      adminTableBody.appendChild(tr);
    });
  } catch (e) {
    console.error(e);
    adminTableBody.innerHTML =
      '<tr><td colspan="6" class="admin-table-empty">Ошибка связи с сервером</td></tr>';
  }
}

async function loadEmployeeDetails(id) {
  if (!adminAuth) return;

  try {
    const resp = await fetch(`${API_BASE}/api/employees/${id}`, {
      headers: {
        "X-Admin-Login": adminAuth.login,
        "X-Admin-Password": adminAuth.password,
      },
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      alert("Ошибка загрузки сотрудника: " + (err.detail || resp.status));
      return;
    }

    const emp = await resp.json();
    fillAdminForm(emp);
    adminFormTitle.textContent = "Редактирование сотрудника";
    adminFormMode.textContent = "#" + emp.id;
    loadPaymentsForEmployee(emp.id);
  } catch (e) {
    console.error(e);
    alert("Ошибка связи с сервером при загрузке сотрудника");
  }
}

function fillAdminForm(emp) {
  admLogin.value = emp.login || "";
  admInitials.value = emp.initials || "";
  admName.value = emp.name || "";
  admPosition.value = emp.position || "";
  admRate.value = extractNumber(emp.rate || "");
  admExperience.value = emp.experience || "";
  admStatus.value = emp.status || "Активен · Основное место";
  admSalary.value = extractNumber(emp.salary || "");
  admHours.value = extractNumber(emp.hours || "");

  if (admWarehouse) {
    admWarehouse.value = emp.warehouse || "Челябинск · Склад №1";
  }
  if (admShiftRole) {
    admShiftRole.value = emp.shift_role || "";
  }
  if (admShiftRate) {
    admShiftRate.value =
      typeof emp.shift_rate === "number" ? String(emp.shift_rate) : "";
  }
  if (admOnShift) {
    admOnShift.checked = !!emp.on_shift;
  }

  const parsedHours = parseHoursDetail(emp.hours_detail || emp.hoursDetail || "");
  admOvertime.value = String(parsedHours.overtime || 0);
  admNightHours.value = String(parsedHours.night || 0);
  updateHoursDetail();

  const parsedPen = parsePenalties(emp.penalties || []);
  admFinesCount.value = String(parsedPen.fines || 0);
  admAbsentCount.value = String(parsedPen.absents || 0);
  admPenaltyComment.value = parsedPen.comment || "";
  admPenalties.value = (emp.penalties || []).join("\n");
  admAbsences.value = listToTextarea(emp.absences || []);
  admErrorText.value = emp.error_text || emp.errorText || "";
  admPhotoUrl.value = emp.photo_url || "";
  admPassword.value = "";
}

// Платежи / история начислений в админке

async function loadPaymentsForEmployee(empId) {
  if (!adminAuth || empId == null) return;
  paymentsTableBody.innerHTML =
    '<tr><td colspan="5" class="admin-table-empty">Загрузка...</td></tr>';

  try {
    const resp = await fetch(`${API_BASE}/api/employees/${empId}/payments`, {
      headers: {
        "X-Admin-Login": adminAuth.login,
        "X-Admin-Password": adminAuth.password,
      },
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      paymentsTableBody.innerHTML =
        `<tr><td colspan="5" class="admin-table-empty">Ошибка: ${(err.detail || resp.status)}</td></tr>`;
      return;
    }

    const list = await resp.json();
    if (!Array.isArray(list) || !list.length) {
      paymentsTableBody.innerHTML =
        '<tr><td colspan="5" class="admin-table-empty">Операций пока нет</td></tr>';
      return;
    }

    paymentsTableBody.innerHTML = "";
    list.forEach(p => {
      const tr = document.createElement("tr");
      const dt = new Date(p.created_at);
      const dateStr = dt.toLocaleString("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });

      const amountStr = formatRub(p.amount);
      tr.innerHTML = `
        <td>${dateStr}</td>
        <td>${p.type}</td>
        <td style="text-align:right;">${amountStr}</td>
        <td>${p.comment || ""}</td>
        <td><button class="btn-small btn-red" data-id="${p.id}">×</button></td>
      `;

      const btn = tr.querySelector("button");
      btn.addEventListener("click", () => {
        deletePayment(empId, p.id);
      });

      paymentsTableBody.appendChild(tr);
    });
  } catch (e) {
    console.error(e);
    paymentsTableBody.innerHTML =
      '<tr><td colspan="5" class="admin-table-empty">Ошибка связи с сервером</td></tr>';
  }
}

async function deletePayment(empId, paymentId) {
  if (!adminAuth) return;
  if (!confirm("Удалить эту операцию?")) return;

  try {
    const resp = await fetch(`${API_BASE}/api/employees/${empId}/payments/${paymentId}`, {
      method: "DELETE",
      headers: {
        "X-Admin-Login": adminAuth.login,
        "X-Admin-Password": adminAuth.password,
      },
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      alert("Ошибка удаления операции: " + (err.detail || resp.status));
      return;
    }

    await loadPaymentsForEmployee(empId);
    await loadEmployeeDetails(empId);
  } catch (e) {
    console.error(e);
    alert("Ошибка связи с сервером при удалении операции");
  }
}

payAddBtn.addEventListener("click", async () => {
  if (!adminAuth || adminCurrentId == null) {
    alert("Выберите сотрудника");
    return;
  }

  const type = payType.value;
  const amount = parseInt(payAmount.value || "0", 10);
  const comment = (payComment.value || "").trim();

  if (!amount) {
    alert("Укажите сумму операции");
    return;
  }

  try {
    const resp = await fetch(`${API_BASE}/api/employees/${adminCurrentId}/payments`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Login": adminAuth.login,
        "X-Admin-Password": adminAuth.password,
      },
      body: JSON.stringify({ type, amount, comment }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      alert("Ошибка добавления операции: " + (err.detail || resp.status));
      return;
    }

    payAmount.value = "";
    payComment.value = "";
    await loadPaymentsForEmployee(adminCurrentId);
    await loadEmployeeDetails(adminCurrentId);
  } catch (e) {
    console.error(e);
    alert("Ошибка связи с сервером при добавлении операции");
  }
});

// простая анимация карточек справа
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("card-visible");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.2 }
);

infoCards.forEach((card) => observer.observe(card));
if (mainEmployeeCard) observer.observe(mainEmployeeCard);
