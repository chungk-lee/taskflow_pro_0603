// 멤버 목록: owner(★)/member 구분.
import { apiGet, ApiError } from "../api.js";
import { store } from "../store.js";
import { navigate } from "../router.js";
import { mountShell } from "../layout.js";
import { esc, h, fmtDate } from "../util.js";

export async function renderMembers(app, params) {
  const teamId = Number(params.id);
  const me = store.user || {};
  let team, members;
  try {
    team = await apiGet(`/teams/${teamId}`);
    members = await apiGet(`/teams/${teamId}/members`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) return navigate("#/403");
    return;
  }

  const content = mountShell(app, { active: "members", teamId, teamName: team.name });
  const rows = members
    .map((m) => {
      const isOwner = m.role === "owner";
      const isMe = m.id === me.id;
      return `
        <div class="flex items-center gap-3 px-4 py-3 ${isMe ? "bg-slate-50" : ""}">
          <div class="w-9 h-9 rounded-full bg-brand/10 text-brand flex items-center justify-center font-bold uppercase">
            ${esc((m.email[0] || "?"))}
          </div>
          <div class="min-w-0">
            <p class="text-sm font-medium truncate">${esc(m.email)} ${isMe ? '<span class="text-slate-400">(나)</span>' : ""}</p>
            <p class="text-xs ${isOwner ? "text-amber-600 font-medium" : "text-slate-400"}">${isOwner ? "★ owner" : "member"}</p>
          </div>
          <span class="ml-auto text-xs text-slate-400">${esc(fmtDate(m.joined_at))}</span>
        </div>`;
    })
    .join("");

  content.appendChild(
    h(`
    <div class="max-w-lg">
      <h2 class="font-bold mb-3">팀 멤버 (${members.length})</h2>
      <div class="bg-white border border-slate-200 rounded-2xl divide-y divide-slate-100">${rows}</div>
      <p class="text-xs text-slate-400 mt-3">owner 1명 / member N명 · 추방·역할 변경은 범위 외</p>
    </div>
  `)
  );
}
