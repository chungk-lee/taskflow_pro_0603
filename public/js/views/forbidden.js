// 403: 비멤버 팀 접근.
import { store } from "../store.js";
import { navigate } from "../router.js";
import { h } from "../util.js";

export function renderForbidden(app) {
  const u = store.user;
  const view = h(`
    <div class="min-h-screen flex items-center justify-center px-4">
      <div class="text-center">
        <div class="text-5xl mb-3">🚫</div>
        <p class="text-4xl font-bold text-red-600 mb-2">403</p>
        <p class="text-lg font-medium mb-1">이 팀에 접근할 권한이 없습니다</p>
        <p class="text-sm text-slate-500 mb-6">당신은 이 팀의 멤버가 아닙니다.<br/>초대코드를 받았다면 팀 선택 화면에서 입력하세요.</p>
        <button data-go class="bg-brand hover:bg-brand-dark text-white font-medium rounded-lg px-5 py-2.5">내 팀으로 돌아가기</button>
      </div>
    </div>
  `);
  view.querySelector("[data-go]").addEventListener("click", () => {
    navigate(u && u.team_id != null ? "#/teams/" + u.team_id : "#/team-select");
  });
  app.appendChild(view);
}
