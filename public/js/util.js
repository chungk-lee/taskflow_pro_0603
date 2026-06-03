// 공통 DOM/포맷 헬퍼.

export function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// HTML 문자열 → DOM 노드
export function h(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

// 서버는 +09:00 ISO를 반환. 항상 KST로 표시.
export function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Seoul",
  });
}

export function fmtDateTime(iso) {
  return new Date(iso).toLocaleString("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Seoul",
  });
}

export function fmtDate(iso) {
  return new Date(iso).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "Asia/Seoul",
  });
}

let toastSeq = 0;
export function toast(message, type = "info") {
  const root = document.getElementById("toast");
  if (!root) return;
  const colors = {
    info: "bg-slate-800",
    success: "bg-emerald-600",
    error: "bg-red-600",
  };
  const id = "t" + ++toastSeq;
  const node = h(
    `<div id="${id}" class="${colors[type] || colors.info} text-white text-sm px-4 py-2 rounded-lg shadow-lg opacity-0 transition-opacity">${esc(
      message
    )}</div>`
  );
  root.appendChild(node);
  requestAnimationFrame(() => node.classList.remove("opacity-0"));
  setTimeout(() => {
    node.classList.add("opacity-0");
    setTimeout(() => node.remove(), 300);
  }, 2500);
}

// @localpart 표기 (현재 사용자는 @me)
export function mention(email, myEmail) {
  if (!email) return "미할당";
  if (email === myEmail) return "@me";
  return "@" + email.split("@")[0];
}
