const apiPrefix = "/api/v1";

const VIEW_META = {
  home: { kicker: "首页", title: "审计总览" },
  projects: { kicker: "审计项目", title: "项目列表与当前项目详情" },
  "task-management": { kicker: "审计项目任务管理", title: "子代理进度与协作日志" },
  reports: { kicker: "报告生成", title: "最终报告预览与导出" },
  knowledge: { kicker: "知识库", title: "历史审计结论沉淀" },
  settings: { kicker: "系统设置", title: "API Key、系统状态与工具能力" },
};

const ROLE_LABELS = {
  manager: "Manager",
  triage: "初步研判",
  "static-analysis": "Static Analysis",
  "dynamic-analysis": "Dynamic Analysis",
  "exploitability-review": "Exploitability Review",
  "exploit-strategy": "利用思路",
};

const ROLE_TOOL_TOTALS = {
  triage: 5,
  "static-analysis": 4,
  "dynamic-analysis": 4,
  "exploitability-review": 4,
  "exploit-strategy": 4,
};

const STATUS_LABELS = {
  idle: "空闲",
  queued: "待审计",
  running: "审计中",
  completed: "已完成",
  failed: "失败",
  unavailable: "不可用",
  timeout: "超时",
  skipped: "已跳过",
};

const EVENT_KIND_LABELS = {
  tool_invocation: "工具调用",
  tool_result: "工具结果",
  llm_usage_recorded: "Token 计量",
  reasoning_round: "推理阶段",
  note_retrieval: "笔记读取",
  agent_message_sent: "发送协作",
  agent_message_received: "接收协作",
  subagent_completed: "子代理完成",
  subagent_started: "子代理启动",
  session_started: "会话开始",
  session_completed: "会话完成",
  session_failed: "会话失败",
  session_created: "会话创建",
};

const SEVERITY_META = {
  high: { label: "高危", color: "#2563eb" },
  medium: { label: "中危", color: "#60a5fa" },
  low: { label: "低危", color: "#bfdbfe" },
};

const DEFAULT_TASK_FORM = {
  title: "",
  objective: "对目标二进制做初始攻击面梳理、基础证据采样，并总结可能的漏洞突破口。",
  difficulty: "auto",
  maxSubagents: "3",
  tags: "",
};

const HIGH_FINDING_PATTERNS = [
  /高危/,
  /极高/,
  /格式化字符串漏洞/,
  /命令执行/,
  /任意代码执行/,
  /任意地址写/,
  /覆写.*target/,
  /shell/i,
  /可写 GOT/i,
  /利用链结论/,
];

const MEDIUM_FINDING_PATTERNS = [
  /中危/,
  /中等/,
  /信息泄露/,
  /溢出/,
  /越界/,
  /读写/,
  /格式串/,
  /泄露/,
  /可控数据/,
];

const LOW_FINDING_PATTERNS = [
  /低危/,
  /低风险/,
  /攻击面/,
  /保护机制/,
  /输入点/,
  /危险导入/,
  /加固/,
];

const state = {
  sessions: [],
  selectedSessionId: null,
  selectionCleared: false,
  currentView: "home",
  autoRefresh: true,
  refreshTimer: null,
  renderTimer: null,
  runtimeProfile: null,
  toolCapabilities: [],
  knowledgeEntries: [],
  deepseekSettings: null,
  apiCheckResult: null,
  selectedProjectSessionIds: new Set(),
  selectedCompletedSessionIds: new Set(),
  selectedKnowledgeEntryIds: new Set(),
  socket: null,
  wsConnected: false,
  wsRetryTimer: null,
  liveEventsBySession: {},
  modalOpen: false,
  dialogResolver: null,
  progressDisplay: {},
  expandedPanels: {},
  loadingSessionIds: new Set(),
  knowledgeLoadedAt: 0,
  knowledgeDirty: true,
};

