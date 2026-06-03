// 로그인 / 회원가입 화면.
import { apiPost, ApiError } from "../api.js";
import { store } from "../store.js";
import { navigate } from "../router.js";
import { h } from "../util.js";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function authCard(inner) {
  return h(`
    <div class="min-h-screen flex items-center justify-center px-4">
      <div class="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
        <div class="text-center mb-6">
          <span class="inline-block bg-brand text-white font-bold px-4 py-2 rounded-lg">TaskFlow</span>
        </div>
        ${inner}
      </div>
    </div>
  `);
}

function goAfterAuth() {
  const u = store.user;
  navigate(u && u.team_id != null ? "#/teams/" + u.team_id : "#/team-select");
}

export function renderLogin(app) {
  const card = authCard(`
    <h1 class="text-xl font-bold text-center mb-6">로그인</h1>
    <form data-form class="space-y-3">
      <input data-email type="email" placeholder="이메일" autocomplete="username"
        class="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand" />
      <input data-password type="password" placeholder="비밀번호" autocomplete="current-password"
        class="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand" />
      <p data-error class="hidden text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2"></p>
      <button data-submit type="submit"
        class="w-full bg-brand hover:bg-brand-dark text-white font-medium rounded-lg py-2.5 transition">로그인</button>
    </form>
    <p class="text-center text-sm text-slate-500 mt-4">계정이 없으신가요?
      <a href="#/signup" class="text-brand font-medium">회원가입</a></p>
  `);

  const form = card.querySelector("[data-form]");
  const err = card.querySelector("[data-error]");
  const btn = card.querySelector("[data-submit]");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    err.classList.add("hidden");
    const email = card.querySelector("[data-email]").value.trim();
    const password = card.querySelector("[data-password]").value;
    if (!EMAIL_RE.test(email) || !password) {
      err.textContent = "이메일과 비밀번호를 확인해주세요";
      err.classList.remove("hidden");
      return;
    }
    btn.disabled = true;
    btn.textContent = "처리 중…";
    try {
      const res = await apiPost("/auth/login", { email, password });
      store.setSession(res.token, res.user);
      goAfterAuth();
    } catch (e2) {
      err.textContent = e2 instanceof ApiError ? e2.message : "로그인에 실패했습니다";
      err.classList.remove("hidden");
      btn.disabled = false;
      btn.textContent = "로그인";
    }
  });

  app.appendChild(card);
}

export function renderSignup(app) {
  const card = authCard(`
    <h1 class="text-xl font-bold text-center mb-6">회원가입</h1>
    <form data-form class="space-y-3">
      <div>
        <input data-email type="email" placeholder="이메일 입력" autocomplete="username"
          class="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand" />
        <p data-email-err class="hidden text-xs text-red-600 mt-1">올바른 이메일 형식이 아닙니다</p>
      </div>
      <div>
        <input data-password type="password" placeholder="비밀번호 (8자 이상)" autocomplete="new-password"
          class="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand" />
        <p data-pw-err class="hidden text-xs text-red-600 mt-1">8자 이상 입력해주세요</p>
      </div>
      <p data-error class="hidden text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2"></p>
      <button data-submit type="submit"
        class="w-full bg-brand hover:bg-brand-dark text-white font-medium rounded-lg py-2.5 transition">가입하기</button>
    </form>
    <p class="text-center text-sm text-slate-500 mt-4">이미 계정이 있으신가요?
      <a href="#/login" class="text-brand font-medium">로그인</a></p>
  `);

  const form = card.querySelector("[data-form]");
  const err = card.querySelector("[data-error]");
  const btn = card.querySelector("[data-submit]");
  const emailErr = card.querySelector("[data-email-err]");
  const pwErr = card.querySelector("[data-pw-err]");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    err.classList.add("hidden");
    emailErr.classList.add("hidden");
    pwErr.classList.add("hidden");
    const email = card.querySelector("[data-email]").value.trim();
    const password = card.querySelector("[data-password]").value;
    let bad = false;
    if (!EMAIL_RE.test(email)) {
      emailErr.classList.remove("hidden");
      bad = true;
    }
    if (password.length < 8) {
      pwErr.classList.remove("hidden");
      bad = true;
    }
    if (bad) return;

    btn.disabled = true;
    btn.textContent = "처리 중…";
    try {
      const res = await apiPost("/auth/signup", { email, password });
      store.setSession(res.token, res.user);
      goAfterAuth();
    } catch (e2) {
      err.textContent = e2 instanceof ApiError ? e2.message : "가입에 실패했습니다";
      err.classList.remove("hidden");
      btn.disabled = false;
      btn.textContent = "가입하기";
    }
  });

  app.appendChild(card);
}
