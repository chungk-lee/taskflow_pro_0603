// 칸반: 3컬럼 + 필터 + 인라인 생성 + 드래그 이동 + 카드 상세/수정 모달.
import { apiGet, apiPost, apiPut, apiPatch, apiDelete, ApiError } from "../api.js";
import { store } from "../store.js";
import { navigate } from "../router.js";
import { mountShell } from "../layout.js";
import { esc, h, fmtDateTime, mention, toast } from "../util.js";

const COLUMNS = [
  { status: "TODO", label: "TODO", color: "bg-amber-100 text-amber-700", dot: "border-amber-300" },
  { status: "DOING", label: "DOING", color: "bg-blue-100 text-blue-700", dot: "border-blue-300" },
  { status: "DONE", label: "DONE", color: "bg-emerald-100 text-emerald-700", dot: "border-emerald-300" },
];
const FILTERS = [
  { key: "all", label: "전체" },
  { key: "me", label: "@me" },
  { key: "unassigned", label: "미할당" },
];

export async function renderKanban(app, params) {
  const teamId = Number(params.id);
  const me = store.user || {};
  let team, members = [], filter = "all";

  try {
    team = await apiGet(`/teams/${teamId}`);
    members = await apiGet(`/teams/${teamId}/members`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) return navigate("#/403");
    if (e instanceof ApiError && e.status === 401) return; // api.js가 처리
    throw e;
  }

  const memberById = new Map(members.map((m) => [m.id, m]));
  const content = mountShell(app, { active: "kanban", teamId, teamName: team.name });

  const wrap = h(`
    <div>
      <div class="flex items-center gap-2 mb-4">
        <div data-filters class="flex gap-1"></div>
        <span class="ml-auto text-sm text-slate-400">정렬: 최근 생성순</span>
      </div>
      <div data-board class="grid md:grid-cols-3 gap-4"></div>
    </div>
  `);
  const filtersEl = wrap.querySelector("[data-filters]");
  const boardEl = wrap.querySelector("[data-board]");
  content.appendChild(wrap);

  function renderFilters() {
    filtersEl.innerHTML = "";
    FILTERS.forEach((f) => {
      const b = h(
        `<button class="px-3 py-1.5 rounded-lg text-sm font-medium ${
          f.key === filter ? "bg-slate-800 text-white" : "bg-white border border-slate-200 text-slate-600"
        }">${f.label}</button>`
      );
      b.addEventListener("click", () => {
        filter = f.key;
        renderFilters();
        loadBoard();
      });
      filtersEl.appendChild(b);
    });
  }

  function assigneeLabel(task) {
    if (task.assignee_id == null) return "미할당";
    const m = memberById.get(task.assignee_id);
    return mention(m ? m.email : "?", me.email);
  }

  function cardNode(task) {
    const unassigned = task.assignee_id == null;
    const card = h(`
      <div draggable="true" data-id="${task.id}"
        class="bg-white border border-slate-200 rounded-lg p-3 shadow-sm hover:shadow cursor-pointer">
        <p class="font-medium text-slate-800 text-sm break-words">${esc(task.title)}</p>
        <p class="text-xs text-slate-400 mt-1">#${task.id} ·
          <span class="${unassigned ? "text-amber-600" : ""}">${esc(assigneeLabel(task))}</span></p>
      </div>
    `);
    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(task.id));
      card.classList.add("card-dragging");
    });
    card.addEventListener("dragend", () => card.classList.remove("card-dragging"));
    card.addEventListener("click", () => openModal(task));
    return card;
  }

  function columnNode(col, tasks) {
    const node = h(`
      <section data-status="${col.status}" class="bg-slate-50 rounded-xl p-3 min-h-[200px]">
        <div class="flex items-center justify-between mb-3 px-1">
          <span class="text-sm font-bold px-2 py-0.5 rounded ${col.color}">${col.label} · ${tasks.length}</span>
          <button data-add class="text-slate-400 hover:text-brand text-lg leading-none" title="카드 추가">+</button>
        </div>
        <div data-list class="space-y-2"></div>
      </section>
    `);
    const list = node.querySelector("[data-list]");
    if (tasks.length === 0) {
      list.appendChild(
        h(`<div class="text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-lg py-6">카드 없음</div>`)
      );
    } else {
      tasks.forEach((t) => list.appendChild(cardNode(t)));
    }

    // 인라인 생성
    node.querySelector("[data-add]").addEventListener("click", () => openInlineCreate(node, col.status));

    // 드롭 타깃
    node.addEventListener("dragover", (e) => {
      e.preventDefault();
      node.classList.add("col-dragover");
    });
    node.addEventListener("dragleave", () => node.classList.remove("col-dragover"));
    node.addEventListener("drop", async (e) => {
      e.preventDefault();
      node.classList.remove("col-dragover");
      const id = Number(e.dataTransfer.getData("text/plain"));
      if (!id) return;
      try {
        await apiPatch(`/tasks/${id}/status`, { status: col.status });
        await loadBoard();
      } catch (e2) {
        toast(e2 instanceof ApiError ? e2.message : "이동 실패", "error");
      }
    });
    return node;
  }

  function openInlineCreate(colNode, status) {
    if (colNode.querySelector("[data-inline]")) return;
    const list = colNode.querySelector("[data-list]");
    const opts = assigneeOptions(me.id);
    const form = h(`
      <div data-inline class="bg-white border-2 border-brand rounded-lg p-2">
        <input data-title maxlength="100" placeholder="할 일 제목" autofocus
          class="w-full text-sm border-b border-slate-200 pb-1 mb-2 focus:outline-none" />
        <div class="flex items-center gap-2">
          <select data-assignee class="text-xs border border-slate-200 rounded px-1 py-1 flex-1">${opts}</select>
        </div>
        <p class="text-[11px] text-slate-400 mt-1">Enter: 저장 · Esc: 취소</p>
      </div>
    `);
    list.prepend(form);
    const title = form.querySelector("[data-title]");
    title.focus();
    const save = async () => {
      const t = title.value.trim();
      if (!t) return form.remove();
      const a = form.querySelector("[data-assignee]").value;
      try {
        await apiPost(`/teams/${teamId}/tasks`, {
          title: t,
          status,
          assignee_id: a === "" ? null : Number(a),
        });
        await loadBoard();
      } catch (e2) {
        toast(e2 instanceof ApiError ? e2.message : "생성 실패", "error");
      }
    };
    title.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        save();
      } else if (e.key === "Escape") {
        form.remove();
      }
    });
  }

  function assigneeOptions(selectedId) {
    const opt = (val, label, sel) =>
      `<option value="${val}" ${sel ? "selected" : ""}>${esc(label)}</option>`;
    let html = "";
    members.forEach((m) => {
      const label = m.id === me.id ? `@me (${m.email})` : m.email;
      html += opt(m.id, label, m.id === selectedId);
    });
    html += opt("", "미할당", selectedId == null);
    return html;
  }

  async function loadBoard() {
    let tasks;
    try {
      tasks = await apiGet(`/teams/${teamId}/tasks?filter=${filter}`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) return navigate("#/403");
      return;
    }
    boardEl.innerHTML = "";
    COLUMNS.forEach((col) => {
      const colTasks = tasks.filter((t) => t.status === col.status);
      boardEl.appendChild(columnNode(col, colTasks));
    });
  }

  // ---- 카드 상세/수정 모달 ----
  function openModal(task) {
    const root = document.getElementById("modal-root");
    const creator = memberById.get(task.creator_id);
    const canDelete = task.creator_id === me.id || team.owner_id === me.id;
    const statusBtn = (s) =>
      `<button data-status="${s}" class="px-3 py-1.5 rounded-lg text-sm border ${
        task.status === s ? "bg-blue-50 border-blue-400 text-blue-700 font-medium" : "border-slate-200 text-slate-500"
      }">${s}</button>`;

    const overlay = h(`
      <div class="fixed inset-0 z-40 bg-black/40 flex items-center justify-center px-4">
        <div class="w-full max-w-lg bg-white rounded-2xl shadow-xl p-6">
          <div class="flex items-start gap-3 mb-5">
            <span class="text-slate-400 text-sm mt-1">#${task.id}</span>
            <input data-title value="${esc(task.title)}" maxlength="100"
              class="flex-1 text-lg font-bold border-b border-transparent hover:border-slate-200 focus:border-brand focus:outline-none pb-1" />
            <button data-close class="text-slate-400 hover:text-slate-600 text-xl leading-none">✕</button>
          </div>
          <div class="space-y-4 text-sm">
            <div class="flex items-center gap-3">
              <span class="w-16 text-slate-400">상태</span>
              <div data-statuses class="flex gap-2">${COLUMNS.map((c) => statusBtn(c.status)).join("")}</div>
            </div>
            <div class="flex items-center gap-3">
              <span class="w-16 text-slate-400">담당자</span>
              <select data-assignee class="border border-slate-200 rounded-lg px-2 py-1.5 flex-1">${assigneeOptions(task.assignee_id)}</select>
            </div>
            <div class="flex items-center gap-3">
              <span class="w-16 text-slate-400">생성자</span>
              <span>${esc(creator ? creator.email : "#" + task.creator_id)}</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="w-16 text-slate-400">생성 시각</span>
              <span>${esc(fmtDateTime(task.created_at))}</span>
            </div>
          </div>
          <div class="flex items-center gap-2 mt-6">
            <button data-save class="bg-brand hover:bg-brand-dark text-white font-medium rounded-lg px-4 py-2">저장</button>
            ${canDelete ? '<button data-delete class="ml-auto text-red-600 border border-red-200 rounded-lg px-4 py-2 hover:bg-red-50">🗑 삭제</button>' : ""}
          </div>
        </div>
      </div>
    `);

    let chosenStatus = task.status;
    overlay.querySelectorAll("[data-statuses] button").forEach((b) => {
      b.addEventListener("click", () => {
        chosenStatus = b.dataset.status;
        overlay.querySelectorAll("[data-statuses] button").forEach((x) => {
          const on = x.dataset.status === chosenStatus;
          x.className = `px-3 py-1.5 rounded-lg text-sm border ${
            on ? "bg-blue-50 border-blue-400 text-blue-700 font-medium" : "border-slate-200 text-slate-500"
          }`;
        });
      });
    });

    const close = () => overlay.remove();
    overlay.querySelector("[data-close]").addEventListener("click", close);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
    });

    overlay.querySelector("[data-save]").addEventListener("click", async () => {
      const title = overlay.querySelector("[data-title]").value.trim();
      const a = overlay.querySelector("[data-assignee]").value;
      if (!title) return toast("제목을 입력하세요", "error");
      try {
        await apiPut(`/tasks/${task.id}`, { title, assignee_id: a === "" ? null : Number(a) });
        if (chosenStatus !== task.status) await apiPatch(`/tasks/${task.id}/status`, { status: chosenStatus });
        close();
        await loadBoard();
        toast("저장했습니다", "success");
      } catch (e2) {
        toast(e2 instanceof ApiError ? e2.message : "저장 실패", "error");
      }
    });

    const delBtn = overlay.querySelector("[data-delete]");
    if (delBtn) {
      delBtn.addEventListener("click", () => {
        if (!confirm(`'#${task.id} ${task.title}' 카드를 삭제하시겠습니까? 되돌릴 수 없습니다.`)) return;
        apiDelete(`/tasks/${task.id}`)
          .then(async () => {
            close();
            await loadBoard();
            toast("삭제했습니다", "success");
          })
          .catch((e2) => toast(e2 instanceof ApiError ? e2.message : "삭제 실패", "error"));
      });
    }

    root.appendChild(overlay);
  }

  renderFilters();
  await loadBoard();

  // 뷰 떠날 때 모달 정리
  return () => {
    document.getElementById("modal-root").innerHTML = "";
  };
}
