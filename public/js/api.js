// fetch 래퍼: JWT 자동 첨부, 표준 에러 파싱, 401(TOKEN_EXPIRED) 시 세션 폐기 후 로그인 이동.
import { store } from "./store.js";

const isLocal = ["localhost", "127.0.0.1"].includes(location.hostname);
// 로컬: 별도 포트의 FastAPI. 운영(Vercel): 동일 출처(상대경로).
export const API_BASE = isLocal ? "http://127.0.0.1:8000" : "";

export class ApiError extends Error {
  constructor(status, code, message, meta) {
    super(message || "오류가 발생했습니다");
    this.status = status;
    this.code = code || "ERROR";
    this.meta = meta || {};
  }
}

export async function api(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = store.token;
  if (token) headers["Authorization"] = "Bearer " + token;

  let res;
  try {
    res = await fetch(API_BASE + path, {
      method,
      headers,
      body: body != null ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "NETWORK", "서버에 연결할 수 없습니다");
  }

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      /* non-json */
    }
  }

  if (!res.ok) {
    const err = (data && data.error) || {};
    // 인증 만료만 세션 폐기 + 리다이렉트. (로그인 실패 INVALID_CREDENTIALS는 제외)
    if (res.status === 401 && err.code === "TOKEN_EXPIRED") {
      store.clear();
      if (!location.hash.startsWith("#/login")) location.hash = "#/login";
    }
    throw new ApiError(res.status, err.code, err.message, err.meta);
  }
  return data;
}

export const apiGet = (p) => api("GET", p);
export const apiPost = (p, b) => api("POST", p, b);
export const apiPut = (p, b) => api("PUT", p, b);
export const apiPatch = (p, b) => api("PATCH", p, b);
export const apiDelete = (p) => api("DELETE", p);
