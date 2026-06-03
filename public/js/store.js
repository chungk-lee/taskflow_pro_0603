// 세션 상태: 토큰 + 사용자. localStorage 백엔드.
const KEY_TOKEN = "taskflow_token";
const KEY_USER = "taskflow_user";

export const store = {
  get token() {
    return localStorage.getItem(KEY_TOKEN);
  },
  get user() {
    try {
      return JSON.parse(localStorage.getItem(KEY_USER));
    } catch {
      return null;
    }
  },
  setSession(token, user) {
    localStorage.setItem(KEY_TOKEN, token);
    localStorage.setItem(KEY_USER, JSON.stringify(user));
  },
  setUser(user) {
    localStorage.setItem(KEY_USER, JSON.stringify(user));
  },
  patchUser(patch) {
    const u = this.user || {};
    localStorage.setItem(KEY_USER, JSON.stringify({ ...u, ...patch }));
  },
  clear() {
    localStorage.removeItem(KEY_TOKEN);
    localStorage.removeItem(KEY_USER);
  },
};
