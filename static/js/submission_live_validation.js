const MAX_FILE_BYTES = 100 * 1024 * 1024;

const FIO_RE = /^(?:[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?\s){2}[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?$/u;
const INITIALS_RE = /\b[А-ЯЁ]\.\s*[А-ЯЁ]\.?\b/u;
const QUOTES_RE = /["'«»„“”]/u;

function normalizeSpaces(v) {
  return (v || "").replace(/\s+/g, " ").trim();
}

function countLetters(v) {
  const m = v.match(/[A-Za-zА-ЯЁа-яё]/gu);
  return m ? m.length : 0;
}

function upperLetterRatio(v) {
  const letters = v.match(/[A-Za-zА-ЯЁа-яё]/gu) || [];
  if (!letters.length) return 0;
  const upper = (v.match(/[A-ZА-ЯЁ]/gu) || []).length;
  return upper / letters.length;
}

function getCsrfToken(form) {
  const el = form.querySelector('input[name="csrfmiddlewaretoken"]');
  return el ? el.value : null;
}

function ensureErrorBox(field) {
  const id = `${field.id}__error`;
  let box = document.getElementById(id);

  if (!box) {
    box = document.createElement("div");
    box.id = id;
    box.className = "invalid-feedback";
    box.setAttribute("aria-live", "polite");
    field.insertAdjacentElement("afterend", box);
  }

  const describedBy = (field.getAttribute("aria-describedby") || "")
    .split(/\s+/)
    .filter(Boolean);

  if (!describedBy.includes(id)) {
    describedBy.push(id);
    field.setAttribute("aria-describedby", describedBy.join(" "));
  }

  if (!field.hasAttribute("aria-invalid")) {
    field.setAttribute("aria-invalid", "false");
  }

  return box;
}

function setFieldError(field, message) {
  const box = ensureErrorBox(field);
  field.classList.add("is-invalid");
  field.classList.remove("is-valid");
  field.setAttribute("aria-invalid", "true");
  field.setCustomValidity(message || "Ошибка");
  box.textContent = message || "Поле заполнено неверно.";
}

function clearFieldError(field) {
  const box = ensureErrorBox(field);
  field.classList.remove("is-invalid");
  field.classList.add("is-valid");
  field.setAttribute("aria-invalid", "false");
  field.setCustomValidity("");
  box.textContent = "";
}

function validateFio(field, label) {
  const value = normalizeSpaces(field.value);

  if (!value) return `Укажите ${label}.`;
  if (value.length > 120) return `${label} слишком длинное.`;
  if (INITIALS_RE.test(value)) return `${label}: нужны полные ФИО, инициалы запрещены.`;
  if (!/^[А-ЯЁа-яё\s-]+$/u.test(value)) return `${label}: допустимы только русские буквы, пробелы и дефис.`;
  if (!FIO_RE.test(value)) return `${label}: формат «Фамилия Имя Отчество».`;

  return null;
}

function validateTitle(field) {
  const value = normalizeSpaces(field.value);

  if (!value) return "Укажите название работы.";
  if (value.length < 5) return "Название слишком короткое.";
  if (value.length > 300) return "Название слишком длинное.";
  if (QUOTES_RE.test(value)) return "В названии нельзя использовать кавычки.";

  const letters = countLetters(value);
  const ratio = upperLetterRatio(value);
  if (letters >= 10 && ratio > 0.85) {
    return "Не используйте КАПС в названии.";
  }

  return null;
}

function validateYear(field) {
  const raw = normalizeSpaces(field.value);
  if (!raw) return "Укажите год.";

  const y = Number(raw);
  const now = new Date().getFullYear();

  if (!Number.isInteger(y)) return "Год должен быть целым числом.";
  if (y < 1950 || y > now + 1) return `Год должен быть в диапазоне 1950–${now + 1}.`;

  return null;
}

function validatePageCount(field) {
  const raw = normalizeSpaces(field.value);
  if (!raw) return "Укажите количество страниц.";

  const n = Number(raw);
  if (!Number.isInteger(n)) return "Количество страниц должно быть целым числом.";
  if (n < 1 || n > 2000) return "Количество страниц должно быть в диапазоне 1–2000.";

  return null;
}

function validateRequiredSelect(field, label) {
  if (!field.value) return `Выберите: ${label}.`;
  return null;
}

function validateFile(field) {
  const f = field.files && field.files[0];
  if (!f) return "Прикрепите PDF-файл.";

  const name = (f.name || "").toLowerCase();
  const byExt = name.endsWith(".pdf");
  const byMime = (f.type || "").toLowerCase() === "application/pdf";

  if (!byExt && !byMime) return "Файл должен быть в формате PDF.";
  if (f.size > MAX_FILE_BYTES) return "Файл слишком большой. Максимум 100 МБ.";

  return null;
}

function createSummary(form) {
  let box = document.getElementById("form__summary");
  if (!box) {
    box = document.createElement("div");
    box.id = "form__summary";
    box.className = "alert alert-danger d-none";
    box.setAttribute("role", "alert");
    box.setAttribute("aria-live", "assertive");
    form.prepend(box);
  }
  return box;
}

function showSummary(form, message) {
  const box = createSummary(form);
  box.textContent = message;
  box.classList.remove("d-none");
}

function hideSummary(form) {
  const box = createSummary(form);
  box.textContent = "";
  box.classList.add("d-none");
}

async function fetchJson(url) {
  const res = await fetch(url, {
    headers: { "Accept": "application/json" },
    credentials: "same-origin",
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

function resetSelect(select) {
  select.innerHTML = "";
  const opt = document.createElement("option");
  opt.value = "";
  opt.textContent = "---------";
  select.appendChild(opt);
}

async function loadDepartments(instituteSelect, departmentSelect) {
  resetSelect(departmentSelect);
  if (!instituteSelect.value) return;

  const data = await fetchJson(`/references/api/departments/?institute_id=${encodeURIComponent(instituteSelect.value)}`);
  for (const item of data.results || []) {
    const opt = document.createElement("option");
    opt.value = String(item.id);
    opt.textContent = item.name;
    departmentSelect.appendChild(opt);
  }
}

async function loadSpecialties(levelSelect, instituteSelect, specialtySelect) {
  resetSelect(specialtySelect);
  if (!levelSelect.value || !instituteSelect.value) return;

  const url = `/references/api/specialties/?education_level_id=${encodeURIComponent(levelSelect.value)}&institute_id=${encodeURIComponent(instituteSelect.value)}`;
  const data = await fetchJson(url);

  for (const item of data.results || []) {
    const opt = document.createElement("option");
    opt.value = String(item.id);
    opt.textContent = item.label;
    specialtySelect.appendChild(opt);
  }
}

function updateFilePreview(fileInput) {
  const nameEl = document.getElementById("selectedFileName");
  if (!nameEl) return;

  const f = fileInput.files && fileInput.files[0];
  nameEl.textContent = f ? `${f.name} (${Math.ceil(f.size / 1024)} КБ)` : "—";
}

function initSubmissionForm() {
  const form = document.getElementById("submissionForm");
  if (!form) return;

  form.noValidate = true;

  const author = document.getElementById("id_author_full_name");
  const supervisor = document.getElementById("id_supervisor_full_name");
  const title = document.getElementById("id_work_title");
  const year = document.getElementById("id_year");
  const pages = document.getElementById("id_page_count");
  const level = document.getElementById("id_education_level");
  const institute = document.getElementById("id_institute");
  const specialty = document.getElementById("id_specialty");
  const department = document.getElementById("id_department");
  const file = document.getElementById("id_file");
  const clearFileBtn = document.getElementById("clearFileBtn");
  const submitBtn = form.querySelector('button[type="submit"]');

  if (!author || !supervisor || !title || !year || !pages || !level || !institute || !specialty || !department || !file) {
    return;
  }

  const touched = new Set();
  const touch = (field) => touched.add(field.id);
  const isTouched = (field) => touched.has(field.id);

  const validators = new Map([
    [author, () => validateFio(author, "ФИО автора")],
    [supervisor, () => validateFio(supervisor, "ФИО руководителя")],
    [title, () => validateTitle(title)],
    [year, () => validateYear(year)],
    [pages, () => validatePageCount(pages)],
    [level, () => validateRequiredSelect(level, "уровень образования")],
    [institute, () => validateRequiredSelect(institute, "институт/школу")],
    [specialty, () => validateRequiredSelect(specialty, "направление/специальность")],
    [department, () => validateRequiredSelect(department, "кафедру/департамент")],
    [file, () => validateFile(file)],
  ]);

  function validateField(field, force = false) {
    const rule = validators.get(field);
    if (!rule) return true;
    if (!force && !isTouched(field)) return true;

    const message = rule();
    if (message) {
      setFieldError(field, message);
      return false;
    }
    clearFieldError(field);
    return true;
  }

  function validateAll(force = false) {
    hideSummary(form);
    let ok = true;
    for (const field of validators.keys()) {
      ok = validateField(field, force) && ok;
    }
    if (submitBtn) submitBtn.disabled = !form.checkValidity();
    return ok;
  }

  function focusFirstInvalid() {
    const first = form.querySelector(".is-invalid");
    if (first) first.focus();
  }

  for (const field of validators.keys()) {
    const evt = (field.tagName === "SELECT" || field.type === "file") ? "change" : "input";

    field.addEventListener(evt, () => {
      touch(field);
      validateField(field, true);
      validateAll(false);
    });

    field.addEventListener("blur", () => {
      touch(field);
      validateField(field, true);
      validateAll(false);
    });
  }

  level.addEventListener("change", async () => {
    resetSelect(specialty);
    try {
      if (level.value && institute.value) {
        await loadSpecialties(level, institute, specialty);
      }
    } catch {
      setFieldError(specialty, "Не удалось загрузить направления.");
    }
  });

  institute.addEventListener("change", async () => {
    resetSelect(department);
    resetSelect(specialty);

    try {
      if (institute.value) {
        await loadDepartments(institute, department);
      }
    } catch {
      setFieldError(department, "Не удалось загрузить кафедры.");
    }

    try {
      if (level.value && institute.value) {
        await loadSpecialties(level, institute, specialty);
      }
    } catch {
      setFieldError(specialty, "Не удалось загрузить направления.");
    }
  });

  file.addEventListener("change", () => {
    updateFilePreview(file);
  });

  if (clearFileBtn) {
    clearFileBtn.addEventListener("click", () => {
      file.value = "";
      updateFilePreview(file);
      touch(file);
      validateField(file, true);
    });
  }

  updateFilePreview(file);
  validateAll(false);

  async function submitAjax() {
    const fd = new FormData(form);
    const csrf = getCsrfToken(form);

    const res = await fetch(form.action || window.location.pathname, {
      method: "POST",
      body: fd,
      credentials: "same-origin",
      headers: {
        "Accept": "application/json",
        ...(csrf ? { "X-CSRFToken": csrf } : {}),
      },
    });

    const data = await res.json();

    if (res.ok && data.ok) {
      window.location.href = data.redirect_url || "/submissions/";
      return;
    }

    showSummary(form, "Форма содержит ошибки. Проверьте подсвеченные поля.");

    for (const [fieldName, errList] of Object.entries(data.errors || {})) {
      const input = document.getElementById(`id_${fieldName}`);
      if (!input) continue;
      touch(input);
      const msg = errList?.[0]?.message || "Ошибка в поле.";
      setFieldError(input, msg);
    }

    validateAll(false);
    focusFirstInvalid();
  }

  form.addEventListener("submit", async (e) => {
    const ok = validateAll(true);

    if (!ok || !form.checkValidity()) {
      e.preventDefault();
      showSummary(form, "Исправьте ошибки перед отправкой формы.");
      focusFirstInvalid();
      return;
    }

    if (form.dataset.ajaxSubmit === "1") {
      e.preventDefault();
      await submitAjax();
    }
  });
}

document.addEventListener("DOMContentLoaded", initSubmissionForm);