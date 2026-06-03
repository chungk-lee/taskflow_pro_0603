// 부트스트랩: 라우트 등록 후 라우터 시작.
import { route, startRouter } from "./router.js";
import { renderLogin, renderSignup } from "./views/auth.js";
import { renderTeamSelect } from "./views/teams.js";
import { renderKanban } from "./views/kanban.js";
import { renderChat } from "./views/chat.js";
import { renderMembers } from "./views/members.js";
import { renderForbidden } from "./views/forbidden.js";

route("/login", renderLogin);
route("/signup", renderSignup);
route("/team-select", renderTeamSelect);
route("/teams/:id", renderKanban);
route("/teams/:id/chat", renderChat);
route("/teams/:id/members", renderMembers);
route("/403", renderForbidden);

startRouter();
