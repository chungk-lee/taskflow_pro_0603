// 해시 라우터 + 세션 가드. 뷰는 (container, params) → optional cleanup 함수.
import { store } from "./store.js";

const routes = [];
let cleanup = null;

export function route(pattern, handler) {
  const keys = (pattern.match(/:[^/]+/g) || []).map((s) => s.slice(1));
  const regex = new RegExp("^" + pattern.replace(/:[^/]+/g, "([^/]+)") + "$");
  routes.push({ regex, keys, handler });
}

export function navigate(hash) {
  if (location.hash === hash) renderCurrent();
  else location.hash = hash;
}

function guard(path) {
  const t = store.token;
  const u = store.user;
  const isPublic = path === "/login" || path === "/signup";

  if (!t) return isPublic ? null : "#/login";

  if (u && u.team_id == null) {
    if (path.startsWith("/teams/") || path === "/login" || path === "/signup") return "#/team-select";
  }
  if (u && u.team_id != null) {
    if (path === "/login" || path === "/signup" || path === "/team-select") return "#/teams/" + u.team_id;
  }
  if (path === "/") {
    if (!u) return "#/login";
    return u.team_id != null ? "#/teams/" + u.team_id : "#/team-select";
  }
  return null;
}

async function renderCurrent() {
  const hash = location.hash || "#/";
  const path = hash.replace(/^#/, "") || "/";

  const redirect = guard(path);
  if (redirect) {
    location.hash = redirect;
    return;
  }

  for (const r of routes) {
    const m = r.regex.exec(path);
    if (m) {
      const params = {};
      r.keys.forEach((k, i) => (params[k] = decodeURIComponent(m[i + 1])));
      if (cleanup) {
        try {
          cleanup();
        } catch {
          /* ignore */
        }
        cleanup = null;
      }
      const app = document.getElementById("app");
      app.innerHTML = "";
      const maybeCleanup = await r.handler(app, params);
      if (typeof maybeCleanup === "function") cleanup = maybeCleanup;
      return;
    }
  }
  document.getElementById("app").innerHTML =
    '<p class="p-8 text-center text-slate-500">페이지를 찾을 수 없습니다.</p>';
}

export function startRouter() {
  window.addEventListener("hashchange", renderCurrent);
  renderCurrent();
}
