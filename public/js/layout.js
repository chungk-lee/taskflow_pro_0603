// 인증 화면 공통 셸: 헤더(로고·팀명·탭·사용자·로그아웃) + 모바일 햄버거. 콘텐츠 컨테이너 반환.
import { store } from "./store.js";
import { navigate } from "./router.js";
import { esc, h } from "./util.js";

export function logout() {
  store.clear();
  navigate("#/login");
}

export function mountShell(app, { active, teamId, teamName }) {
  const user = store.user || {};
  const tabs = [
    { key: "kanban", label: "칸반", hash: `#/teams/${teamId}` },
    { key: "chat", label: "채팅", hash: `#/teams/${teamId}/chat` },
    { key: "members", label: "멤버", hash: `#/teams/${teamId}/members` },
  ];
  const tabBtn = (t, mobile = false) =>
    `<a href="${t.hash}" data-tab="${t.key}"
        class="${mobile ? "block px-4 py-3" : "px-4 py-2 rounded-lg"} text-sm font-medium ${
      t.key === active
        ? "bg-brand text-white"
        : "text-slate-600 hover:bg-slate-100"
    }">${t.label}</a>`;

  const shell = h(`
    <div class="min-h-screen flex flex-col">
      <header class="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div class="max-w-6xl mx-auto px-4 h-14 flex items-center gap-3">
          <span class="font-bold text-brand text-lg">TaskFlow</span>
          <span class="text-slate-400 hidden sm:inline">·</span>
          <span class="text-slate-600 text-sm font-medium truncate max-w-[40vw]">${esc(teamName || "")}</span>
          <nav class="ml-4 hidden md:flex items-center gap-1">${tabs.map((t) => tabBtn(t)).join("")}</nav>
          <div class="ml-auto hidden md:flex items-center gap-3">
            <span class="text-sm text-slate-500 truncate max-w-[20vw]">${esc(user.email || "")}</span>
            <button data-logout class="text-sm text-slate-500 hover:text-red-600">로그아웃</button>
          </div>
          <button data-hamburger class="ml-auto md:hidden p-2 text-slate-600" aria-label="메뉴">☰</button>
        </div>
        <div data-mobilemenu class="md:hidden hidden border-t border-slate-200 bg-white">
          <div class="px-2 py-2">
            <div class="px-4 py-2 text-sm text-slate-500">${esc(user.email || "")}</div>
            ${tabs.map((t) => tabBtn(t, true)).join("")}
            <button data-logout class="block w-full text-left px-4 py-3 text-sm text-red-600">로그아웃</button>
          </div>
        </div>
      </header>
      <main data-content class="flex-1 max-w-6xl w-full mx-auto px-4 py-4"></main>
    </div>
  `);

  shell.querySelectorAll("[data-logout]").forEach((b) => b.addEventListener("click", logout));
  const menu = shell.querySelector("[data-mobilemenu]");
  shell.querySelector("[data-hamburger]").addEventListener("click", () => menu.classList.toggle("hidden"));

  app.appendChild(shell);
  return shell.querySelector("[data-content]");
}
