const MAX_FILE_BYTES = 100 * 1024 * 1024;

const FIO_RE = /^(?:[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?\s){2}[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?$/u;
const INITIALS_RE = /\b[А-ЯЁ]\.\s*[А-ЯЁ]\.?\b/u;

function normalizeSpaces(value) {
  return (value || "").replace(/\s+/g, " ").trim();
}

function extractLetters(value) {
  return Array.from(value).filter((char) => /\p{L}/u.test(char));
}

function countLetters(value) {
  return extractLetters(value).length;
}

function upperLetterRatio(value) {
  const letters = extractLetters(value);
  if (!letters.length) return 0;
  const upper = letters.filter((char) => char === char.toUpperCase() && char !== char.toLowerCase()).length;
  return upper / letters.length;
}

function hasBalancedQuotes(value) {
  if (((value.match(/"/g) || []).length % 2) !== 0) {
    return false;
  }

  let opened = 0;
  for (const char of value) {
    if (char === "«") {
      opened += 1;
    } else if (char === "»") {
      if (opened === 0) return false;
      opened -= 1;
    }
  }

  return opened === 0;
}

function getCsrfToken(form) {
  const element = form.querySelector('input[name="csrfmiddlewaretoken"]');
  return element ? element.value : null;
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
  box.textContent = message || "Поле заполнено некорректно.";
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
  if (value.length > 120) return `${label} указано слишком длинно.`;
  if (INITIALS_RE.test(value)) return `${label}: укажите полное ФИО без инициалов.`;
  if (!/^[А-ЯЁа-яё\s-]+$/u.test(value)) return `${label}: допустимы только русские буквы, пробелы и дефис.`;
  if (!FIO_RE.test(value)) return `${label}: используйте формат «Фамилия Имя Отчество».`;

  return null;
}

function validateTitle(field) {
  const value = normalizeSpaces(field.value);

  if (!value) return "Укажите название работы.";
  if (value.length < 5) return "Название работы указано слишком кратко.";
  if (value.length > 500) return "Название работы указано слишком длинно.";
  if (countLetters(value) < 3) return "Название работы должно содержать осмысленный текст.";
  if (/[.,;:!?]{3,}/u.test(value)) return "Не используйте более двух знаков препинания подряд в названии работы.";
  if (!hasBalancedQuotes(value)) return "Если в названии используются кавычки, они должны быть парными.";

  const letters = countLetters(value);
  const ratio = upperLetterRatio(value);
  if (letters > 0 && ratio === 1) {
    return "Не используйте написание названия полностью заглавными буквами (CAPS).";
  }

  return null;
}

function validateYear(field) {
  const raw = normalizeSpaces(field.value);
  if (!raw) return "Укажите год.";

  const year = Number(raw);
  const currentYear = new Date().getFullYear();

  if (!Number.isInteger(year)) return "Год должен быть целым числом.";
  if (year < 1900 || year > currentYear) {
    return `Год должен быть в диапазоне 1900–${currentYear}.`;
  }

  return null;
}

function validatePageCount(field) {
  const raw = normalizeSpaces(field.value);
  if (!raw) return "Укажите количество страниц.";

  const count = Number(raw);
  if (!Number.isInteger(count)) return "Количество страниц должно быть целым числом.";
  if (count < 1 || count > 5000) return "Количество страниц должно быть в диапазоне 1–5000.";

  return null;
}

function validateRequiredSelect(field, label) {
  if (!field.value) return `Выберите ${label}.`;
  return null;
}

function validateFile(field) {
  const file = field.files && field.files[0];
  if (!file) return "Прикрепите PDF-файл.";

  const name = (file.name || "").toLowerCase();
  const byExt = name.endsWith(".pdf");
  const byMime = (file.type || "").toLowerCase() === "application/pdf";

  if (!byExt && !byMime) return "Файл должен быть в формате PDF.";
  if (file.size > MAX_FILE_BYTES) return "Размер файла превышает допустимые 100 МБ.";

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
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function resetSelect(select) {
  select.innerHTML = "";
  const option = document.createElement("option");
  option.value = "";
  option.textContent = "---------";
  select.appendChild(option);
}

async function loadDepartments(instituteSelect, departmentSelect) {
  resetSelect(departmentSelect);
  if (!instituteSelect.value) return;

  const data = await fetchJson(`/references/api/departments/?institute_id=${encodeURIComponent(instituteSelect.value)}`);
  for (const item of data.results || []) {
    const option = document.createElement("option");
    option.value = String(item.id);
    option.textContent = item.name;
    departmentSelect.appendChild(option);
  }
}

async function loadSpecialties(levelSelect, instituteSelect, specialtySelect) {
  resetSelect(specialtySelect);
  if (!levelSelect.value || !instituteSelect.value) return;

  const url = `/references/api/specialties/?education_level_id=${encodeURIComponent(levelSelect.value)}&institute_id=${encodeURIComponent(instituteSelect.value)}`;
  const data = await fetchJson(url);

  for (const item of data.results || []) {
    const option = document.createElement("option");
    option.value = String(item.id);
    option.textContent = item.label;
    specialtySelect.appendChild(option);
  }
}

function updateFilePreview(fileInput) {
  const nameElement = document.getElementById("selectedFileName");
  if (!nameElement) return;

  const file = fileInput.files && fileInput.files[0];
  nameElement.textContent = file ? `${file.name} (${Math.ceil(file.size / 1024)} КБ)` : "—";
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
  const documentType = document.getElementById("id_document_type");
  const level = document.getElementById("id_education_level");
  const institute = document.getElementById("id_institute");
  const specialty = document.getElementById("id_specialty");
  const department = document.getElementById("id_department");
  const file = document.getElementById("id_file");
  const clearFileBtn = document.getElementById("clearFileBtn");
  const submitBtn = form.querySelector('button[type="submit"]');

  if (!author || !supervisor || !title || !year || !pages || !documentType || !level || !institute || !specialty || !department || !file) {
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
    [documentType, () => validateRequiredSelect(documentType, "тип документа")],
    [level, () => validateRequiredSelect(level, "уровень образования")],
    [institute, () => validateRequiredSelect(institute, "институт/школу")],
    [specialty, () => validateRequiredSelect(specialty, "направление подготовки")],
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
    if (submitBtn) {
      submitBtn.disabled = !form.checkValidity();
    }
    return ok;
  }

  function focusFirstInvalid() {
    const first = form.querySelector(".is-invalid");
    if (first) {
      first.scrollIntoView({ behavior: "smooth", block: "center" });
      first.focus();
    }
  }

  for (const field of validators.keys()) {
    const eventName = field.tagName === "SELECT" || field.type === "file" ? "change" : "input";

    field.addEventListener(eventName, () => {
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
      setFieldError(specialty, "Не удалось загрузить список направлений подготовки.");
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
      setFieldError(department, "Не удалось загрузить список кафедр.");
    }

    try {
      if (level.value && institute.value) {
        await loadSpecialties(level, institute, specialty);
      }
    } catch {
      setFieldError(specialty, "Не удалось загрузить список направлений подготовки.");
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
    const formData = new FormData(form);
    const csrfToken = getCsrfToken(form);

    const response = await fetch(form.action || window.location.pathname, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      },
    });

    const data = await response.json();

    if (response.ok && data.ok) {
      window.location.href = data.redirect_url || "/submissions/";
      return;
    }

    showSummary(form, "Форма содержит ошибки. Проверьте поля с подсветкой.");

    for (const [fieldName, errorList] of Object.entries(data.errors || {})) {
      const input = document.getElementById(`id_${fieldName}`);
      if (!input) continue;

      touch(input);
      const message = errorList?.[0]?.message || "Поле заполнено некорректно.";
      setFieldError(input, message);
    }

    validateAll(false);
    focusFirstInvalid();
  }

  form.addEventListener("submit", async (event) => {
    const isValid = validateAll(true);

    if (!isValid || !form.checkValidity()) {
      event.preventDefault();
      showSummary(form, "Исправьте ошибки перед отправкой формы.");
      focusFirstInvalid();
      return;
    }

    if (form.dataset.ajaxSubmit === "1") {
      event.preventDefault();
      await submitAjax();
    }
  });
}

document.addEventListener("DOMContentLoaded", initSubmissionForm);
