// 팀 선택(미가입): 팀 만들기 + 초대코드 합류. 생성 후 초대코드 안내.
import { apiPost, ApiError } from "../api.js";
import { store } from "../store.js";
import { navigate } from "../router.js";
import { logout } from "../layout.js";
import { esc, h, toast } from "../util.js";

const CODE_RE = /^[A-Z]{4}-[0-9]{4}$/;

export function renderTeamSelect(app) {
  const user = store.user || {};
  const view = h(`
    <div class="min-h-screen flex flex-col">
      <header class="bg-white border-b border-slate-200">
        <div class="max-w-3xl mx-auto px-4 h-14 flex items-center">
          <span class="font-bold text-brand text-lg">TaskFlow</span>
          <div class="ml-auto flex items-center gap-3">
            <span class="text-sm text-slate-500">${esc(user.email || "")}</span>
            <button data-logout class="text-sm text-slate-500 hover:text-red-600">로그아웃</button>
          </div>
        </div>
      </header>
      <main class="flex-1 max-w-3xl w-full mx-auto px-4 py-8">
        <div class="bg-blue-50 text-blue-700 text-sm rounded-lg px-4 py-3 mb-6">
          ℹ 아직 팀에 소속되지 않았습니다. 팀을 만들거나 초대코드로 합류하세요.
        </div>
        <div class="grid md:grid-cols-2 gap-4">
          <section class="bg-white border border-slate-200 rounded-2xl p-6">
            <h2 class="font-bold mb-4">+ 새 팀 만들기</h2>
            <form data-create class="space-y-3">
              <input data-name maxlength="30" placeholder="팀 이름 (1–30자)"
                class="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand" />
              <p data-create-err class="hidden text-sm text-red-600"></p>
              <button class="w-full bg-brand hover:bg-brand-dark text-white font-medium rounded-lg py-2.5">만들기</button>
            </form>
          </section>
          <section class="bg-white border border-slate-200 rounded-2xl p-6">
            <h2 class="font-bold mb-4">초대코드로 합류</h2>
            <form data-join class="space-y-1">
              <input data-code maxlength="9" placeholder="ABCD-1234"
                class="w-full border border-slate-300 rounded-lg px-3 py-2 text-center tracking-widest uppercase focus:outline-none focus:ring-2 focus:ring-brand" />
              <p class="text-xs text-slate-400 py-1">형식: 대문자 4 + 숫자 4 (하이픈 포함)</p>
              <p data-join-err class="hidden text-sm text-red-600"></p>
              <button class="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-lg py-2.5">합류</button>
            </form>
          </section>
        </div>
      </main>
    </div>
  `);

  view.querySelector("[data-logout]").addEventListener("click", logout);

  // 팀 생성
  const createForm = view.querySelector("[data-create]");
  const createErr = view.querySelector("[data-create-err]");
  createForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    createErr.classList.add("hidden");
    const name = view.querySelector("[data-name]").value.trim();
    if (name.length < 1 || name.length > 30) {
      createErr.textContent = "팀 이름은 1–30자입니다";
      createErr.classList.remove("hidden");
      return;
    }
    try {
      const team = await apiPost("/teams", { name });
      store.patchUser({ team_id: team.id });
      showCreated(team);
    } catch (e2) {
      createErr.textContent = e2 instanceof ApiError ? e2.message : "생성 실패";
      createErr.classList.remove("hidden");
    }
  });

  // 초대코드 합류
  const joinForm = view.querySelector("[data-join]");
  const joinErr = view.querySelector("[data-join-err]");
  const codeInput = view.querySelector("[data-code]");
  codeInput.addEventListener("input", () => {
    codeInput.value = codeInput.value.toUpperCase();
  });
  joinForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    joinErr.classList.add("hidden");
    const code = codeInput.value.trim().toUpperCase();
    if (!CODE_RE.test(code)) {
      joinErr.textContent = "형식이 올바르지 않습니다 (예: FRNT-2026)";
      joinErr.classList.remove("hidden");
      return;
    }
    try {
      const team = await apiPost("/teams/join", { invite_code: code });
      store.patchUser({ team_id: team.id });
      toast("팀에 합류했습니다", "success");
      navigate("#/teams/" + team.id);
    } catch (e2) {
      joinErr.textContent = e2 instanceof ApiError ? e2.message : "합류 실패";
      joinErr.classList.remove("hidden");
    }
  });

  // 생성 완료 → 초대코드 안내 화면으로 교체
  function showCreated(team) {
    app.innerHTML = "";
    const done = h(`
      <div class="min-h-screen flex items-center justify-center px-4">
        <div class="w-full max-w-md bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">
          <div class="bg-emerald-50 text-emerald-700 rounded-lg py-3 mb-6 font-medium">✓ 팀이 생성되었습니다!</div>
          <p class="text-sm text-slate-500">팀 이름</p>
          <p class="text-lg font-bold mb-4">${esc(team.name)}</p>
          <p class="text-sm text-slate-500 mb-1">초대코드 (멤버에게 공유)</p>
          <div class="flex items-center gap-2 justify-center mb-6">
            <code class="text-2xl font-bold tracking-widest text-emerald-600 border-2 border-emerald-200 rounded-lg px-4 py-2">${esc(team.invite_code)}</code>
            <button data-copy class="text-sm bg-slate-800 text-white rounded-lg px-3 py-2">복사</button>
          </div>
          <button data-go class="w-full bg-brand hover:bg-brand-dark text-white font-medium rounded-lg py-2.5">칸반 시작하기 →</button>
        </div>
      </div>
    `);
    done.querySelector("[data-copy]").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(team.invite_code);
        toast("초대코드를 복사했습니다", "success");
      } catch {
        toast("복사에 실패했습니다", "error");
      }
    });
    done.querySelector("[data-go]").addEventListener("click", () => navigate("#/teams/" + team.id));
    app.appendChild(done);
  }

  app.appendChild(view);
}
