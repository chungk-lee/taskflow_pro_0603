// 채팅: since_id 증분 폴링(5초, 입력 포커스 2초) + 1000자 카운터 + 본인 메시지 삭제.
import { apiGet, apiPost, apiDelete, ApiError } from "../api.js";
import { store } from "../store.js";
import { navigate } from "../router.js";
import { mountShell } from "../layout.js";
import { esc, h, fmtTime, toast } from "../util.js";

const MAX = 1000;

export async function renderChat(app, params) {
  const teamId = Number(params.id);
  const me = store.user || {};
  let team;
  try {
    team = await apiGet(`/teams/${teamId}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) return navigate("#/403");
    return;
  }

  const content = mountShell(app, { active: "chat", teamId, teamName: team.name });
  const view = h(`
    <div class="bg-white border border-slate-200 rounded-2xl flex flex-col" style="height: calc(100vh - 8rem)">
      <div class="px-4 py-3 border-b border-slate-200 flex items-center">
        <span class="font-bold">${esc(team.name)} · 채팅</span>
        <span data-status class="ml-auto text-xs text-emerald-600">● 5초마다 새로고침</span>
      </div>
      <div data-list class="flex-1 overflow-y-auto px-4 py-4 space-y-3"></div>
      <form data-form class="border-t border-slate-200 p-3 flex items-end gap-2">
        <div class="flex-1">
          <textarea data-input rows="1" placeholder="메시지 입력 (1000자 이내)…"
            class="w-full resize-none border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand max-h-32"></textarea>
          <div class="text-right text-xs mt-0.5"><span data-counter class="text-slate-400">0 / 1000</span></div>
        </div>
        <button data-send class="bg-brand hover:bg-brand-dark text-white font-medium rounded-lg px-4 py-2 mb-5">전송</button>
      </form>
    </div>
  `);
  content.appendChild(view);

  const listEl = view.querySelector("[data-list]");
  const statusEl = view.querySelector("[data-status]");
  const input = view.querySelector("[data-input]");
  const counter = view.querySelector("[data-counter]");
  const sendBtn = view.querySelector("[data-send]");
  const form = view.querySelector("[data-form]");

  let lastId = 0;
  let timer = null;
  let interval = 5000;
  let alive = true;
  const seen = new Set(); // 렌더된 메시지 id (send/poll 경합 시 중복 렌더 방지)

  function emptyState() {
    listEl.innerHTML = `
      <div class="h-full flex flex-col items-center justify-center text-center text-slate-400">
        <div class="text-4xl mb-2">💬</div>
        <p class="font-medium text-slate-500">아직 대화가 없습니다</p>
        <p class="text-sm">첫 메시지를 보내 팀원과 대화를 시작하세요</p>
      </div>`;
  }

  function bubble(m) {
    const mine = m.user_id === me.id;
    const node = h(`
      <div class="flex flex-col ${mine ? "items-end" : "items-start"}">
        <span class="text-xs text-slate-400 mb-0.5">${mine ? "나" : esc(m.user_email)} · ${fmtTime(m.created_at)}</span>
        <div class="group flex items-center gap-1 ${mine ? "flex-row-reverse" : ""}">
          <div class="max-w-md px-3 py-2 rounded-2xl text-sm break-words ${
            mine ? "bg-brand text-white" : "bg-slate-100 text-slate-800"
          }">${esc(m.content)}</div>
          ${mine ? '<button data-del class="opacity-0 group-hover:opacity-100 text-red-500 text-sm px-1" title="삭제">🗑</button>' : ""}
        </div>
      </div>
    `);
    if (mine) {
      node.querySelector("[data-del]").addEventListener("click", async () => {
        try {
          await apiDelete(`/messages/${m.id}`);
          seen.delete(m.id);
          node.remove();
          if (!listEl.querySelector("[class*='flex-col']")) emptyState();
        } catch (e) {
          toast(e instanceof ApiError ? e.message : "삭제 실패", "error");
        }
      });
    }
    return node;
  }

  function append(messages) {
    // 이미 렌더된 메시지(send 낙관적 추가 vs poll 수신 경합)는 건너뛴다
    const fresh = messages.filter((m) => !seen.has(m.id));
    if (fresh.length === 0) return;
    // empty state 제거
    if (listEl.querySelector(".justify-center")) listEl.innerHTML = "";
    const atBottom = listEl.scrollHeight - listEl.scrollTop - listEl.clientHeight < 60;
    fresh.forEach((m) => {
      seen.add(m.id);
      listEl.appendChild(bubble(m));
      if (m.id > lastId) lastId = m.id;
    });
    if (atBottom) listEl.scrollTop = listEl.scrollHeight;
  }

  async function poll() {
    try {
      const msgs = await apiGet(`/teams/${teamId}/messages?since_id=${lastId}`);
      statusEl.textContent = "● 5초마다 새로고침";
      statusEl.className = "ml-auto text-xs text-emerald-600";
      append(msgs);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) return navigate("#/403");
      statusEl.textContent = "⚠ 연결 끊김 · 재시도 중";
      statusEl.className = "ml-auto text-xs text-red-500";
    }
  }

  function schedule() {
    if (!alive) return;
    timer = setTimeout(async () => {
      await poll();
      schedule();
    }, interval);
  }

  // 초기 로드(since_id 없이 최근 50개)
  try {
    const initial = await apiGet(`/teams/${teamId}/messages`);
    if (initial.length === 0) emptyState();
    else append(initial);
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) return navigate("#/403");
  }
  schedule();

  // 입력/카운터
  function updateCounter() {
    const len = input.value.length;
    counter.textContent = `${len} / ${MAX}`;
    const over = len > MAX;
    counter.className = over ? "text-red-600 font-medium" : "text-slate-400";
    sendBtn.disabled = over || input.value.trim().length === 0;
    sendBtn.classList.toggle("opacity-50", sendBtn.disabled);
    // textarea 자동 높이
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 128) + "px";
  }
  input.addEventListener("input", updateCounter);
  input.addEventListener("focus", () => {
    interval = 2000;
  });
  input.addEventListener("blur", () => {
    interval = 5000;
  });
  updateCounter();

  async function send() {
    const content = input.value.trim();
    if (!content || content.length > MAX) return;
    sendBtn.disabled = true;
    try {
      const m = await apiPost(`/teams/${teamId}/messages`, { content });
      append([m]);
      input.value = "";
      updateCounter();
      listEl.scrollTop = listEl.scrollHeight;
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "전송 실패", "error");
    } finally {
      sendBtn.disabled = false;
    }
  }
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    send();
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });

  // 뷰 떠날 때 폴링 중지
  return () => {
    alive = false;
    if (timer) clearTimeout(timer);
  };
}