const elements = {
  contentArea: document.querySelector(".content-area"),
  viewKicker: document.getElementById("view-kicker"),
  viewTitle: document.getElementById("view-title"),
  navButtons: Array.from(document.querySelectorAll("[data-view-target]")),
  viewSections: Array.from(document.querySelectorAll(".view")),
  clearSessionSelectionButton: document.getElementById("clear-session-selection-button"),
  openCreateTaskModalButton: document.getElementById("open-create-task-modal-button"),
  heroCreateTaskButton: document.getElementById("hero-create-task-button"),
  refreshProjectsButton: document.getElementById("refresh-projects-button"),
  toggleCompletedSelectionButton: document.getElementById("toggle-completed-selection-button"),
  bulkDeleteCompletedButton: document.getElementById("bulk-delete-completed-button"),
  toggleProjectSelectionButton: document.getElementById("toggle-project-selection-button"),
  bulkDeleteProjectsButton: document.getElementById("bulk-delete-projects-button"),
  toggleKnowledgeSelectionButton: document.getElementById("toggle-knowledge-selection-button"),
  bulkDeleteKnowledgeButton: document.getElementById("bulk-delete-knowledge-button"),
  autoRefreshToggle: null,
  pendingTaskCount: document.getElementById("pending-task-count"),
  activeTaskCount: document.getElementById("active-task-count"),
  completedTaskCount: document.getElementById("completed-task-count"),
  issueTotalCount: document.getElementById("issue-total-count"),
  severityChart: document.getElementById("severity-chart"),
  severityLegend: document.getElementById("severity-legend"),
  trendChart: document.getElementById("trend-chart"),
  pendingTaskList: document.getElementById("pending-task-list"),
  activeTaskList: document.getElementById("active-task-list"),
  completedTaskList: document.getElementById("completed-task-list"),
  projectList: document.getElementById("project-list"),
  projectDetail: document.getElementById("project-detail"),
  taskManagementSummary: document.getElementById("task-management-summary"),
  taskAgentBoard: document.getElementById("task-agent-board"),
  agentLogList: document.getElementById("agent-log-list"),
  progressLogList: document.getElementById("progress-log-list"),
  reportSessionSummary: document.getElementById("report-session-summary"),
  reportPreview: document.getElementById("report-preview"),
  knowledgeSummary: document.getElementById("knowledge-summary"),
  knowledgeList: document.getElementById("knowledge-list"),
  systemStatusGrid: document.getElementById("system-status-grid"),
  toolGrid: document.getElementById("tool-grid"),
  deepseekSettingsForm: document.getElementById("deepseek-settings-form"),
  settingsApiKeyInput: document.getElementById("settings-api-key"),
  settingsApiKeyHint: document.getElementById("settings-api-key-hint"),
  saveApiKeyButton: document.getElementById("save-api-key-button"),
  checkApiButton: document.getElementById("check-api-button"),
  apiCheckStatus: document.getElementById("api-check-status"),
  createTaskModal: document.getElementById("create-task-modal"),
  closeCreateTaskModalButton: document.getElementById("close-create-task-modal-button"),
  createTaskForm: document.getElementById("create-task-form"),
  createTaskSubmitButton: document.getElementById("create-task-submit-button"),
  resetCreateTaskButton: document.getElementById("reset-create-task-button"),
  taskFileInput: document.getElementById("task-file"),
  taskFileMeta: document.getElementById("task-file-meta"),
  taskTitle: document.getElementById("task-title"),
  taskDifficulty: document.getElementById("task-difficulty"),
  taskObjective: document.getElementById("task-objective"),
  taskMaxSubagents: document.getElementById("task-max-subagents"),
  taskTags: document.getElementById("task-tags"),
  appDialogModal: document.getElementById("app-dialog-modal"),
  closeAppDialogButton: document.getElementById("close-app-dialog-button"),
  appDialogKicker: document.getElementById("app-dialog-kicker"),
  appDialogTitle: document.getElementById("app-dialog-title"),
  appDialogMessage: document.getElementById("app-dialog-message"),
  appDialogCancelButton: document.getElementById("app-dialog-cancel-button"),
  appDialogConfirmButton: document.getElementById("app-dialog-confirm-button"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatTime(value) {
  if (!value) {
    return "N/A";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function formatShortDate(value) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function formatTokenCount(value) {
  const amount = Number(value || 0);
  if (!Number.isFinite(amount) || amount <= 0) {
    return "0";
  }
  return new Intl.NumberFormat("zh-CN").format(Math.round(amount));
}

function normalizeTokenUsage(usage) {
  const source = usage || {};
  return {
    prompt_tokens: Number(source.prompt_tokens || 0),
    completion_tokens: Number(source.completion_tokens || 0),
    total_tokens: Number(source.total_tokens || 0),
    reasoning_tokens: Number(source.reasoning_tokens || 0),
    cached_tokens: Number(source.cached_tokens || 0),
    llm_calls: Number(source.llm_calls || 0),
  };
}

function addTokenUsage(base, extra) {
  const left = normalizeTokenUsage(base);
  const right = normalizeTokenUsage(extra);
  return {
    prompt_tokens: left.prompt_tokens + right.prompt_tokens,
    completion_tokens: left.completion_tokens + right.completion_tokens,
    total_tokens: left.total_tokens + right.total_tokens,
    reasoning_tokens: left.reasoning_tokens + right.reasoning_tokens,
    cached_tokens: left.cached_tokens + right.cached_tokens,
    llm_calls: left.llm_calls + right.llm_calls,
  };
}

function getTaskTokenUsage(task) {
  return normalizeTokenUsage(task?.token_usage);
}

function getSessionTokenUsage(session) {
  const direct = normalizeTokenUsage(session?.token_usage);
  if (direct.total_tokens || direct.llm_calls) {
    return direct;
  }
  let aggregate = normalizeTokenUsage(session?.manager_token_usage);
  for (const task of session?.subagents || []) {
    aggregate = addTokenUsage(aggregate, task?.token_usage);
  }
  return aggregate;
}

function formatTokenBreakdown(usage) {
  const normalized = normalizeTokenUsage(usage);
  return `P ${formatTokenCount(normalized.prompt_tokens)} / C ${formatTokenCount(normalized.completion_tokens)}`;
}

function truncateText(text, limit = 96) {
  const normalized = String(text || "").replace(/\s+/g, " ").trim();
  if (normalized.length <= limit) {
    return normalized;
  }
  return `${normalized.slice(0, Math.max(0, limit - 1)).trim()}…`;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      if (data.detail) {
        message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return null;
  }
  return response.json();
}

function syncModalBodyLock() {
  const anyOpen = !elements.createTaskModal.hidden || !elements.appDialogModal.hidden;
  state.modalOpen = anyOpen;
  document.body.classList.toggle("modal-open", anyOpen);
}

function closeAppDialog(result = false) {
  if (elements.appDialogModal.hidden) {
    return;
  }
  elements.appDialogModal.hidden = true;
  syncModalBodyLock();
  const resolver = state.dialogResolver;
  state.dialogResolver = null;
  if (typeof resolver === "function") {
    resolver(result);
  }
}

function showDialog({
  kicker = "提示",
  title = "系统提示",
  message,
  confirmLabel = "确认",
  cancelLabel = "取消",
  showCancel = false,
  danger = false,
} = {}) {
  if (state.dialogResolver) {
    closeAppDialog(false);
  }
  elements.appDialogKicker.textContent = kicker;
  elements.appDialogTitle.textContent = title;
  elements.appDialogMessage.textContent = message || "";
  elements.appDialogCancelButton.hidden = !showCancel;
  elements.appDialogCancelButton.textContent = cancelLabel;
  elements.appDialogConfirmButton.textContent = confirmLabel;
  elements.appDialogConfirmButton.classList.toggle("button-danger", danger);
  elements.appDialogConfirmButton.classList.toggle("button-primary", !danger);
  elements.appDialogModal.hidden = false;
  syncModalBodyLock();
  return new Promise((resolve) => {
    state.dialogResolver = resolve;
  });
}

function notify(message, title = "系统提示") {
  return showDialog({
    kicker: "提示",
    title,
    message,
    confirmLabel: "知道了",
    showCancel: false,
  });
}

function confirmAction(message, title = "确认操作", confirmLabel = "确认删除") {
  return showDialog({
    kicker: "确认",
    title,
    message,
    confirmLabel,
    cancelLabel: "取消",
    showCancel: true,
    danger: true,
  });
}

function triggerDownload(url) {
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

function labelForStatus(status) {
  return STATUS_LABELS[status] || status || "未知";
}

function labelForRole(role) {
  return ROLE_LABELS[role] || role || "子代理";
}

function agentNameForRole(role) {
  if (role === "manager") {
    return "Manager Agent";
  }
  return `${labelForRole(role)} Agent`;
}

function isPanelExpanded(key, defaultOpen = false) {
  if (Object.prototype.hasOwnProperty.call(state.expandedPanels, key)) {
    return Boolean(state.expandedPanels[key]);
  }
  return defaultOpen;
}

function getPanelOpenAttr(key, defaultOpen = false) {
  return isPanelExpanded(key, defaultOpen) ? "open" : "";
}

function rememberExpandedPanels(root) {
  if (!(root instanceof Element)) {
    return;
  }
  root.querySelectorAll("details[data-panel-key]").forEach((panel) => {
    if (!(panel instanceof HTMLDetailsElement)) {
      return;
    }
    const panelKey = panel.dataset.panelKey;
    if (!panelKey) {
      return;
    }
    state.expandedPanels[panelKey] = panel.open;
  });
}

function labelForEventKind(kind) {
  return EVENT_KIND_LABELS[kind] || kind || "事件";
}

function getLatestRoundIndex(session) {
  const taskRounds = (session?.subagents || []).map((task) => Number(task.round_index) || 1);
  return Math.max(Number(session?.manager_round) || 0, ...taskRounds, 1);
}

function getRoundTasks(session, roundIndex = getLatestRoundIndex(session)) {
  return (session?.subagents || []).filter((task) => (Number(task.round_index) || 1) === roundIndex);
}

function syncViewChrome(viewName) {
  const resolved = VIEW_META[viewName] ? viewName : "home";
  const meta = VIEW_META[resolved];
  elements.viewKicker.textContent = meta.kicker;
  elements.viewTitle.textContent = meta.title;

  elements.navButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.viewTarget === resolved);
  });
}

function showViewInstantly(viewName) {
  const resolved = VIEW_META[viewName] ? viewName : "home";
  elements.viewSections.forEach((section) => {
    section.classList.toggle("is-active", section.dataset.view === resolved);
    section.classList.remove("is-transitioning", "is-leaving");
  });
}

function prefersReducedMotion() {
  return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function setView(viewName, { animate = true } = {}) {
  const resolved = VIEW_META[viewName] ? viewName : "home";
  const current = elements.viewSections.find((section) => section.classList.contains("is-active")) || null;
  const next = elements.viewSections.find((section) => section.dataset.view === resolved) || null;
  state.currentView = resolved;
  syncViewChrome(resolved);

  if (resolved === "task-management" || resolved === "reports") {
    const selected = ensureSelectedSession();
    if (selected?._compact) {
      void ensureDetailedSession(selected.id);
    }
  }
  if (resolved === "knowledge") {
    void ensureKnowledgeEntries();
  }

  if (!next) {
    showViewInstantly("home");
    return;
  }

  if (
    !animate
    || prefersReducedMotion()
    || !current
    || current === next
    || typeof current.animate !== "function"
    || typeof next.animate !== "function"
  ) {
    showViewInstantly(resolved);
    return;
  }

  elements.viewSections.forEach((section) => {
    if (typeof section.getAnimations === "function") {
      section.getAnimations().forEach((animation) => animation.cancel());
    }
  });

  const lockedHeight = Math.max(current.offsetHeight, next.offsetHeight, 420);
  if (elements.contentArea) {
    elements.contentArea.style.minHeight = `${lockedHeight}px`;
  }

  elements.viewSections.forEach((section) => {
    if (section !== current && section !== next) {
      section.classList.remove("is-active", "is-transitioning", "is-leaving");
    }
  });

  current.classList.add("is-active", "is-transitioning", "is-leaving");
  next.classList.add("is-active", "is-transitioning");

  const outgoing = current.animate(
    [
      { opacity: 1, transform: "translateY(0) scale(1)", filter: "blur(0px)" },
      { opacity: 0, transform: "translateY(18px) scale(0.985)", filter: "blur(8px)" },
    ],
    {
      duration: 240,
      easing: "cubic-bezier(0.4, 0, 0.2, 1)",
      fill: "forwards",
    }
  );
  const incoming = next.animate(
    [
      { opacity: 0, transform: "translateY(22px) scale(0.985)", filter: "blur(10px)" },
      { opacity: 1, transform: "translateY(0) scale(1)", filter: "blur(0px)" },
    ],
    {
      duration: 320,
      easing: "cubic-bezier(0.2, 0.8, 0.2, 1)",
      fill: "forwards",
    }
  );

  Promise.allSettled([outgoing.finished, incoming.finished]).then(() => {
    elements.viewSections.forEach((section) => {
      section.classList.toggle("is-active", section === next);
      section.classList.remove("is-transitioning", "is-leaving");
    });
    if (elements.contentArea) {
      window.setTimeout(() => {
        if (state.currentView === resolved) {
          elements.contentArea.style.minHeight = "";
        }
      }, 30);
    }
  });
}

function scheduleRender(delay = 80) {
  if (state.renderTimer) {
    return;
  }
  state.renderTimer = window.setTimeout(() => {
    state.renderTimer = null;
    renderAll();
  }, delay);
}

function sortSessions() {
  state.sessions.sort((left, right) => {
    const leftTime = new Date(left.updated_at || left.created_at || 0).getTime();
    const rightTime = new Date(right.updated_at || right.created_at || 0).getTime();
    return rightTime - leftTime;
  });
}

function pruneSelections() {
  const sessionIds = new Set(state.sessions.map((session) => session.id));
  state.selectedProjectSessionIds = new Set(
    [...state.selectedProjectSessionIds].filter((sessionId) => sessionIds.has(sessionId))
  );
  state.selectedCompletedSessionIds = new Set(
    [...state.selectedCompletedSessionIds].filter((sessionId) => (
      sessionIds.has(sessionId) && state.sessions.some((session) => session.id === sessionId && session.status === "completed")
    ))
  );
  const knowledgeIds = new Set(state.knowledgeEntries.map((entry) => entry.id));
  state.selectedKnowledgeEntryIds = new Set(
    [...state.selectedKnowledgeEntryIds].filter((entryId) => knowledgeIds.has(entryId))
  );

  const activeProgressKeys = new Set();
  for (const session of state.sessions) {
    activeProgressKeys.add(`session:${session.id}`);
    for (const task of session.subagents || []) {
      activeProgressKeys.add(`task:${task.id}`);
    }
  }
  state.progressDisplay = Object.fromEntries(
    Object.entries(state.progressDisplay).filter(([key]) => activeProgressKeys.has(key))
  );
}

function toggleSetMembership(bucket, value) {
  if (bucket.has(value)) {
    bucket.delete(value);
  } else {
    bucket.add(value);
  }
}

function upsertSession(session) {
  const index = state.sessions.findIndex((item) => item.id === session.id);
  if (index >= 0) {
    state.sessions[index] = session;
  } else {
    state.sessions.push(session);
  }
  sortSessions();
  pruneSelections();
}

function getSelectedSession() {
  return state.sessions.find((item) => item.id === state.selectedSessionId) || null;
}

function ensureSelectedSession() {
  if (state.selectedSessionId) {
    const selected = getSelectedSession();
    if (selected) {
      return selected;
    }
  }
  if (!state.selectionCleared && state.sessions.length) {
    state.selectedSessionId = state.sessions[0].id;
    return state.sessions[0];
  }
  return null;
}

function selectSession(sessionId) {
  state.selectionCleared = false;
  state.selectedSessionId = sessionId;
  scheduleRender(0);
}

function clearSelectedSession() {
  state.selectionCleared = true;
  state.selectedSessionId = null;
  scheduleRender(0);
}

function normalizeSummaryLine(line) {
  return line
    .replace(/^[-*]\s+/, "")
    .replace(/^\d+\.\s+/, "")
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .trim();
}

function extractSummaryHighlights(text, limit = 4) {
  if (!text) {
    return [];
  }
  const lines = text
    .split("\n")
    .map((line) => normalizeSummaryLine(line))
    .filter((line) => line && !line.startsWith("工具调用概览") && !line.startsWith("干预记录"));
  return [...new Set(lines)].slice(0, limit);
}

function classifySeverity(text) {
  if (!text) {
    return null;
  }
  const normalized = String(text).replace(/\s+/g, " ").trim();
  if (!normalized) {
    return null;
  }
  if (HIGH_FINDING_PATTERNS.some((pattern) => pattern.test(normalized))) {
    return "high";
  }
  if (MEDIUM_FINDING_PATTERNS.some((pattern) => pattern.test(normalized))) {
    return "medium";
  }
  if (LOW_FINDING_PATTERNS.some((pattern) => pattern.test(normalized))) {
    return "low";
  }
  if (/漏洞|问题|风险/.test(normalized)) {
    return "medium";
  }
  return null;
}

function deriveSessionMetrics(session) {
  const buckets = {
    high: 0,
    medium: 0,
    low: 0,
  };
  const findingLines = [];
  const seen = new Set();
  const sources = [];

  if (session.final_report) {
    sources.push(...session.final_report.split("\n"));
  }
  for (const task of session.subagents || []) {
    sources.push(...(task.promoted_notes || []));
    sources.push(...extractSummaryHighlights(task.output_summary || "", 5));
  }

  for (const rawLine of sources) {
    const line = normalizeSummaryLine(rawLine || "");
    if (!line || line.length < 4) {
      continue;
    }
    if (line.startsWith("角色覆盖") || line.startsWith("证据来源") || line.startsWith("状态") || line.startsWith("模型")) {
      continue;
    }
    if (seen.has(line)) {
      continue;
    }
    seen.add(line);
    const severity = classifySeverity(line);
    if (!severity) {
      continue;
    }
    buckets[severity] += 1;
    findingLines.push({ text: line, severity });
  }

  return {
    counts: buckets,
    total: buckets.high + buckets.medium + buckets.low,
    findings: findingLines,
  };
}

function getTaskEventList(task, sessionEntries) {
  if (Array.isArray(sessionEntries)) {
    return sessionEntries
      .filter((entry) => entry.taskId === task.id)
      .map((entry) => entry.event)
      .filter(Boolean);
  }
  return task.events || [];
}

function getTaskObservedToolIds(task, sessionEntries) {
  const observed = new Set((task.evidence || []).map((item) => item.command_id).filter(Boolean));
  for (const event of getTaskEventList(task, sessionEntries)) {
    if (event?.kind !== "tool_result") {
      continue;
    }
    const toolId = event.payload?.command_key || event.payload?.tool_id;
    if (toolId) {
      observed.add(toolId);
    }
  }
  return observed;
}

function getTaskPlannedSteps(task) {
  if (Array.isArray(task.planned_steps) && task.planned_steps.length) {
    return task.planned_steps;
  }
  if (Array.isArray(task.expected_evidence) && task.expected_evidence.length) {
    return task.expected_evidence;
  }
  return [];
}

function getTaskTotalSteps(task, sessionEntries) {
  const plannedCount = Number(task.manager_step_total) || getTaskPlannedSteps(task).length;
  const observedCount = getTaskObservedToolIds(task, sessionEntries).size;
  return Math.max(plannedCount, observedCount, 1);
}

function getTaskLiveProgressUnits(task, sessionEntries) {
  const total = getTaskTotalSteps(task, sessionEntries);
  const observedCount = getTaskObservedToolIds(task, sessionEntries).size;
  const coordinationCount = getTaskEventList(task, sessionEntries).filter((event) => (
    event?.kind === "agent_message_sent" || event?.kind === "agent_message_received"
  )).length;
  const outputUnits = task.output_summary ? 1 : 0;
  const latestEvent = getLatestTaskEvent(task, sessionEntries) ? 1 : 0;
  const managerApproved = Number(task.manager_step_completed) || 0;
  const provisionalTarget = task.manager_completion_confirmed ? total : Math.max(total - 1, 1);
  const liveUnits = Math.min(total, outputUnits + observedCount + (coordinationCount ? 1 : 0) + latestEvent);
  return Math.max(managerApproved, Math.min(provisionalTarget, liveUnits));
}

function getTaskFinishedSteps(task, sessionEntries) {
  const total = getTaskTotalSteps(task, sessionEntries);
  if (task.manager_completion_confirmed) {
    return total;
  }
  return Math.min(total, getTaskLiveProgressUnits(task, sessionEntries));
}

function getTaskProgressPercent(task, sessionEntries) {
  const total = getTaskTotalSteps(task, sessionEntries);
  const finished = getTaskFinishedSteps(task, sessionEntries);
  if (task.manager_completion_confirmed) {
    return 100;
  }
  if (task.status === "failed") {
    return Math.max(18, Math.round((finished / total) * 100));
  }
  if (task.status === "queued") {
    return 5;
  }
  if (!finished) {
    return 12;
  }
  if (task.status === "completed") {
    return Math.min(98, Math.round((finished / total) * 100));
  }
  return Math.min(96, Math.round((finished / total) * 100));
}

function getSessionProgressPercent(session, sessionEntries) {
  const tasks = getRoundTasks(session);
  if (!tasks.length) {
    return session.status === "running" ? 28 : 0;
  }
  const totalSteps = tasks.reduce((sum, task) => sum + getTaskTotalSteps(task, sessionEntries), 0);
  const finishedSteps = tasks.reduce((sum, task) => sum + getTaskFinishedSteps(task, sessionEntries), 0);
  if (!totalSteps) {
    return session.status === "running" ? 28 : 0;
  }
  const allConfirmed = tasks.every((task) => task.manager_completion_confirmed);
  if (session.status === "completed" && allConfirmed) {
    return 100;
  }
  return Math.max(4, Math.min(session.status === "completed" ? 98 : 96, Math.round((finishedSteps / totalSteps) * 100)));
}

function getAnimatedProgressValue(key, target, status) {
  const normalizedTarget = Math.max(0, Math.min(100, Math.round(target)));
  const existing = state.progressDisplay[key];
  if (typeof existing !== "number") {
    state.progressDisplay[key] = normalizedTarget;
    return normalizedTarget;
  }

  const delta = normalizedTarget - existing;
  if (!delta) {
    return existing;
  }

  const maxStep = delta > 0
    ? (status === "completed" ? 10 : 6)
    : 4;
  const next = Math.round(existing + Math.sign(delta) * Math.min(Math.abs(delta), maxStep));
  state.progressDisplay[key] = next;
  if (next !== normalizedTarget) {
    scheduleRender(140);
  }
  return next;
}

function getDisplayedTaskProgress(task, sessionEntries) {
  return getAnimatedProgressValue(`task:${task.id}`, getTaskProgressPercent(task, sessionEntries), task.status);
}

function getDisplayedSessionProgress(session, sessionEntries) {
  return getAnimatedProgressValue(`session:${session.id}`, getSessionProgressPercent(session, sessionEntries), session.status);
}

function getTargetFileName(session) {
  const path = session?.request?.target_path || "";
  return path.split("/").pop() || "未知样本";
}

function flattenSessionEntries(session) {
  if (!session) {
    return [];
  }

  const taskRoleById = new Map((session.subagents || []).map((task) => [task.id, task.role]));
  const entries = [];
  const sessionEvents = (session.events || []).slice(-80);

  for (const event of sessionEvents) {
    entries.push({ taskId: null, taskRole: "manager", event });
  }

  for (const task of session.subagents || []) {
    for (const event of (task.events || []).slice(-80)) {
      entries.push({ taskId: task.id, taskRole: task.role, event });
    }
  }

  for (const entry of state.liveEventsBySession[session.id] || []) {
    entries.push({
      taskId: entry.taskId || null,
      taskRole: taskRoleById.get(entry.taskId) || "manager",
      event: entry.event,
    });
  }

  const deduped = [];
  const seen = new Set();
  for (const item of entries) {
    const event = item.event || {};
    const key = [
      item.taskId || "",
      event.created_at || "",
      event.kind || "",
      event.agent_id || "",
      event.message || "",
    ].join("|");
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    deduped.push(item);
  }

  deduped.sort((left, right) => {
    const leftTime = new Date(left.event?.created_at || 0).getTime();
    const rightTime = new Date(right.event?.created_at || 0).getTime();
    return leftTime - rightTime;
  });
  return deduped;
}

function filterEntriesForRound(entries, session, roundIndex) {
  const taskIds = new Set(getRoundTasks(session, roundIndex).map((task) => task.id));
  return entries.filter((entry) => {
    if (entry.taskId) {
      return taskIds.has(entry.taskId);
    }
    const payloadRound = Number(entry.event?.payload?.round_index || 0);
    const nextRound = Number(entry.event?.payload?.next_round_index || 0);
    if (!payloadRound && !nextRound) {
      return true;
    }
    return payloadRound === roundIndex || nextRound === roundIndex;
  });
}

function getLatestTaskEvent(task, entries) {
  for (let index = entries.length - 1; index >= 0; index -= 1) {
    const item = entries[index];
    if (item.taskId === task.id) {
      return item.event;
    }
  }
  return task.events?.length ? task.events[task.events.length - 1] : null;
}

function summarizeRecipients(recipients) {
  if (!recipients?.length) {
    return "所有同伴agent";
  }
  return recipients.map((item) => agentNameForRole(item)).join("、");
}

function stripCoordinationLead(text) {
  return String(text || "")
    .replace(/^(?:好的|收到)[，,\s]*/u, "")
    .replace(/^[A-Za-z][A-Za-z0-9-]*\s+(规划摘要|证据进展|结论摘要)：\s*/u, "")
    .replace(/^[A-Za-z][A-Za-z0-9-]*\s+(遇到阻塞|回应协查)：\s*/u, "$1：")
    .replace(/^[^。！？]*以下是[^。！？]*[。！？]\s*/u, "");
}

function normalizeCoordinationTopic(topic) {
  const normalized = String(topic || "").replace(/\s+/g, " ").trim();
  if (!normalized || ["初始分工", "最终结论", "协查回应"].includes(normalized)) {
    return "";
  }
  return normalized;
}

function extractCoordinationSummaryLines(text, limit = 3) {
  const normalized = stripCoordinationLead(text)
    .replace(/\*\*/g, "")
    .replace(/\s*(\d+\.)\s*/g, "\n$1 ")
    .replace(/\s+([-*])\s+/g, "\n$1 ")
    .replace(/。/g, "。\n")
    .replace(/；/g, "；\n")
    .split("\n")
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter(Boolean);

  const compactLines = [];
  const seen = new Set();
  for (const line of normalized) {
    const cleaned = line
      .replace(/^\d+\.\s*/, "")
      .replace(/^[-*]\s*/, "")
      .trim();
    if (
      !cleaned
      || seen.has(cleaned)
      || /^(?:当前已确认|希望同伴协查|当前阻塞|已验证发现|关键函数深度分析|利用性判断|值得提升为核心笔记的结论)$/u.test(cleaned)
    ) {
      continue;
    }
    seen.add(cleaned);
    compactLines.push(truncateText(cleaned, 150));
    if (compactLines.length >= limit) {
      break;
    }
  }
  return compactLines;
}

function buildCoordinationDescriptor(event, direction, taskRole = "") {
  const kind = event?.payload?.message_kind || "update";
  const senderRole = event?.payload?.sender_role || taskRole || "manager";
  const senderText = agentNameForRole(senderRole);
  const recipientText = direction === "sent"
    ? summarizeRecipients(event?.payload?.recipients || [])
    : (taskRole ? agentNameForRole(taskRole) : "当前agent");
  const kindText = getCoordinationKindLabel(kind);
  const topicText = normalizeCoordinationTopic(event?.payload?.topic || "");
  const previewSource = event?.payload?.content_preview || event?.message || "";
  const fullContent = String(event?.payload?.content || previewSource || "").trim();
  const summaryLines = extractCoordinationSummaryLines(previewSource, 3);
  const headline = `${senderText} 向 ${recipientText} 发送${kindText}消息`;
  const compactSummary = summaryLines[0] || topicText || "等待更多协作内容。";
  return {
    kind,
    kindText,
    headline,
    topicText,
    summaryLines,
    fullContent,
    compactText: `${headline}：${compactSummary}`,
    shortHeadline: direction === "sent"
      ? `向 ${recipientText} 发送${kindText}`
      : `接收 ${senderText} 的${kindText}`,
  };
}

function getCoordinationKindLabel(kind) {
  if (kind === "question") {
    return "协查问题";
  }
  if (kind === "answer") {
    return "协查回应";
  }
  if (kind === "summary") {
    return "最终结论";
  }
  if (kind === "plan") {
    return "初始规划";
  }
  return "阶段同步";
}

function getCoordinationPreview(event) {
  const descriptor = buildCoordinationDescriptor(event, "sent");
  return descriptor.summaryLines[0] || descriptor.topicText || "无正文";
}

function describeCoordinationEvent(event, direction, taskRole = "") {
  return buildCoordinationDescriptor(event, direction, taskRole).compactText;
}

function describeEventMessage(event, taskRole = "") {
  if (!event) {
    return "";
  }
  if (event.kind === "reasoning_round" && event.payload?.scope === "manager") {
    if (event.payload?.correction_summary) {
      return truncateText(event.payload.correction_summary, 220);
    }
    if (event.payload?.reason) {
      return `Manager 进入下一轮规划：${truncateText(event.payload.reason, 180)}`;
    }
    return event.payload?.manager_plan_summary
      ? truncateText(event.payload.manager_plan_summary, 180)
      : "管理代理正在构建本轮调度方案。";
  }
  if (event.kind === "reasoning_round" && event.payload?.phase_label) {
    return `${event.payload.phase_label}，子代理会结合同伴消息继续细化证据。`;
  }
  if (event.kind === "tool_invocation") {
    return `正在调用 ${event.payload?.command_key || event.payload?.tool_id || "工具"}。`;
  }
  if (event.kind === "tool_result") {
    const toolId = event.payload?.command_key || event.payload?.tool_id || "工具";
    return `${toolId} 已返回，当前状态为 ${labelForStatus(event.payload?.status)}。`;
  }
  if (event.kind === "llm_usage_recorded") {
    const model = event.payload?.model || "LLM";
    const total = formatTokenCount(event.payload?.total_tokens || 0);
    return `${model} 本次新增 ${total} token。`;
  }
  if (event.kind === "agent_message_sent") {
    return describeCoordinationEvent(event, "sent", taskRole);
  }
  if (event.kind === "agent_message_received") {
    return describeCoordinationEvent(event, "received", taskRole);
  }
  if (event.kind === "subagent_completed") {
    return "子代理已完成并回填当前阶段结论。";
  }
  if (event.kind === "subagent_started") {
    return "子代理已启动，开始执行当前任务。";
  }
  if (event.kind === "session_completed") {
    return "会话已完成，管理代理已经生成最终报告。";
  }
  if (event.kind === "session_failed") {
    return event.message || "会话执行失败。";
  }
  return event.message || "";
}

function buildManagerPlanStructuredPanel(session) {
  const plan = session?.manager_plan;
  if (!plan) {
    return "";
  }
  const phasePlan = Array.isArray(plan.phase_plan) ? plan.phase_plan : [];
  const riskWatchpoints = Array.isArray(plan.risk_watchpoints) ? plan.risk_watchpoints : [];
  const roles = Array.isArray(plan.roles) ? plan.roles : [];

  return `
    <div class="manager-plan-structured">
      <div class="manager-plan-metrics">
        <span>当前第 ${escapeHtml(getLatestRoundIndex(session))} 轮</span>
        <span>累计 ${escapeHtml((session.manager_plan_history || []).length || 1)} 次规划</span>
        <span>${roles.length} 个角色</span>
        <span>${phasePlan.length} 个阶段</span>
        <span>${riskWatchpoints.length} 个风险观察</span>
      </div>
      ${phasePlan.length ? `
        <div class="manager-phase-strip">
          ${phasePlan.map((phase) => `
            <article class="manager-phase-item">
              <strong>${escapeHtml(phase.phase || "阶段")}</strong>
              <p>${escapeHtml(phase.goal || "")}</p>
              <span>${escapeHtml((phase.owner_roles || []).join(" / ") || "全体协同")}</span>
            </article>
          `).join("")}
        </div>
      ` : ""}
      ${roles.length ? `
        <div class="manager-role-lines">
          ${roles.map((role) => `
            <article class="manager-role-line">
              <div class="manager-role-line-head">
                <strong>${escapeHtml(agentNameForRole(role.role))}</strong>
                <span>${escapeHtml(role.stage_goal || "明确 exploit stage 边界")}</span>
              </div>
              <p>${escapeHtml(truncateText(role.objective || "", 140))}</p>
              ${(role.planned_steps || []).length ? `
                <div class="manager-role-evidence">
                  ${(role.planned_steps || []).slice(0, 4).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
                </div>
              ` : ""}
              ${(role.expected_evidence || []).length ? `
                <div class="manager-role-evidence">
                  ${(role.expected_evidence || []).slice(0, 3).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
                </div>
              ` : ""}
            </article>
          `).join("")}
        </div>
      ` : ""}
    </div>
  `;
}

function buildManagerPlanPanel(session) {
  if (!session?.manager_plan_summary && !session?.manager_plan) {
    return "";
  }
  const panelKey = `manager-plan:${session.id}`;
  return `
    <details class="manager-plan-details" data-panel-key="${escapeHtml(panelKey)}" ${getPanelOpenAttr(panelKey, true)}>
      <summary>
        <span>Manager 深度规划</span>
        <span class="manager-plan-hint">${isPanelExpanded(panelKey, true) ? "点击收起" : "点击展开"}</span>
      </summary>
      ${buildManagerPlanStructuredPanel(session)}
      <div class="manager-plan-body rich-text">
        ${renderStructuredText(session.manager_plan_summary || "")}
      </div>
    </details>
  `;
}

function buildSharedMemoryPanel(session) {
  const entries = Array.isArray(session?.shared_memory) ? session.shared_memory.slice(-8).reverse() : [];
  if (!entries.length) {
    return "";
  }
  const panelKey = `shared-memory:${session.id}`;
  return `
    <details class="manager-plan-details" data-panel-key="${escapeHtml(panelKey)}" ${getPanelOpenAttr(panelKey, false)}>
      <summary>
        <span>共享记忆</span>
        <span class="manager-plan-hint">${entries.length} 条稳定事实</span>
      </summary>
      <div class="manager-plan-body rich-text">
        ${entries.map((entry) => `
          <p><strong>${escapeHtml(entry.role || entry.category || "memory")}</strong> · ${escapeHtml(entry.content || "")}</p>
        `).join("")}
      </div>
    </details>
  `;
}

function renderInlineStructuredText(text) {
  const source = String(text ?? "");
  const parts = [];
  let lastIndex = 0;
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let match;

  while ((match = pattern.exec(source)) !== null) {
    if (match.index > lastIndex) {
      parts.push(escapeHtml(source.slice(lastIndex, match.index)));
    }
    const token = match[0];
    if (token.startsWith("`")) {
      parts.push(`<code>${escapeHtml(token.slice(1, -1))}</code>`);
    } else {
      parts.push(`<strong>${escapeHtml(token.slice(2, -2))}</strong>`);
    }
    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < source.length) {
    parts.push(escapeHtml(source.slice(lastIndex)));
  }

  return parts.join("");
}

function renderStructuredText(text) {
  if (!text) {
    return "";
  }

  const parts = [];
  let listItems = [];
  let inCodeBlock = false;
  let codeFenceLang = "";
  let codeLines = [];

  function flushList() {
    if (!listItems.length) {
      return;
    }
    parts.push(`<ul class="structured-list">${listItems.join("")}</ul>`);
    listItems = [];
  }

  function flushCodeBlock() {
    if (!codeLines.length && !inCodeBlock) {
      return;
    }
    const language = codeFenceLang || "text";
    const renderedLines = (codeLines.length ? codeLines : [""])
      .map((codeLine) => {
        const content = escapeHtml(codeLine);
        return `<span class="code-line"><span class="code-line-text">${content || "&nbsp;"}</span></span>`;
      })
      .join("");
    parts.push(
      [
        `<div class="code-block-shell" data-language="${escapeHtml(language)}">`,
        '  <div class="code-block-bar">',
        '    <span class="code-block-dots" aria-hidden="true"><span></span><span></span><span></span></span>',
        `    <span class="code-block-label">${escapeHtml(language)}</span>`,
        "  </div>",
        `  <pre class="code-block"><code class="code-block-lines">${renderedLines}</code></pre>`,
        "</div>",
      ].join("")
    );
    inCodeBlock = false;
    codeFenceLang = "";
    codeLines = [];
  }

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (line.startsWith("```")) {
      flushList();
      if (inCodeBlock) {
        flushCodeBlock();
      } else {
        inCodeBlock = true;
        codeFenceLang = line.slice(3).trim();
        codeLines = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(rawLine);
      continue;
    }

    if (!line) {
      flushList();
      continue;
    }

    if (line.startsWith("# ")) {
      flushList();
      parts.push(`<h1>${renderInlineStructuredText(line.slice(2))}</h1>`);
      continue;
    }

    if (line.startsWith("## ")) {
      flushList();
      parts.push(`<h2>${renderInlineStructuredText(line.slice(3))}</h2>`);
      continue;
    }

    if (line.startsWith("### ")) {
      flushList();
      parts.push(`<h3>${renderInlineStructuredText(line.slice(4))}</h3>`);
      continue;
    }

    const numberedMatch = line.match(/^(\d+)\.\s+(.*)$/);
    if (numberedMatch) {
      flushList();
      parts.push(
        `<h4 class="structured-step"><span class="structured-step-index">${escapeHtml(numberedMatch[1])}</span><span>${renderInlineStructuredText(numberedMatch[2])}</span></h4>`
      );
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      listItems.push(`<li>${renderInlineStructuredText(line.replace(/^[-*]\s+/, ""))}</li>`);
      continue;
    }

    flushList();
    parts.push(`<p>${renderInlineStructuredText(line)}</p>`);
  }

  flushList();
  flushCodeBlock();
  return parts.join("");
}

function buildSeverityChip(level, count) {
  const meta = SEVERITY_META[level];
  return `
    <span class="severity-chip severity-${level}">
      ${meta.label} ${count}
    </span>
  `;
}

function renderSeverityBoard(counts) {
  const total = counts.high + counts.medium + counts.low;
  if (!total) {
    elements.severityChart.innerHTML = `
      <div class="chart-empty">
        <strong>暂无问题分布</strong>
        <p>完成审计后会在这里汇总高危、中危和低危结果。</p>
      </div>
    `;
    elements.severityLegend.innerHTML = "";
    return;
  }

  const highDeg = Math.round((counts.high / total) * 360);
  const mediumDeg = Math.round((counts.medium / total) * 360);
  const lowDeg = 360 - highDeg - mediumDeg;
  const gradient = `conic-gradient(${SEVERITY_META.high.color} 0deg ${highDeg}deg, ${SEVERITY_META.medium.color} ${highDeg}deg ${highDeg + mediumDeg}deg, ${SEVERITY_META.low.color} ${highDeg + mediumDeg}deg ${highDeg + mediumDeg + lowDeg}deg)`;

  elements.severityChart.innerHTML = `
    <div class="severity-donut" style="background:${gradient}">
      <div class="severity-donut-core">
        <strong>${total}</strong>
        <span>问题总数</span>
      </div>
    </div>
  `;

  elements.severityLegend.innerHTML = `
    <article class="severity-row">
      <span class="severity-swatch severity-high"></span>
      <div>
        <strong>高危</strong>
        <p>${counts.high} 项</p>
      </div>
    </article>
    <article class="severity-row">
      <span class="severity-swatch severity-medium"></span>
      <div>
        <strong>中危</strong>
        <p>${counts.medium} 项</p>
      </div>
    </article>
    <article class="severity-row">
      <span class="severity-swatch severity-low"></span>
      <div>
        <strong>低危</strong>
        <p>${counts.low} 项</p>
      </div>
    </article>
  `;
}

function renderTrendChart(sessions) {
  const completed = sessions
    .filter((session) => session.status === "completed")
    .slice()
    .sort((left, right) => new Date(left.updated_at || left.created_at || 0) - new Date(right.updated_at || right.created_at || 0))
    .slice(-8)
    .map((session) => ({
      label: formatShortDate(session.updated_at || session.created_at),
      value: deriveSessionMetrics(session).total,
      title: session.request.title,
    }));

  if (!completed.length) {
    elements.trendChart.innerHTML = `
      <div class="chart-empty">
        <strong>暂无趋势数据</strong>
        <p>等待更多已完成任务后生成问题趋势折线。</p>
      </div>
    `;
    return;
  }

  const width = 640;
  const height = 220;
  const paddingX = 34;
  const paddingY = 24;
  const maxValue = Math.max(1, ...completed.map((item) => item.value));
  const stepX = completed.length > 1 ? (width - paddingX * 2) / (completed.length - 1) : 0;
  const points = completed.map((item, index) => {
    const x = paddingX + index * stepX;
    const y = height - paddingY - (item.value / maxValue) * (height - paddingY * 2);
    return { x, y, value: item.value, label: item.label, title: item.title };
  });
  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");
  const areaPoints = `${paddingX},${height - paddingY} ${polyline} ${points[points.length - 1].x},${height - paddingY}`;
  const guideValues = [maxValue, Math.round(maxValue / 2), 0];

  elements.trendChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" class="trend-svg" role="img" aria-label="问题趋势折线图">
      ${guideValues
        .map((value) => {
          const y = height - paddingY - (value / maxValue) * (height - paddingY * 2);
          return `
            <line x1="${paddingX}" y1="${y}" x2="${width - paddingX}" y2="${y}" class="trend-guide"></line>
            <text x="4" y="${Math.max(14, y - 4)}" class="trend-guide-label">${value}</text>
          `;
        })
        .join("")}
      <polyline points="${areaPoints}" class="trend-area"></polyline>
      <polyline points="${polyline}" class="trend-line"></polyline>
      ${points
        .map(
          (point) => `
            <circle cx="${point.x}" cy="${point.y}" r="4.5" class="trend-point"></circle>
            <text x="${point.x}" y="${height - 4}" text-anchor="middle" class="trend-x-label">${escapeHtml(point.label)}</text>
          `
        )
        .join("")}
    </svg>
    <div class="trend-meta">
      ${completed
        .map(
          (item) => `
            <article class="trend-pill">
              <strong>${escapeHtml(item.label)}</strong>
              <span>${escapeHtml(truncateText(item.title, 26))} · ${item.value} 项</span>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function buildEmptyBlock(title, message) {
  return `
    <div class="empty-block">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
}

function buildSelectionControl({ checked, target, id, label }) {
  return `
    <label class="selection-control" data-selection-target="${escapeHtml(target)}" data-selection-id="${escapeHtml(id)}">
      <input type="checkbox" ${checked ? "checked" : ""} />
      <span>${escapeHtml(label)}</span>
    </label>
  `;
}

function buildQuickTaskList(sessions, emptyMessage, options = {}) {
  const {
    selectable = false,
    selectionTarget = "",
    selectionSet = new Set(),
    limit = 5,
  } = options;
  if (!sessions.length) {
    return buildEmptyBlock("暂无任务", emptyMessage);
  }
  return sessions
    .slice(0, limit)
    .map((session) => {
      const severity = deriveSessionMetrics(session).counts;
      return `
        <article class="session-brief">
          <div class="session-brief-head">
            <div>
              <p class="session-brief-title">${escapeHtml(session.request.title)}</p>
              <p class="session-brief-meta">${escapeHtml(getTargetFileName(session))} · ${escapeHtml(formatTime(session.updated_at))}</p>
            </div>
            ${selectable ? buildSelectionControl({
              checked: selectionSet.has(session.id),
              target: selectionTarget,
              id: session.id,
              label: "选中",
            }) : ""}
          </div>
          <div class="session-brief-side">
            <span class="status-pill status-${escapeHtml(session.status)}">${escapeHtml(labelForStatus(session.status))}</span>
            <div class="project-actions">
              <button class="text-button" type="button" data-select-session="${escapeHtml(session.id)}" data-switch-view="projects">
                查看
              </button>
              <button class="text-button" type="button" data-delete-session="${escapeHtml(session.id)}">
                删除
              </button>
            </div>
          </div>
          <div class="severity-line">
            ${buildSeverityChip("high", severity.high)}
            ${buildSeverityChip("medium", severity.medium)}
            ${buildSeverityChip("low", severity.low)}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderHomeView() {
  const pending = state.sessions.filter((session) => session.status === "queued");
  const active = state.sessions.filter((session) => session.status === "running");
  const completed = state.sessions.filter((session) => session.status === "completed");
  const aggregate = state.sessions.reduce(
    (sum, session) => {
      const derived = deriveSessionMetrics(session);
      sum.high += derived.counts.high;
      sum.medium += derived.counts.medium;
      sum.low += derived.counts.low;
      return sum;
    },
    { high: 0, medium: 0, low: 0 }
  );

  elements.pendingTaskCount.textContent = String(pending.length);
  elements.activeTaskCount.textContent = String(active.length);
  elements.completedTaskCount.textContent = String(completed.length);
  elements.issueTotalCount.textContent = String(aggregate.high + aggregate.medium + aggregate.low);
  renderSeverityBoard(aggregate);
  renderTrendChart(state.sessions);
  elements.pendingTaskList.innerHTML = buildQuickTaskList(pending, "当前没有待审计任务。");
  elements.activeTaskList.innerHTML = buildQuickTaskList(active, "当前没有审计中的任务。");
  elements.completedTaskList.innerHTML = buildQuickTaskList(completed, "当前还没有已完成任务。", {
    selectable: true,
    selectionTarget: "completed-sessions",
    selectionSet: state.selectedCompletedSessionIds,
    limit: completed.length || 5,
  });
  elements.toggleCompletedSelectionButton.disabled = !completed.length;
  elements.bulkDeleteCompletedButton.disabled = !state.selectedCompletedSessionIds.size;
  elements.toggleCompletedSelectionButton.textContent = (
    completed.length && state.selectedCompletedSessionIds.size === completed.length
      ? "取消全选历史任务"
      : "全选历史任务"
  );
  elements.bulkDeleteCompletedButton.textContent = state.selectedCompletedSessionIds.size
    ? `批量删除历史任务 (${state.selectedCompletedSessionIds.size})`
    : "批量删除历史任务";
}

function buildProjectCard(session) {
  const derived = deriveSessionMetrics(session);
  const progress = getDisplayedSessionProgress(session, flattenSessionEntries(session));
  return `
    <article class="project-card ${session.id === state.selectedSessionId ? "is-active" : ""}">
      <div class="project-card-head">
        <div>
          <p class="project-card-title">${escapeHtml(session.request.title)}</p>
          <p class="project-card-meta">${escapeHtml(getTargetFileName(session))} · ${escapeHtml(formatTime(session.updated_at))}</p>
        </div>
        <div class="project-card-side">
          ${buildSelectionControl({
            checked: state.selectedProjectSessionIds.has(session.id),
            target: "project-sessions",
            id: session.id,
            label: "选中",
          })}
          <span class="status-pill status-${escapeHtml(session.status)}">${escapeHtml(labelForStatus(session.status))}</span>
        </div>
      </div>
      <p class="project-card-copy">${escapeHtml(truncateText(session.request.objective, 120))}</p>
      <div class="project-progress-track">
        <span class="project-progress-fill status-${escapeHtml(session.status)}" style="width:${progress}%"></span>
      </div>
      <div class="severity-line">
        ${buildSeverityChip("high", derived.counts.high)}
        ${buildSeverityChip("medium", derived.counts.medium)}
        ${buildSeverityChip("low", derived.counts.low)}
      </div>
      <div class="project-actions">
        <button class="button button-secondary" type="button" data-select-session="${escapeHtml(session.id)}">
          选择项目
        </button>
        <button class="button button-ghost" type="button" data-select-session="${escapeHtml(session.id)}" data-switch-view="task-management">
          任务管理
        </button>
        <button class="button button-danger" type="button" data-delete-session="${escapeHtml(session.id)}">
          删除任务
        </button>
      </div>
    </article>
  `;
}

function renderProjectsView() {
  elements.projectList.innerHTML = state.sessions.length
    ? state.sessions.map((session) => buildProjectCard(session)).join("")
    : buildEmptyBlock("暂无审计项目", "点击右上角“新建审计任务”开始创建第一条项目。");
  elements.toggleProjectSelectionButton.disabled = !state.sessions.length;
  elements.bulkDeleteProjectsButton.disabled = !state.selectedProjectSessionIds.size;
  elements.toggleProjectSelectionButton.textContent = (
    state.sessions.length && state.selectedProjectSessionIds.size === state.sessions.length
      ? "取消全选任务"
      : "全选任务"
  );
  elements.bulkDeleteProjectsButton.textContent = state.selectedProjectSessionIds.size
    ? `批量删除任务 (${state.selectedProjectSessionIds.size})`
    : "批量删除任务";

  const session = ensureSelectedSession();
  if (!session) {
    elements.projectDetail.innerHTML = buildEmptyBlock("未选择项目", "从左侧项目列表中选择一个项目查看详情。");
    return;
  }

  const derived = deriveSessionMetrics(session);
  const progress = getDisplayedSessionProgress(session, flattenSessionEntries(session));
  const completedSubagents = (session.subagents || []).filter((task) => task.status === "completed").length;
  const latestRound = getLatestRoundIndex(session);
  const sessionTokenUsage = getSessionTokenUsage(session);

  elements.projectDetail.innerHTML = `
    <article class="summary-card">
      <div class="section-heading">
        <div>
          <p class="section-kicker">当前项目</p>
          <h3>${escapeHtml(session.request.title)}</h3>
        </div>
        <span class="status-pill status-${escapeHtml(session.status)}">${escapeHtml(labelForStatus(session.status))}</span>
      </div>

      <div class="detail-grid">
        <div class="meta-card">
          <span>样本文件</span>
          <strong>${escapeHtml(getTargetFileName(session))}</strong>
        </div>
        <div class="meta-card">
          <span>更新时间</span>
          <strong>${escapeHtml(formatTime(session.updated_at))}</strong>
        </div>
        <div class="meta-card">
          <span>最大子代理数</span>
          <strong>${escapeHtml(session.request.max_subagents)}</strong>
        </div>
        <div class="meta-card">
          <span>当前轮次</span>
          <strong>第 ${latestRound} 轮</strong>
        </div>
        <div class="meta-card">
          <span>已完成子代理</span>
          <strong>${completedSubagents}/${(session.subagents || []).length || 0}</strong>
        </div>
        <div class="meta-card">
          <span>累计 Token</span>
          <strong>${formatTokenCount(sessionTokenUsage.total_tokens)}</strong>
        </div>
        <div class="meta-card">
          <span>Prompt / Completion</span>
          <strong>${escapeHtml(formatTokenBreakdown(sessionTokenUsage))}</strong>
        </div>
        <div class="meta-card">
          <span>LLM 调用</span>
          <strong>${formatTokenCount(sessionTokenUsage.llm_calls)}</strong>
        </div>
        <div class="meta-card">
          <span>共享记忆</span>
          <strong>${formatTokenCount((session.shared_memory || []).length)}</strong>
        </div>
      </div>

      <div class="project-progress-panel">
        <div class="project-progress-head">
          <span>整体进度</span>
          <strong>${progress}%</strong>
        </div>
        <div class="project-progress-track">
          <span class="project-progress-fill status-${escapeHtml(session.status)}" style="width:${progress}%"></span>
        </div>
      </div>

      <p class="summary-copy">${escapeHtml(session.request.objective)}</p>

      <div class="severity-line">
        ${buildSeverityChip("high", derived.counts.high)}
        ${buildSeverityChip("medium", derived.counts.medium)}
        ${buildSeverityChip("low", derived.counts.low)}
      </div>

      <div class="project-actions">
        <button class="button button-primary" type="button" data-switch-view="reports">查看报告</button>
        <button class="button button-secondary" type="button" data-switch-view="task-management">查看任务管理</button>
        <button class="button button-ghost" type="button" data-export-session="${escapeHtml(session.id)}" data-export-format="markdown">
          导出 Markdown
        </button>
        <button class="button button-danger" type="button" data-delete-session="${escapeHtml(session.id)}">
          删除任务
        </button>
      </div>
    </article>
  `;
}

function resolveTaskStage(task, latestEvent) {
  if (task.status === "completed" && !task.manager_completion_confirmed) {
    return "等待 Manager 复核";
  }
  if (task.status === "completed") {
    return "分析完成";
  }
  if (task.status === "failed") {
    return "执行异常";
  }
  if (task.status === "queued") {
    return "等待启动";
  }
  if (latestEvent?.kind === "reasoning_round") {
    return "整理结论";
  }
  if (latestEvent?.kind === "note_retrieval") {
    return "读取上下文";
  }
  if (latestEvent?.kind === "tool_invocation") {
    return `执行 ${latestEvent.payload?.command_key || latestEvent.payload?.tool_id || "工具"}`;
  }
  if (latestEvent?.kind === "tool_result") {
    return `${latestEvent.payload?.command_key || latestEvent.payload?.tool_id || "工具"} 已返回`;
  }
  if (latestEvent?.kind === "llm_usage_recorded") {
    return "更新 LLM token 计量";
  }
  if (latestEvent?.kind === "agent_message_sent") {
    return "发起协作";
  }
  if (latestEvent?.kind === "agent_message_received") {
    return "接收协作";
  }
  return "运行中";
}

function getLatestToolEvent(task, entries) {
  for (let index = entries.length - 1; index >= 0; index -= 1) {
    const item = entries[index];
    if (item.taskId === task.id && (item.event?.kind === "tool_result" || item.event?.kind === "tool_invocation")) {
      return item.event;
    }
  }
  return null;
}

function buildCollaborationStatus(event, taskRole = "") {
  if (!event) {
    return {
      headline: "当前尚未发生 agent 间协作。",
      detail: "等待本轮协作消息。",
      fullContent: "",
    };
  }
  const direction = event.kind === "agent_message_received" ? "received" : "sent";
  const descriptor = buildCoordinationDescriptor(event, direction, taskRole);
  return {
    headline: descriptor.shortHeadline,
    detail: descriptor.summaryLines[0] || descriptor.topicText || "等待更多协作内容。",
    fullContent: descriptor.fullContent,
  };
}

function buildAgentCard(task, sessionEntries) {
  const latestEvent = getLatestTaskEvent(task, sessionEntries);
  const latestToolEvent = getLatestToolEvent(task, sessionEntries);
  const progress = getDisplayedTaskProgress(task, sessionEntries);
  const finished = getTaskFinishedSteps(task, sessionEntries);
  const total = getTaskTotalSteps(task, sessionEntries);
  const taskEvents = sessionEntries.filter((entry) => entry.taskId === task.id);
  const collaborationEvents = taskEvents.filter((entry) => (
    entry.event?.kind === "agent_message_sent" || entry.event?.kind === "agent_message_received"
  ));
  const collaborationStatus = buildCollaborationStatus(
    collaborationEvents.length ? collaborationEvents[collaborationEvents.length - 1].event : null,
    task.role,
  );
  const expectedEvidence = (task.expected_evidence || []).slice(0, 3);
  const plannedSteps = getTaskPlannedSteps(task);
  const currentTool = latestToolEvent?.payload?.command_key || latestToolEvent?.payload?.tool_id || "";
  const currentToolStatus = latestToolEvent?.payload?.status ? labelForStatus(latestToolEvent.payload.status) : "";
  const collabPanelKey = `agent-collab:${task.id}`;
  const tokenUsage = getTaskTokenUsage(task);
  const reusedTools = Array.isArray(task.reused_tool_ids) ? task.reused_tool_ids.slice(0, 4) : [];

  return `
    <article class="agent-card">
      <div class="agent-card-head">
        <div>
          <p class="agent-card-title">${escapeHtml(labelForRole(task.role))}</p>
          <p class="agent-card-meta">第 ${escapeHtml(task.round_index || 1)} 轮 · ${escapeHtml(resolveTaskStage(task, latestEvent))}</p>
        </div>
        <span class="status-pill status-${escapeHtml(task.status)}">${escapeHtml(labelForStatus(task.status))}</span>
      </div>
      <div class="agent-progress-head">
        <span>当前进度</span>
        <strong>${finished}/${total}</strong>
      </div>
      <div class="project-progress-track">
        <span class="project-progress-fill status-${escapeHtml(task.status)}" style="width:${progress}%"></span>
      </div>
      <div class="agent-status-strip">
        <span>${escapeHtml(task.manager_review_summary || task.stage_goal || "明确 exploit stage 边界")}</span>
        <strong>${currentTool ? `${escapeHtml(currentTool)} ${escapeHtml(currentToolStatus)}` : (task.manager_completion_confirmed ? "Manager 已确认完成" : "等待工具结果")}</strong>
      </div>
      <p class="agent-objective">${escapeHtml(truncateText(task.objective || "", 140))}</p>
      <p class="agent-copy">${escapeHtml(latestEvent ? describeEventMessage(latestEvent, task.role) : "子代理正在准备执行当前任务。")}</p>
      <div class="agent-evidence-tags">
        <span>Token ${escapeHtml(formatTokenCount(tokenUsage.total_tokens))}</span>
        <span>调用 ${escapeHtml(formatTokenCount(tokenUsage.llm_calls))}</span>
        <span>${escapeHtml(formatTokenBreakdown(tokenUsage))}</span>
      </div>
      ${reusedTools.length ? `
        <div class="agent-evidence-tags">
          ${reusedTools.map((item) => `<span>复用 ${escapeHtml(item)}</span>`).join("")}
        </div>
      ` : ""}
      ${plannedSteps.length ? `
        <div class="agent-evidence-tags">
          ${plannedSteps.slice(0, 4).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
        </div>
      ` : ""}
      ${expectedEvidence.length ? `
        <div class="agent-evidence-tags">
          ${expectedEvidence.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
        </div>
      ` : ""}
      <details class="agent-collab-note" data-panel-key="${escapeHtml(collabPanelKey)}" ${getPanelOpenAttr(collabPanelKey, false)}>
        <summary>
          <span>协作状态</span>
          <strong>${escapeHtml(collaborationStatus.headline)}</strong>
        </summary>
        <div class="agent-collab-body">
          <p class="agent-collab-copy">${renderInlineStructuredText(collaborationStatus.detail)}</p>
          ${collaborationStatus.fullContent ? `
            <div class="agent-collab-rich rich-text">
              ${renderStructuredText(collaborationStatus.fullContent)}
            </div>
          ` : ""}
        </div>
      </details>
    </article>
  `;
}

function buildStreamEntryKey(entry) {
  const event = entry?.event || {};
  return [
    entry?.taskId || "",
    event.created_at || "",
    event.kind || "",
    event.agent_id || "",
    event.message || "",
  ].join("|");
}

function buildStreamItemDescriptor(entry, variant = "timeline") {
  const event = entry.event || {};
  const roleLabel = entry.taskRole && entry.taskRole !== "manager"
    ? agentNameForRole(entry.taskRole)
    : agentNameForRole("manager");
  const kindLabel = labelForEventKind(event.kind);
  const description = describeEventMessage(event, entry.taskRole);
  const accent = event.kind === "agent_message_sent" || event.kind === "agent_message_received"
    ? "coordination"
    : (event.kind === "tool_result" || event.kind === "tool_invocation" ? "tool" : "reasoning");
  const coordination = accent === "coordination"
    ? buildCoordinationDescriptor(
      event,
      event.kind === "agent_message_received" ? "received" : "sent",
      entry.taskRole,
    )
    : null;
  return {
    key: buildStreamEntryKey(entry),
    accent,
    variant,
    roleLabel,
    kindLabel,
    createdAt: formatTime(event.created_at),
    description,
    coordination,
  };
}

function renderStreamBodyInnerHtml(item) {
  const metaHtml = `
    <div class="stream-meta">
      <span class="stream-role">${escapeHtml(item.roleLabel)}</span>
      <span class="stream-kind">${escapeHtml(item.kindLabel)}</span>
      <span class="stream-time">${escapeHtml(item.createdAt)}</span>
    </div>
  `;

  if (item.coordination) {
    const detailKey = `coordination-entry:${item.key}`;
    return `
      ${metaHtml}
      <p class="stream-copy stream-copy-primary">${escapeHtml(item.coordination.headline)}</p>
      ${item.coordination.topicText ? `<p class="stream-subcopy"><span>主题</span><strong>${escapeHtml(item.coordination.topicText)}</strong></p>` : ""}
      ${item.coordination.summaryLines.length ? `
        <div class="stream-summary-lines">
          ${item.coordination.summaryLines.map((line) => `<p>${renderInlineStructuredText(line)}</p>`).join("")}
        </div>
      ` : ""}
      ${item.coordination.fullContent ? `
        <details class="stream-content-details" data-panel-key="${escapeHtml(detailKey)}" ${getPanelOpenAttr(detailKey, false)}>
          <summary>${isPanelExpanded(detailKey, false) ? "收起完整协作正文" : "展开完整协作正文"}</summary>
          <div class="stream-detail-body rich-text">
            ${renderStructuredText(item.coordination.fullContent)}
          </div>
        </details>
      ` : ""}
    `;
  }

  return `
    ${metaHtml}
    <p class="stream-copy">${escapeHtml(item.description)}</p>
  `;
}

function createStreamItemNode(item) {
  const node = document.createElement("article");
  node.className = `stream-item stream-item-${item.variant} stream-item-enter`;
  node.dataset.accent = item.accent;
  node.dataset.streamKey = item.key;
  node.innerHTML = `
    <div class="stream-rail">
      <span class="stream-dot"></span>
    </div>
    <div class="stream-body">${renderStreamBodyInnerHtml(item)}</div>
  `;
  window.requestAnimationFrame(() => {
    node.classList.remove("stream-item-enter");
  });
  return node;
}

function patchStreamItemNode(node, item) {
  const bodyNode = node.querySelector(".stream-body");
  node.className = `stream-item stream-item-${item.variant}`;
  node.dataset.accent = item.accent;
  node.dataset.streamKey = item.key;
  if (bodyNode) {
    rememberExpandedPanels(bodyNode);
    bodyNode.innerHTML = renderStreamBodyInnerHtml(item);
  }
}

function buildActivityStream(entries, emptyTitle, emptyMessage, variant = "timeline") {
  if (!entries.length) {
    return buildEmptyBlock(emptyTitle, emptyMessage);
  }

  const streamItems = entries
    .slice()
    .reverse()
    .slice(0, 36)
    .map((entry) => {
      const item = buildStreamItemDescriptor(entry, variant);
      return `
        <article class="stream-item stream-item-${variant}" data-accent="${escapeHtml(item.accent)}" data-stream-key="${escapeHtml(item.key)}">
          <div class="stream-rail">
            <span class="stream-dot"></span>
          </div>
          <div class="stream-body">
            <div class="stream-meta">
              <span class="stream-role">${escapeHtml(item.roleLabel)}</span>
              <span class="stream-kind">${escapeHtml(item.kindLabel)}</span>
              <span class="stream-time">${escapeHtml(item.createdAt)}</span>
            </div>
            <p class="stream-copy">${escapeHtml(item.description)}</p>
          </div>
        </article>
      `;
    })
    .join("");

  return `
    <div class="stream-panel stream-panel-${variant}">
      <div class="stream-list">
        ${streamItems}
      </div>
    </div>
  `;
}

function renderActivityStreamIncremental(container, entries, emptyTitle, emptyMessage, variant = "timeline", contextKey = "") {
  rememberExpandedPanels(container);
  const items = entries
    .slice()
    .reverse()
    .slice(0, 36)
    .map((entry) => buildStreamItemDescriptor(entry, variant));
  const signature = items.map((item) => item.key).join("||");
  const stateKey = `${contextKey}|${variant}`;

  if (!items.length) {
    const emptySignature = `empty|${stateKey}|${emptyTitle}|${emptyMessage}`;
    if (container.dataset.streamSignature !== emptySignature) {
      container.innerHTML = buildEmptyBlock(emptyTitle, emptyMessage);
      container.dataset.streamSignature = emptySignature;
      container.dataset.streamContextKey = stateKey;
    }
    return;
  }

  let panel = container.querySelector(".stream-panel");
  let list = panel?.querySelector(".stream-list");
  const contextChanged = container.dataset.streamContextKey !== stateKey;

  if (!panel || !list || contextChanged) {
    container.innerHTML = `
      <div class="stream-panel stream-panel-${variant}">
        <div class="stream-list"></div>
      </div>
    `;
    panel = container.querySelector(".stream-panel");
    list = panel?.querySelector(".stream-list");
    container.dataset.streamContextKey = stateKey;
    container.dataset.streamSignature = "";
  }

  if (!panel || !list) {
    return;
  }
  if (!contextChanged && container.dataset.streamSignature === signature) {
    return;
  }

  const previousScrollTop = panel.scrollTop;
  const previousScrollHeight = panel.scrollHeight;
  const keepPinnedToTop = contextChanged || previousScrollTop <= 24;
  const nextKeys = new Set(items.map((item) => item.key));
  const existingNodes = new Map(
    Array.from(list.children)
      .filter((node) => node instanceof HTMLElement)
      .map((node) => [node.dataset.streamKey || "", node])
  );

  items.forEach((item, index) => {
    let node = existingNodes.get(item.key);
    if (!node) {
      node = createStreamItemNode(item);
    } else {
      patchStreamItemNode(node, item);
    }
    const currentNode = list.children[index];
    if (currentNode !== node) {
      list.insertBefore(node, currentNode || null);
    }
  });

  Array.from(list.children).forEach((node) => {
    if (!(node instanceof HTMLElement)) {
      return;
    }
    const key = node.dataset.streamKey || "";
    if (!nextKeys.has(key)) {
      node.remove();
    }
  });

  container.dataset.streamSignature = signature;
  container.dataset.streamContextKey = stateKey;

  const restoreScroll = () => {
    if (keepPinnedToTop) {
      panel.scrollTop = 0;
      return;
    }
    const nextScrollHeight = panel.scrollHeight;
    const delta = nextScrollHeight - previousScrollHeight;
    panel.scrollTop = Math.max(0, previousScrollTop + delta);
  };
  window.requestAnimationFrame(restoreScroll);
}

function renderExpandableStreamPanel(
  container,
  {
    panelKey,
    title,
    hintCollapsed = "默认收起",
    hintExpanded = "点击收起",
    entries,
    emptyTitle,
    emptyMessage,
    variant = "timeline",
    contextKey = "",
    defaultOpen = false,
  }
) {
  rememberExpandedPanels(container);
  const openAttr = getPanelOpenAttr(panelKey, defaultOpen);
  const hint = isPanelExpanded(panelKey, defaultOpen) ? hintExpanded : hintCollapsed;
  container.innerHTML = `
    <details class="stream-details" data-panel-key="${escapeHtml(panelKey)}" ${openAttr}>
      <summary>
        <span>${escapeHtml(title)}</span>
        <span class="stream-details-hint">${escapeHtml(hint)}</span>
      </summary>
      <div class="stream-details-body"></div>
    </details>
  `;
  const body = container.querySelector(".stream-details-body");
  if (!body) {
    return;
  }
  renderActivityStreamIncremental(body, entries, emptyTitle, emptyMessage, variant, contextKey);
}

function renderTaskManagementView() {
  const session = ensureSelectedSession();
  if (!session) {
    elements.taskManagementSummary.innerHTML = buildEmptyBlock("未选择项目", "请先在“审计项目”中选择一个项目。");
    elements.taskAgentBoard.innerHTML = buildEmptyBlock("暂无子代理进度", "选定项目后会在这里展示子代理当前进度。");
    elements.agentLogList.innerHTML = buildEmptyBlock("暂无通信日志", "选定项目后会显示 agent 之间的互相交流日志。");
    elements.progressLogList.innerHTML = buildEmptyBlock("暂无进度时间线", "选定项目后会显示工具执行和推理阶段时间线。");
    return;
  }
  if (session._compact) {
    void ensureDetailedSession(session.id);
    elements.taskManagementSummary.innerHTML = buildEmptyBlock("正在加载项目详情", "已完成项目列表加载，正在补充当前项目的完整规划、事件流与进度数据。");
    elements.taskAgentBoard.innerHTML = buildEmptyBlock("正在加载子代理工作台", "子代理当前任务进度与协作状态即将展示。");
    elements.agentLogList.innerHTML = buildEmptyBlock("正在加载通信日志", "agent 间消息流正在同步。");
    elements.progressLogList.innerHTML = buildEmptyBlock("正在加载进度时间线", "工具执行与推理阶段事件正在同步。");
    return;
  }

  const entries = flattenSessionEntries(session);
  const activeRound = getLatestRoundIndex(session);
  const roundTasks = getRoundTasks(session, activeRound);
  const roundEntries = filterEntriesForRound(entries, session, activeRound);
  const derived = deriveSessionMetrics(session);
  const progress = getDisplayedSessionProgress(session, roundEntries);
  const roundPlanTotal = roundTasks.reduce((sum, task) => sum + getTaskTotalSteps(task, roundEntries), 0);
  const roundPlanCompleted = roundTasks.reduce((sum, task) => sum + getTaskFinishedSteps(task, roundEntries), 0);
  const sessionTokenUsage = getSessionTokenUsage(session);
  const managerTokenUsage = normalizeTokenUsage(session.manager_token_usage);
  const communicationEntries = roundEntries.filter((entry) => (
    entry.event?.kind === "agent_message_sent" || entry.event?.kind === "agent_message_received"
  ));
  const progressEntries = roundEntries.filter((entry) => (
    entry.event?.kind === "tool_invocation"
    || entry.event?.kind === "tool_result"
    || entry.event?.kind === "llm_usage_recorded"
    || entry.event?.kind === "reasoning_round"
    || entry.event?.kind === "subagent_completed"
    || entry.event?.kind === "subagent_started"
    || entry.event?.kind === "session_completed"
    || entry.event?.kind === "session_failed"
  ));

  rememberExpandedPanels(elements.taskManagementSummary);
  elements.taskManagementSummary.innerHTML = `
    <article class="summary-card">
      <div class="section-heading">
        <div>
          <p class="section-kicker">当前项目</p>
          <h3>${escapeHtml(session.request.title)}</h3>
        </div>
        <span class="status-pill status-${escapeHtml(session.status)}">${escapeHtml(labelForStatus(session.status))}</span>
      </div>

      <div class="detail-grid">
        <div class="meta-card">
          <span>样本文件</span>
          <strong>${escapeHtml(getTargetFileName(session))}</strong>
        </div>
        <div class="meta-card">
          <span>最近更新时间</span>
          <strong>${escapeHtml(formatTime(session.updated_at))}</strong>
        </div>
        <div class="meta-card">
          <span>问题总数</span>
          <strong>${derived.total}</strong>
        </div>
        <div class="meta-card">
          <span>当前轮次</span>
          <strong>第 ${activeRound} 轮</strong>
        </div>
        <div class="meta-card">
          <span>本轮计划步数</span>
          <strong>${roundPlanCompleted}/${roundPlanTotal || 0}</strong>
        </div>
        <div class="meta-card">
          <span>累计 Token</span>
          <strong>${formatTokenCount(sessionTokenUsage.total_tokens)}</strong>
        </div>
        <div class="meta-card">
          <span>Manager Token</span>
          <strong>${formatTokenCount(managerTokenUsage.total_tokens)}</strong>
        </div>
        <div class="meta-card">
          <span>共享记忆条数</span>
          <strong>${formatTokenCount((session.shared_memory || []).length)}</strong>
        </div>
      </div>

      <div class="project-progress-panel">
        <div class="project-progress-head">
          <span>整体执行进度</span>
          <strong>${progress}%</strong>
        </div>
        <div class="project-progress-track">
          <span class="project-progress-fill status-${escapeHtml(session.status)}" style="width:${progress}%"></span>
        </div>
      </div>

      <div class="severity-line">
        ${buildSeverityChip("high", derived.counts.high)}
        ${buildSeverityChip("medium", derived.counts.medium)}
        ${buildSeverityChip("low", derived.counts.low)}
      </div>

      ${buildManagerPlanPanel(session)}
      ${buildSharedMemoryPanel(session)}

      <div class="project-actions">
        <button class="button button-primary" type="button" data-switch-view="reports">转到报告生成</button>
        <button class="button button-secondary" type="button" data-export-session="${escapeHtml(session.id)}" data-export-format="markdown">
          导出 Markdown
        </button>
        <button class="button button-danger" type="button" data-delete-session="${escapeHtml(session.id)}">
          删除任务
        </button>
      </div>
    </article>
  `;

  rememberExpandedPanels(elements.taskAgentBoard);
  elements.taskAgentBoard.innerHTML = roundTasks.length
    ? roundTasks.map((task) => buildAgentCard(task, roundEntries)).join("")
    : buildEmptyBlock("暂无子代理", "当前项目尚未分配子代理。");
  renderExpandableStreamPanel(
    elements.agentLogList,
    {
      panelKey: `agent-log:${session.id}:round:${activeRound}`,
      title: "Agent 互相交流记录",
      entries: communicationEntries,
      emptyTitle: "暂无通信日志",
      emptyMessage: "当前项目尚未发生 agent 之间的协作消息。",
      variant: "coordination",
      contextKey: `${session.id}|round:${activeRound}|coordination`,
      defaultOpen: false,
    }
  );
  renderActivityStreamIncremental(
    elements.progressLogList,
    progressEntries,
    "暂无进度时间线",
    "当前项目尚未产生可展示的进度事件。",
    "timeline",
    `${session.id}|round:${activeRound}|timeline`
  );
}

function renderReportsView() {
  const session = ensureSelectedSession();
  if (!session) {
    elements.reportSessionSummary.innerHTML = buildEmptyBlock("未选择项目", "请选择一个审计项目后再查看报告。");
    elements.reportPreview.innerHTML = buildEmptyBlock("暂无报告内容", "选定项目后会在这里展示最终报告。");
    return;
  }
  if (session._compact) {
    void ensureDetailedSession(session.id);
    elements.reportSessionSummary.innerHTML = buildEmptyBlock("正在加载完整报告", "已完成项目列表加载，正在补充当前项目的函数级报告与动态调试结论。");
    elements.reportPreview.innerHTML = buildEmptyBlock("报告同步中", "最终报告、PoC 和代码块内容正在同步。");
    return;
  }

  const derived = deriveSessionMetrics(session);
  elements.reportSessionSummary.innerHTML = `
    <article class="summary-card">
      <div class="section-heading">
        <div>
          <p class="section-kicker">当前报告</p>
          <h3>${escapeHtml(session.request.title)}</h3>
        </div>
        <span class="status-pill status-${escapeHtml(session.status)}">${escapeHtml(labelForStatus(session.status))}</span>
      </div>
      <div class="detail-grid">
        <div class="meta-card">
          <span>样本文件</span>
          <strong>${escapeHtml(getTargetFileName(session))}</strong>
        </div>
        <div class="meta-card">
          <span>更新时间</span>
          <strong>${escapeHtml(formatTime(session.updated_at))}</strong>
        </div>
        <div class="meta-card">
          <span>高危 / 中危 / 低危</span>
          <strong>${derived.counts.high} / ${derived.counts.medium} / ${derived.counts.low}</strong>
        </div>
      </div>
      <div class="project-actions">
        <button class="button button-primary" type="button" data-export-session="${escapeHtml(session.id)}" data-export-format="markdown">
          导出 Markdown
        </button>
        <button class="button button-secondary" type="button" data-export-session="${escapeHtml(session.id)}" data-export-format="json">
          导出 JSON
        </button>
        <button class="button button-ghost" type="button" data-switch-view="task-management">
          返回任务管理
        </button>
        <button class="button button-danger" type="button" data-delete-session="${escapeHtml(session.id)}">
          删除任务
        </button>
      </div>
    </article>
  `;

  elements.reportPreview.innerHTML = session.final_report
    ? renderStructuredText(session.final_report)
    : buildEmptyBlock("报告生成中", "当前项目仍在执行中，最终报告会在这里展示。");
}

function renderKnowledgeView() {
  const entries = state.knowledgeEntries.map((entry) => ({
    ...entry,
    severity: classifySeverity(entry.text) || "low",
  }));
  const completedSessions = state.sessions.filter((session) => session.status === "completed").length;

  elements.knowledgeSummary.innerHTML = `
    <article class="summary-card summary-inline">
      <div class="meta-card">
        <span>已完成项目</span>
        <strong>${completedSessions}</strong>
      </div>
      <div class="meta-card">
        <span>沉淀结论</span>
        <strong>${entries.length}</strong>
      </div>
      <div class="meta-card">
        <span>覆盖角色</span>
        <strong>${new Set(entries.map((item) => item.role)).size}</strong>
      </div>
    </article>
  `;

  elements.knowledgeList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="knowledge-card">
              <div class="knowledge-card-head">
                <div class="log-card-tags">
                  ${buildSelectionControl({
                    checked: state.selectedKnowledgeEntryIds.has(entry.id),
                    target: "knowledge-entries",
                    id: entry.id,
                    label: "选中",
                  })}
                  <span class="role-chip">${escapeHtml(labelForRole(entry.role))}</span>
                  <span class="severity-chip severity-${escapeHtml(entry.severity)}">${escapeHtml(SEVERITY_META[entry.severity].label)}</span>
                </div>
                <div class="project-actions">
                  <button class="text-button" type="button" data-select-session="${escapeHtml(entry.session_id)}" data-switch-view="reports">
                    查看报告
                  </button>
                  <button class="text-button" type="button" data-delete-knowledge-entry="${escapeHtml(entry.id)}">
                    删除历史
                  </button>
                </div>
              </div>
              <p class="knowledge-title">${escapeHtml(entry.session_title)}</p>
              <p class="knowledge-copy">${escapeHtml(entry.text)}</p>
            </article>
          `
        )
        .join("")
    : buildEmptyBlock("知识库为空", "等待更多已完成审计任务后，系统会在这里沉淀历史结论。");
  elements.toggleKnowledgeSelectionButton.disabled = !entries.length;
  elements.bulkDeleteKnowledgeButton.disabled = !state.selectedKnowledgeEntryIds.size;
  elements.toggleKnowledgeSelectionButton.textContent = (
    entries.length && state.selectedKnowledgeEntryIds.size === entries.length
      ? "取消全选知识历史"
      : "全选知识历史"
  );
  elements.bulkDeleteKnowledgeButton.textContent = state.selectedKnowledgeEntryIds.size
    ? `批量删除历史 (${state.selectedKnowledgeEntryIds.size})`
    : "批量删除历史";
}

function renderSystemStatus() {
  const running = state.sessions.filter((session) => session.status === "running").length;
  const completed = state.sessions.filter((session) => session.status === "completed").length;
  const runtime = state.runtimeProfile || {};
  const deepseek = state.deepseekSettings || {};
  const disabledTools = Array.isArray(runtime.disabled_tool_ids) ? runtime.disabled_tool_ids.length : 0;
  const auditReady = runtime.llm_status === "ready";
  const globalTokenUsage = state.sessions.reduce(
    (acc, session) => addTokenUsage(acc, getSessionTokenUsage(session)),
    normalizeTokenUsage({})
  );
  const cards = [
    {
      label: "实时同步",
      value: state.wsConnected ? "WebSocket 已连接" : (state.autoRefresh ? "轮询同步中" : "等待手动刷新"),
    },
    {
      label: "审计后端",
      value: auditReady ? "已就绪" : "未就绪",
    },
    {
      label: "API Key 状态",
      value: deepseek.configured ? "已配置" : "未配置",
    },
    {
      label: "Docker 子代理",
      value: runtime.docker_runtime ? "已启用" : "未启用",
    },
    {
      label: "自动轮询",
      value: state.autoRefresh ? "已开启" : "已关闭",
    },
    {
      label: "审计项目数",
      value: `${state.sessions.length} 个`,
    },
    {
      label: "审计中任务",
      value: `${running} 个`,
    },
    {
      label: "已完成任务",
      value: `${completed} 个`,
    },
    {
      label: "累计 Token",
      value: formatTokenCount(globalTokenUsage.total_tokens),
    },
    {
      label: "模型路由",
      value: runtime.subagent_model_policy === "auto-by-phase" ? "按阶段自动决策" : "按运行时策略决定",
    },
    {
      label: "Manager 续轮",
      value: runtime.manager_round_policy === "result_driven" ? "按每轮复核结果决定" : "按运行时策略决定",
    },
    {
      label: "Token 计量",
      value: runtime.token_tracking === "live-per-call" ? "实时累计中" : "按快照统计",
    },
    {
      label: "已关闭工具",
      value: `${disabledTools} 个`,
    },
  ];

  elements.systemStatusGrid.innerHTML = cards
    .map(
      (card) => `
        <article class="meta-card meta-card-emphasis">
          <span>${escapeHtml(card.label)}</span>
          <strong>${escapeHtml(card.value)}</strong>
        </article>
      `
    )
    .join("");
}

function renderDeepSeekSettings() {
  const settings = state.deepseekSettings;
  if (!settings) {
    elements.settingsApiKeyHint.textContent = "正在读取当前 API Key 配置。";
  } else if (settings.configured) {
    elements.settingsApiKeyHint.textContent = `当前已配置 API Key：${settings.key_preview || "已隐藏"}`;
  } else {
    elements.settingsApiKeyHint.textContent = "当前未配置 API Key。";
  }

  const result = state.apiCheckResult;
  if (!result) {
    elements.apiCheckStatus.innerHTML = buildEmptyBlock("尚未检测", "保存 API Key 后可直接检测当前 DeepSeek API 是否可用。");
    return;
  }

  const statusClass = result.available ? "status-ok" : "status-error";
  const summary = result.available
    ? "已成功完成一次最小真实 DeepSeek 请求。"
    : (result.error || "当前请求未通过。");

  elements.apiCheckStatus.innerHTML = `
    <article class="api-status-card ${statusClass}">
      <span class="section-kicker">API 可用性</span>
      <strong>${escapeHtml(result.available ? "可用" : "不可用")}</strong>
      <p>${escapeHtml(summary)}</p>
    </article>
    <article class="api-status-card">
      <span class="section-kicker">检测模型</span>
      <strong>${escapeHtml(result.model || "--")}</strong>
      <p>${escapeHtml(formatTime(result.checked_at))}</p>
    </article>
  `;
}

function renderToolCapabilities() {
  if (!state.toolCapabilities.length) {
    elements.toolGrid.innerHTML = buildEmptyBlock("暂无工具能力", "等待后端返回当前可调用工具和可用状态。");
    return;
  }
  elements.toolGrid.innerHTML = state.toolCapabilities
    .map(
      (tool) => `
        <article class="tool-card ${tool.available ? "" : "is-unavailable"} ${tool.enabled ? "" : "is-disabled"}">
          <div class="tool-card-head">
            <div>
              <strong class="mono">${escapeHtml(tool.tool_id)}</strong>
              <p class="tool-card-copy">${escapeHtml(tool.summary)}</p>
            </div>
            <div class="tool-card-statuses">
              <span class="status-pill status-${tool.available ? "completed" : "failed"}">${tool.available ? "可用" : "不可用"}</span>
              <span class="status-pill status-${tool.enabled ? "running" : "skipped"}">${tool.enabled ? "已启用" : "已关闭"}</span>
            </div>
          </div>
          <div class="tool-card-actions">
            <button
              class="button ${tool.enabled ? "button-danger" : "button-secondary"}"
              type="button"
              data-toggle-tool="${escapeHtml(tool.tool_id)}"
              data-toggle-enabled="${tool.enabled ? "false" : "true"}"
            >
              ${tool.enabled ? "关闭工具" : "启用工具"}
            </button>
          </div>
        </article>
      `
    )
    .join("");
}

function renderAll() {
  pruneSelections();
  ensureSelectedSession();
  setView(state.currentView, { animate: false });
  renderHomeView();
  renderProjectsView();
  renderTaskManagementView();
  renderReportsView();
  renderKnowledgeView();
  renderSystemStatus();
  renderDeepSeekSettings();
  renderToolCapabilities();
}

async function loadSessions({ keepSelection = true } = {}) {
  const sessions = await requestJson(`${apiPrefix}/audits?compact=true`);
  const existingById = new Map(state.sessions.map((session) => [session.id, session]));
  state.sessions = sessions.map((session) => {
    session._compact = true;
    const existing = existingById.get(session.id);
    if (existing && existing._compact === false) {
      return existing;
    }
    return session;
  });
  sortSessions();
  pruneSelections();

  if (!keepSelection && sessions.length && !state.selectionCleared) {
    state.selectedSessionId = sessions[0].id;
  }

  if (state.selectedSessionId && !getSelectedSession()) {
    state.selectedSessionId = null;
  }
  renderAll();
}

async function loadSession(sessionId) {
  const session = await requestJson(`${apiPrefix}/audits/${sessionId}`);
  session._compact = false;
  upsertSession(session);
  state.selectionCleared = false;
  state.selectedSessionId = session.id;
  renderAll();
}

async function ensureDetailedSession(sessionId) {
  const session = state.sessions.find((item) => item.id === sessionId);
  if (!session || session._compact === false || state.loadingSessionIds.has(sessionId)) {
    return;
  }
  state.loadingSessionIds.add(sessionId);
  try {
    await loadSession(sessionId);
  } finally {
    state.loadingSessionIds.delete(sessionId);
  }
}

async function loadToolCapabilities() {
  state.toolCapabilities = await requestJson(`${apiPrefix}/tools`);
  renderToolCapabilities();
}

async function loadRuntimeProfile() {
  state.runtimeProfile = await requestJson(`${apiPrefix}/runtime`);
  renderSystemStatus();
}

function isAuditRuntimeReady(runtime = state.runtimeProfile) {
  return runtime?.llm_status === "ready";
}

async function ensureAuditRuntimeReady() {
  await loadRuntimeProfile();
  if (isAuditRuntimeReady()) {
    return true;
  }
  const detail = state.runtimeProfile?.llm_error || "当前未配置可用的 DeepSeek API Key。";
  closeCreateTaskModal();
  await notify(`当前无法创建审计任务：${detail}`, "审计后端未就绪");
  setView("settings");
  return false;
}

async function loadKnowledgeEntries({ render = true } = {}) {
  state.knowledgeEntries = await requestJson(`${apiPrefix}/knowledge`);
  state.knowledgeLoadedAt = Date.now();
  state.knowledgeDirty = false;
  pruneSelections();
  if (render) {
    renderKnowledgeView();
  }
}

async function ensureKnowledgeEntries({ force = false, maxAgeMs = 15000 } = {}) {
  const shouldReload = (
    force
    || state.knowledgeDirty
    || !state.knowledgeLoadedAt
    || (Date.now() - state.knowledgeLoadedAt) > maxAgeMs
  );
  if (!shouldReload) {
    return;
  }
  await loadKnowledgeEntries({ render: state.currentView === "knowledge" });
}

async function loadDeepSeekSettings() {
  state.deepseekSettings = await requestJson(`${apiPrefix}/settings/deepseek`);
  renderDeepSeekSettings();
  renderSystemStatus();
}

function openCreateTaskModal() {
  elements.createTaskModal.hidden = false;
  syncModalBodyLock();
}

function closeCreateTaskModal() {
  elements.createTaskModal.hidden = true;
  syncModalBodyLock();
}

function resetCreateTaskForm() {
  elements.createTaskForm.reset();
  elements.taskTitle.value = DEFAULT_TASK_FORM.title;
  elements.taskObjective.value = DEFAULT_TASK_FORM.objective;
  elements.taskDifficulty.value = DEFAULT_TASK_FORM.difficulty;
  elements.taskMaxSubagents.value = DEFAULT_TASK_FORM.maxSubagents;
  elements.taskTags.value = DEFAULT_TASK_FORM.tags;
  elements.taskFileMeta.textContent = "请选择待审计的二进制样本文件。";
}

function updateTaskFileMeta() {
  const file = elements.taskFileInput.files?.[0];
  if (!file) {
    elements.taskFileMeta.textContent = "请选择待审计的二进制样本文件。";
    return;
  }
  const currentTitle = elements.taskTitle.value.trim();
  if (!currentTitle || currentTitle === "样本初始审计") {
    elements.taskTitle.value = `${file.name} 深度审计`;
  }
  elements.taskFileMeta.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
}

async function uploadArtifact(file) {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson(`${apiPrefix}/artifacts`, {
    method: "POST",
    body: formData,
  });
}

function parseCsv(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

async function handleCreateTask(event) {
  event.preventDefault();
  const file = elements.taskFileInput.files?.[0];
  if (!file) {
    notify("请先上传任务文件。", "缺少样本");
    return;
  }

  elements.createTaskSubmitButton.disabled = true;
  elements.createTaskSubmitButton.textContent = "检查环境...";

  try {
    const runtimeReady = await ensureAuditRuntimeReady();
    if (!runtimeReady) {
      return;
    }

    elements.createTaskSubmitButton.textContent = "上传并创建中...";
    const artifact = await uploadArtifact(file);
    const normalizedTitle = elements.taskTitle.value.trim() || `${file.name} 深度审计`;
    const payload = {
      title: normalizedTitle,
      objective: elements.taskObjective.value.trim(),
      artifact_id: artifact.id,
      difficulty: elements.taskDifficulty.value,
      max_subagents: Number(elements.taskMaxSubagents.value || 3),
      tags: parseCsv(elements.taskTags.value),
    };

    const session = await requestJson(`${apiPrefix}/audits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    upsertSession(session);
    state.selectionCleared = false;
    state.selectedSessionId = session.id;
    state.liveEventsBySession[session.id] = [];
    closeCreateTaskModal();
    resetCreateTaskForm();
    setView("task-management");
    await loadSession(session.id);
  } catch (error) {
    notify(`创建审计任务失败: ${error.message}`, "创建失败");
  } finally {
    elements.createTaskSubmitButton.disabled = false;
    elements.createTaskSubmitButton.textContent = "上传并创建";
  }
}

function removeSessionsLocally(sessionIds) {
  const deletedIds = new Set(sessionIds);
  state.sessions = state.sessions.filter((item) => !deletedIds.has(item.id));
  for (const sessionId of deletedIds) {
    delete state.liveEventsBySession[sessionId];
  }
  state.knowledgeEntries = state.knowledgeEntries.filter((entry) => !deletedIds.has(entry.session_id));
  state.selectedProjectSessionIds = new Set(
    [...state.selectedProjectSessionIds].filter((sessionId) => !deletedIds.has(sessionId))
  );
  state.selectedCompletedSessionIds = new Set(
    [...state.selectedCompletedSessionIds].filter((sessionId) => !deletedIds.has(sessionId))
  );
  if (state.selectedSessionId && deletedIds.has(state.selectedSessionId)) {
    state.selectedSessionId = null;
    state.selectionCleared = false;
  }
  state.knowledgeDirty = true;
}

function removeKnowledgeEntriesLocally(entryIds) {
  const deletedIds = new Set(entryIds);
  state.knowledgeEntries = state.knowledgeEntries.filter((entry) => !deletedIds.has(entry.id));
  state.selectedKnowledgeEntryIds = new Set(
    [...state.selectedKnowledgeEntryIds].filter((entryId) => !deletedIds.has(entryId))
  );
  state.knowledgeLoadedAt = Date.now();
}

async function deleteSessionsByIds(sessionIds, title, message) {
  if (!sessionIds.length) {
    return;
  }
  const confirmed = await confirmAction(message, title, sessionIds.length > 1 ? "批量删除" : "确认删除");
  if (!confirmed) {
    return;
  }

  try {
    const failedIds = [];
    for (const sessionId of sessionIds) {
      try {
        await requestJson(`${apiPrefix}/audits/${sessionId}`, { method: "DELETE" });
      } catch (error) {
        failedIds.push({ sessionId, error });
      }
    }
    const succeededIds = sessionIds.filter((sessionId) => !failedIds.some((item) => item.sessionId === sessionId));
    if (succeededIds.length) {
      removeSessionsLocally(succeededIds);
      renderAll();
      await loadSessions({ keepSelection: false });
    }
    if (failedIds.length) {
      notify(`以下任务删除失败：${failedIds.map((item) => item.sessionId).join("、")}`, "批量删除部分失败");
      return;
    }
    if (sessionIds.length > 1) {
      notify(`已删除 ${sessionIds.length} 个任务。`, "批量删除完成");
    }
  } catch (error) {
    notify(`删除任务失败: ${error.message}`, "删除失败");
  }
}

async function handleDeleteSession(sessionId) {
  const session = state.sessions.find((item) => item.id === sessionId) || null;
  const title = session?.request?.title || sessionId;
  return deleteSessionsByIds(
    [sessionId],
    "确认删除任务",
    `确认删除任务“${title}”吗？这会清理会话记录、运行目录和关联知识库条目。`
  );
}

async function handleBulkDeleteSelectedProjects() {
  const sessionIds = [...state.selectedProjectSessionIds];
  return deleteSessionsByIds(
    sessionIds,
    "批量删除任务",
    `确认批量删除选中的 ${sessionIds.length} 个任务吗？运行中的任务也会被停止并清理。`
  );
}

async function handleBulkDeleteCompletedSessions() {
  const sessionIds = [...state.selectedCompletedSessionIds];
  return deleteSessionsByIds(
    sessionIds,
    "批量删除历史任务",
    `确认批量删除选中的 ${sessionIds.length} 个已完成任务吗？对应知识库条目也会一起清理。`
  );
}

async function deleteKnowledgeEntriesByIds(entryIds, title, message) {
  if (!entryIds.length) {
    return;
  }
  const confirmed = await confirmAction(message, title, entryIds.length > 1 ? "批量删除" : "确认删除");
  if (!confirmed) {
    return;
  }
  try {
    const failedIds = [];
    for (const entryId of entryIds) {
      try {
        await requestJson(`${apiPrefix}/knowledge/${entryId}`, { method: "DELETE" });
      } catch (error) {
        failedIds.push({ entryId, error });
      }
    }
    const succeededIds = entryIds.filter((entryId) => !failedIds.some((item) => item.entryId === entryId));
    if (succeededIds.length) {
      removeKnowledgeEntriesLocally(succeededIds);
      renderKnowledgeView();
    }
    if (failedIds.length) {
      notify(`以下知识库历史删除失败：${failedIds.map((item) => item.entryId).join("、")}`, "批量删除部分失败");
      return;
    }
    if (entryIds.length > 1) {
      notify(`已删除 ${entryIds.length} 条知识库历史。`, "批量删除完成");
    }
  } catch (error) {
    notify(`删除知识库历史失败: ${error.message}`, "删除失败");
  }
}

async function handleDeleteKnowledgeEntry(entryId) {
  return deleteKnowledgeEntriesByIds(
    [entryId],
    "确认删除知识历史",
    "确认删除这条知识库历史吗？删除后不会再在前端知识库中展示。"
  );
}

async function handleBulkDeleteKnowledgeEntries() {
  const entryIds = [...state.selectedKnowledgeEntryIds];
  return deleteKnowledgeEntriesByIds(
    entryIds,
    "批量删除知识历史",
    `确认批量删除选中的 ${entryIds.length} 条知识库历史吗？`
  );
}

async function handleSaveApiKey(event) {
  event.preventDefault();
  const apiKey = elements.settingsApiKeyInput.value.trim();
  elements.saveApiKeyButton.disabled = true;
  elements.saveApiKeyButton.textContent = "保存中...";

  try {
    state.deepseekSettings = await requestJson(`${apiPrefix}/settings/deepseek`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: apiKey || null }),
    });
    state.apiCheckResult = null;
    elements.settingsApiKeyInput.value = "";
    await loadRuntimeProfile();
    renderDeepSeekSettings();
    notify(apiKey ? "API Key 已保存。" : "API Key 已清除。", "设置已更新");
  } catch (error) {
    notify(`保存 API Key 失败: ${error.message}`, "保存失败");
  } finally {
    elements.saveApiKeyButton.disabled = false;
    elements.saveApiKeyButton.textContent = "保存 API Key";
  }
}

async function handleCheckApi() {
  const apiKey = elements.settingsApiKeyInput.value.trim();
  elements.checkApiButton.disabled = true;
  elements.checkApiButton.textContent = "检测中...";

  try {
    state.apiCheckResult = await requestJson(`${apiPrefix}/settings/deepseek/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: apiKey || null }),
    });
    renderDeepSeekSettings();
  } catch (error) {
    notify(`检测 API 失败: ${error.message}`, "检测失败");
  } finally {
    elements.checkApiButton.disabled = false;
    elements.checkApiButton.textContent = "检测当前 API";
  }
}

async function handleToggleTool(toolId, enabled) {
  const actionText = enabled ? "启用" : "关闭";
  if (!enabled) {
    const confirmed = await confirmAction(
      `确认关闭工具“${toolId}”吗？关闭后新的 Manager 轮次和子代理执行都不会再调度它。`,
      "确认关闭工具",
      "确认关闭"
    );
    if (!confirmed) {
      return;
    }
  }

  try {
    const updated = await requestJson(`${apiPrefix}/tools/${encodeURIComponent(toolId)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    const index = state.toolCapabilities.findIndex((tool) => tool.tool_id === toolId);
    if (index >= 0) {
      state.toolCapabilities[index] = updated;
    } else {
      state.toolCapabilities.push(updated);
    }
    await loadRuntimeProfile();
    renderToolCapabilities();
    notify(`工具 ${toolId} 已${actionText}。`, "工具设置已更新");
  } catch (error) {
    notify(`更新工具状态失败: ${error.message}`, "工具设置失败");
  }
}

function toggleSelectionBucket(target, id) {
  if (target === "project-sessions") {
    toggleSetMembership(state.selectedProjectSessionIds, id);
  } else if (target === "completed-sessions") {
    toggleSetMembership(state.selectedCompletedSessionIds, id);
  } else if (target === "knowledge-entries") {
    toggleSetMembership(state.selectedKnowledgeEntryIds, id);
  }
  renderAll();
}

function toggleAllProjectSelections() {
  if (!state.sessions.length) {
    return;
  }
  if (state.selectedProjectSessionIds.size === state.sessions.length) {
    state.selectedProjectSessionIds.clear();
  } else {
    state.selectedProjectSessionIds = new Set(state.sessions.map((session) => session.id));
  }
  renderProjectsView();
}

function toggleAllCompletedSelections() {
  const completedIds = state.sessions
    .filter((session) => session.status === "completed")
    .map((session) => session.id);
  if (!completedIds.length) {
    return;
  }
  if (state.selectedCompletedSessionIds.size === completedIds.length) {
    state.selectedCompletedSessionIds.clear();
  } else {
    state.selectedCompletedSessionIds = new Set(completedIds);
  }
  renderHomeView();
}

function toggleAllKnowledgeSelections() {
  const knowledgeIds = state.knowledgeEntries.map((entry) => entry.id);
  if (!knowledgeIds.length) {
    return;
  }
  if (state.selectedKnowledgeEntryIds.size === knowledgeIds.length) {
    state.selectedKnowledgeEntryIds.clear();
  } else {
    state.selectedKnowledgeEntryIds = new Set(knowledgeIds);
  }
  renderKnowledgeView();
}

function connectWebSocket() {
  if (state.socket && (state.socket.readyState === WebSocket.OPEN || state.socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socketUrl = `${protocol}://${window.location.host}${apiPrefix}/ws/audits`;
  state.socket = new WebSocket(socketUrl);

  state.socket.addEventListener("message", (rawEvent) => {
    const payload = JSON.parse(rawEvent.data);

    if (payload.type === "connected") {
      state.wsConnected = true;
      scheduleRender(0);
      return;
    }

    if (payload.type === "tool_inventory") {
      state.toolCapabilities = payload.tool_capabilities || [];
      renderToolCapabilities();
      return;
    }

    if (payload.type === "session_snapshot" && payload.session) {
      upsertSession(payload.session);
      if (!state.selectedSessionId && !state.selectionCleared) {
        state.selectedSessionId = payload.session.id;
      }
      if (payload.session.status === "completed" || payload.session.status === "failed") {
        state.knowledgeDirty = true;
      }
      scheduleRender(0);
      return;
    }

    if (payload.type === "audit_event" && payload.event) {
      const sessionId = payload.session_id;
      if (!state.liveEventsBySession[sessionId]) {
        state.liveEventsBySession[sessionId] = [];
      }
      state.liveEventsBySession[sessionId].push({
        taskId: payload.task_id,
        event: payload.event,
      });
      state.liveEventsBySession[sessionId] = state.liveEventsBySession[sessionId].slice(-120);
      if (payload.event.kind === "session_completed" || payload.event.kind === "session_failed") {
        state.knowledgeDirty = true;
        if (state.currentView === "knowledge") {
          void ensureKnowledgeEntries({ force: true, maxAgeMs: 0 });
        }
      }
      if (sessionId === state.selectedSessionId) {
        scheduleRender();
      }
    }
  });

  state.socket.addEventListener("close", () => {
    state.wsConnected = false;
    scheduleRender(0);
    state.socket = null;
    if (state.wsRetryTimer) {
      window.clearTimeout(state.wsRetryTimer);
    }
    state.wsRetryTimer = window.setTimeout(connectWebSocket, 2000);
  });

  state.socket.addEventListener("error", () => {
    if (state.socket) {
      state.socket.close();
    }
  });
}

function startAutoRefresh() {
  stopAutoRefresh();
  state.refreshTimer = window.setInterval(async () => {
    if (!state.autoRefresh) {
      return;
    }
    try {
      await loadSessions();
      const selected = getSelectedSession();
      if (!state.wsConnected && selected && (selected.status === "running" || selected.status === "queued")) {
        await loadSession(selected.id);
      }
    } catch (error) {
      console.error(error);
    }
  }, 3000);
}

function stopAutoRefresh() {
  if (state.refreshTimer) {
    window.clearInterval(state.refreshTimer);
    state.refreshTimer = null;
  }
}

function bindStaticEvents() {
  elements.navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setView(button.dataset.viewTarget);
    });
  });

  elements.clearSessionSelectionButton.addEventListener("click", clearSelectedSession);
  elements.openCreateTaskModalButton.addEventListener("click", openCreateTaskModal);
  elements.heroCreateTaskButton.addEventListener("click", openCreateTaskModal);
  elements.refreshProjectsButton.addEventListener("click", () => loadSessions());
  elements.toggleCompletedSelectionButton.addEventListener("click", toggleAllCompletedSelections);
  elements.bulkDeleteCompletedButton.addEventListener("click", handleBulkDeleteCompletedSessions);
  elements.toggleProjectSelectionButton.addEventListener("click", toggleAllProjectSelections);
  elements.bulkDeleteProjectsButton.addEventListener("click", handleBulkDeleteSelectedProjects);
  elements.toggleKnowledgeSelectionButton.addEventListener("click", toggleAllKnowledgeSelections);
  elements.bulkDeleteKnowledgeButton.addEventListener("click", handleBulkDeleteKnowledgeEntries);
  elements.closeCreateTaskModalButton.addEventListener("click", closeCreateTaskModal);
  elements.resetCreateTaskButton.addEventListener("click", resetCreateTaskForm);
  elements.taskFileInput.addEventListener("change", updateTaskFileMeta);
  elements.createTaskForm.addEventListener("submit", handleCreateTask);
  elements.deepseekSettingsForm.addEventListener("submit", handleSaveApiKey);
  elements.checkApiButton.addEventListener("click", handleCheckApi);
  elements.closeAppDialogButton.addEventListener("click", () => closeAppDialog(false));
  elements.appDialogCancelButton.addEventListener("click", () => closeAppDialog(false));
  elements.appDialogConfirmButton.addEventListener("click", () => closeAppDialog(true));
  document.addEventListener("toggle", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLDetailsElement)) {
      return;
    }
    const panelKey = target.dataset.panelKey;
    if (!panelKey) {
      return;
    }
    state.expandedPanels[panelKey] = target.open;
  }, true);

  document.addEventListener("click", (event) => {
    const closeTarget = event.target.closest("[data-close-modal]");
    if (closeTarget) {
      closeCreateTaskModal();
      return;
    }

    const closeDialogTarget = event.target.closest("[data-close-dialog]");
    if (closeDialogTarget) {
      closeAppDialog(false);
      return;
    }

    const selectionTarget = event.target.closest("[data-selection-target][data-selection-id]");
    if (selectionTarget) {
      toggleSelectionBucket(selectionTarget.dataset.selectionTarget, selectionTarget.dataset.selectionId);
      return;
    }

    const sessionTarget = event.target.closest("[data-select-session]");
    if (sessionTarget) {
      const sessionId = sessionTarget.dataset.selectSession;
      selectSession(sessionId);
      void ensureDetailedSession(sessionId);
      if (sessionTarget.dataset.switchView) {
        setView(sessionTarget.dataset.switchView);
      }
      return;
    }

    const viewTarget = event.target.closest("[data-switch-view]");
    if (viewTarget) {
      setView(viewTarget.dataset.switchView);
      return;
    }

    const deleteSessionTarget = event.target.closest("[data-delete-session]");
    if (deleteSessionTarget) {
      handleDeleteSession(deleteSessionTarget.dataset.deleteSession);
      return;
    }

    const deleteKnowledgeTarget = event.target.closest("[data-delete-knowledge-entry]");
    if (deleteKnowledgeTarget) {
      handleDeleteKnowledgeEntry(deleteKnowledgeTarget.dataset.deleteKnowledgeEntry);
      return;
    }

    const exportTarget = event.target.closest("[data-export-session][data-export-format]");
    if (exportTarget) {
      const sessionId = exportTarget.dataset.exportSession;
      const format = exportTarget.dataset.exportFormat;
      triggerDownload(`${apiPrefix}/audits/${sessionId}/report?format=${format}&download=true`);
      return;
    }

    const toolToggleTarget = event.target.closest("[data-toggle-tool][data-toggle-enabled]");
    if (toolToggleTarget) {
      handleToggleTool(
        toolToggleTarget.dataset.toggleTool,
        toolToggleTarget.dataset.toggleEnabled === "true"
      );
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !elements.appDialogModal.hidden) {
      closeAppDialog(false);
      return;
    }
    if (event.key === "Escape" && !elements.createTaskModal.hidden) {
      closeCreateTaskModal();
    }
  });
}

async function bootstrap() {
  bindStaticEvents();
  resetCreateTaskForm();

  await Promise.all([
    loadSessions({ keepSelection: false }),
    loadToolCapabilities(),
    loadRuntimeProfile(),
    loadDeepSeekSettings(),
    loadKnowledgeEntries({ render: false }),
  ]);

  connectWebSocket();
  startAutoRefresh();
}

bootstrap().catch((error) => {
  console.error(error);
  notify(`前端初始化失败: ${error.message}`, "初始化失败");
});
