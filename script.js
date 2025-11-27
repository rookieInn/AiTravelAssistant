const promptInput = document.getElementById("promptInput");
const negativeInput = document.getElementById("negativeInput");
const customInput = document.getElementById("customInput");
const resultEl = document.getElementById("result");
const feedbackEl = document.getElementById("feedback");
const copyBtn = document.getElementById("copyBtn");
const resetBtn = document.getElementById("resetBtn");
const paramButtons = Array.from(document.querySelectorAll(".param-button"));
let feedbackTimer = null;

const placeholderText = "请先输入提示词并根据需要选择参数";

const collectActiveParams = () =>
  paramButtons
    .filter((btn) => btn.classList.contains("active"))
    .map((btn) => btn.dataset.param.trim());

const assembleCommand = () => {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    return "";
  }

  const segments = [`/imagine prompt: ${prompt}`];
  const params = collectActiveParams();
  const custom = customInput.value.trim();
  const negative = negativeInput.value.trim();

  if (params.length) {
    segments.push(params.join(" "));
  }

  if (custom) {
    segments.push(custom);
  }

  if (negative) {
    segments.push(`--no ${negative}`);
  }

  return segments.join(" ").replace(/\s+/g, " ").trim();
};

const renderResult = () => {
  const command = assembleCommand();
  resultEl.textContent = command || placeholderText;
  copyBtn.disabled = !command;
};

const toggleParamButton = (button) => {
  const alreadyActive = button.classList.contains("active");
  const group = button.dataset.group;
  const isMulti = button.dataset.multi === "true";

  if (!isMulti && group) {
    paramButtons
      .filter((btn) => btn.dataset.group === group && btn !== button)
      .forEach((btn) => btn.classList.remove("active"));
  }

  if (isMulti) {
    button.classList.toggle("active");
  } else {
    button.classList.toggle("active", !alreadyActive);
  }

  renderResult();
};

const showFeedback = (message, isError = false) => {
  clearTimeout(feedbackTimer);
  feedbackEl.textContent = message;
  feedbackEl.style.color = isError ? "#ef4444" : "#22c55e";
  feedbackTimer = setTimeout(() => {
    feedbackEl.textContent = "";
  }, 2400);
};

const handleCopy = async () => {
  const command = assembleCommand();
  if (!command) return;

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(command);
    } else {
      const area = document.createElement("textarea");
      area.value = command;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }

    showFeedback("已复制到剪贴板 ✨");
  } catch (error) {
    console.error(error);
    showFeedback("复制失败，请手动复制", true);
  }
};

const handleReset = () => {
  [promptInput, negativeInput, customInput].forEach((field) => {
    field.value = "";
  });
  paramButtons.forEach((btn) => btn.classList.remove("active"));
  renderResult();
  showFeedback("已重置", false);
};

const bindEvents = () => {
  document.addEventListener("click", (event) => {
    const button = event.target.closest(".param-button");
    if (!button) return;
    toggleParamButton(button);
  });

  [promptInput, negativeInput, customInput].forEach((field) => {
    field.addEventListener("input", renderResult);
  });

  copyBtn.addEventListener("click", handleCopy);
  resetBtn.addEventListener("click", handleReset);

  renderResult();
};

bindEvents();
