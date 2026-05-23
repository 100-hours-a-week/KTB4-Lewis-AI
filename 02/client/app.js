window.addEventListener("error", (event) => {
  const msg = `[Global Error] ${event.message} at ${event.filename}:${event.lineno}:${event.colno}`;
  console.error(msg, event.error);
  alert(msg + "\n" + (event.error ? event.error.stack : ""));
});

window.addEventListener("unhandledrejection", (event) => {
  const msg = `[Unhandled Rejection] ${event.reason}`;
  console.error(msg, event.reason);
  alert(msg + "\n" + (event.reason && event.reason.stack ? event.reason.stack : ""));
});

const state = {
  posts: [],
  selectedPost: null,
  comments: [],
  category: "",
  sort: "latest",
  editing: false,
  replyTarget: null,
  toxicPollTimer: null,
};

const $ = (id) => document.getElementById(id);

const elements = {
  baseUrl: $("baseUrlInput"),
  anonymousId: $("anonymousIdInput"),
  connection: $("connectionLabel"),
  toast: $("toast"),
  response: $("responseOutput"),
  composer: $("composerPanel"),
};

function init() {
  elements.baseUrl.value = localStorage.getItem("community.baseUrl") || defaultBaseUrl();
  elements.anonymousId.value = localStorage.getItem("community.anonymousId") || createId();
  saveSettings();
  hideLegacyPanels();
  ensurePostRail();
  bindEvents();
  loadPosts();
  checkStatus(false);
}

function hideLegacyPanels() {
  ["postDetail", "editPanel", "commentsSection"].forEach((id) => {
    const element = $(id);
    if (element) element.remove();
  });
  $("emptyState")?.classList.add("hidden");
}

function defaultBaseUrl() {
  return location.protocol.startsWith("http") ? location.origin : "http://127.0.0.1:8000";
}

function createId() {
  return crypto.randomUUID ? crypto.randomUUID() : `client-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function saveSettings() {
  localStorage.setItem("community.baseUrl", elements.baseUrl.value.trim());
  localStorage.setItem("community.anonymousId", elements.anonymousId.value.trim());
}

function apiPath(path) {
  return `${elements.baseUrl.value.trim().replace(/\/$/, "")}${path}`;
}

async function api(path, options = {}) {
  saveSettings();
  const headers = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.auth) headers["X-Anonymous-ID"] = elements.anonymousId.value.trim();

  const response = await fetch(apiPath(path), {
    method: options.method || "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

async function run(action, successMessage, options = {}) {
  try {
    if (!options.silent) setToast("요청 중...", "warn");
    const data = await action();
    renderResponse(data);
    if (!options.silent) setToast(successMessage, "ok");
    return data;
  } catch (error) {
    renderResponse(error.data || String(error));
    setToast(error.status ? `HTTP ${error.status}` : "요청 실패", "error");
    return null;
  }
}

function setToast(message, type = "") {
  elements.toast.className = "rounded-xl border p-md text-sm";
  const classes = {
    ok: ["border-secondary-container", "bg-secondary-container/20", "text-secondary"],
    error: ["border-error-container", "bg-error-container/60", "text-error"],
    warn: ["border-tertiary-fixed", "bg-tertiary-fixed/40", "text-tertiary"],
    default: ["border-outline-variant", "bg-surface-container-low", "text-on-surface-variant"],
  };
  elements.toast.classList.add(...(classes[type] || classes.default));
  elements.toast.textContent = message;
}

function renderResponse(data) {
  elements.response.textContent = JSON.stringify(data, null, 2);
}

function queryString(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) query.set(key, value);
  });
  return query.toString();
}

function ensurePostRail() {
  let rail = $("postRail");
  if (rail) return rail;
  rail = document.createElement("div");
  rail.id = "postRail";
  rail.className = "space-y-sm mb-lg";
  $("emptyState").insertAdjacentElement("beforebegin", rail);
  return rail;
}

async function checkStatus(showToast = true) {
  const data = await run(() => api("/"), "서버 연결 성공", {silent: !showToast});
  elements.connection.textContent = data ? "API 연결됨" : "API 연결 실패";
}

async function loadPosts() {
  const query = queryString({
    sort: state.sort,
    search: $("searchInput").value.trim(),
    category: state.category,
    skip: 0,
    limit: 50,
  });
  const posts = await run(() => api(`/posts/?${query}`), "게시글 목록 갱신");
  if (!posts) return;

  state.posts = posts;
  $("statsText").textContent = `${posts.length} posts`;
  if (state.selectedPost && !posts.some((post) => post.id === state.selectedPost.id)) {
    collapsePost();
  }
  renderPosts();
}

async function openPost(postId) {
  if (state.selectedPost?.id === postId) {
    collapsePost();
    renderPosts();
    return;
  }

  state.editing = false;
  state.replyTarget = null;
  const post = await run(() => api(`/posts/${postId}`), "게시글 상세 조회");
  if (!post) return;
  state.selectedPost = post;
  await loadComments(false);
  renderPosts();
}

function collapsePost() {
  state.selectedPost = null;
  state.comments = [];
  state.editing = false;
  state.replyTarget = null;
  $("breadcrumbPost").textContent = "게시글 선택";
}

function renderPosts() {
  const rail = ensurePostRail();
  if (!state.posts.length) {
    rail.innerHTML = `<div class="panel text-center text-on-surface-variant">게시글이 없습니다.</div>`;
    return;
  }

  rail.innerHTML = state.posts.map((post) => {
    const expanded = state.selectedPost?.id === post.id;
    return `
      <article class="post-list-card ${expanded ? "active" : ""}" data-post-card="${post.id}">
        <div class="post-title-button" role="button" tabindex="0" data-action="toggle-post" data-post-id="${post.id}">
          <div class="flex items-start justify-between gap-md">
            <div class="min-w-0">
              <div class="flex items-center gap-sm min-w-0">
                <div class="font-bold text-on-surface truncate min-w-0">${escapeHtml(post.title)}</div>
                ${post.comments_count > 0 ? `
                <div class="flex items-center gap-[3px] bg-on-surface text-surface px-[8px] py-[2px] rounded-full text-[11px] font-bold shrink-0">
                  <span class="material-symbols-outlined text-[12px]">chat_bubble</span>
                  <span>${post.comments_count}</span>
                </div>
                ` : ''}
              </div>
              <div class="text-xs text-on-surface-variant mt-xs">
                ${escapeHtml(post.category)} · 조회 ${post.views} · 추천 ${post.likes_count} · #${post.id}
              </div>
            </div>
            <span class="material-symbols-outlined text-primary">${expanded ? "expand_less" : "expand_more"}</span>
          </div>
        </div>
        ${expanded ? renderExpandedPost(state.selectedPost) : ""}
      </article>
    `;
  }).join("");
}

function renderExpandedPost(post) {
  $("breadcrumbCategory").textContent = state.category || post.category || "전체";
  $("breadcrumbPost").textContent = post.title;
  const canSummarize = post.content.trim().length >= 200;

  return `
    <div class="post-expanded-slot">
      <article class="bg-surface-container-lowest rounded-xl border border-outline-variant shadow-sm overflow-hidden mb-lg">
        <header class="p-lg md:p-xl border-b border-outline-variant/50">
          <div class="flex items-center gap-md mb-md">
            <div class="avatar"><span class="material-symbols-outlined">account_circle</span></div>
            <div class="min-w-0">
              <p class="text-sm text-on-surface">
                <span class="font-semibold">${escapeHtml(shortId(post.author_id))}</span>
                <span class="text-on-surface-variant"> in </span>
                <span class="text-primary font-bold">${escapeHtml(post.category)}</span>
              </p>
              <p class="text-xs text-on-surface-variant">${formatDate(post.created_at)} · 조회 ${post.views}</p>
            </div>
            <div class="ml-auto flex gap-xs">
              <button class="icon-button" data-action="edit-post" aria-label="게시글 수정">
                <span class="material-symbols-outlined">edit</span>
              </button>
              <button class="icon-button danger" data-action="delete-post" aria-label="게시글 삭제">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </div>
          </div>
          <h1 class="text-[28px] md:text-[36px] font-bold leading-tight mb-md break-words">${escapeHtml(post.title)}</h1>
          <div class="flex flex-wrap gap-sm">
            <span class="tag">${escapeHtml(post.category)}</span>
            <span class="tag neutral">#${post.id}</span>
          </div>
        </header>
        <div class="p-lg md:p-xl space-y-lg text-on-surface leading-relaxed">
          <p class="text-lg leading-relaxed whitespace-pre-wrap break-words">${escapeHtml(post.content)}</p>
          <div id="llmResultBox" class="rounded-xl border border-outline-variant bg-surface-container-low p-md hidden">
            <div class="flex items-center gap-sm text-primary font-semibold mb-sm">
              <span class="material-symbols-outlined">auto_awesome</span>
              <span>LLM 결과</span>
            </div>
            <pre id="llmResult" class="whitespace-pre-wrap break-words text-sm"></pre>
          </div>
        </div>
        <footer class="px-lg py-md md:px-xl border-t border-outline-variant/50 flex items-center justify-between bg-surface-container-lowest">
          <div class="flex items-center gap-md">
            <button class="engage-button" data-action="like-post">
              <span class="material-symbols-outlined">thumb_up</span>
              <span>${post.likes_count}</span>
            </button>
            <button class="engage-button" data-action="focus-comment">
              <span class="material-symbols-outlined">mode_comment</span>
              <span>${countComments(state.comments)}</span>
            </button>
          </div>
          <button class="button-secondary ${canSummarize ? "" : "hidden"}" data-action="summarize-post">
            <span class="material-symbols-outlined text-[18px]">summarize</span>
            요약
          </button>
        </footer>
      </article>
      ${state.editing ? renderEditForm(post) : ""}
      ${renderCommentsSection()}
    </div>
  `;
}

function renderEditForm(post) {
  return `
    <section class="panel mb-lg">
      <div class="flex items-center justify-between mb-md">
        <h2 class="font-bold text-lg">게시글 수정</h2>
        <button class="icon-button" data-action="cancel-edit" aria-label="수정 닫기">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <form class="space-y-md" data-form="edit-post">
        <div class="grid sm:grid-cols-[1fr_160px] gap-md">
          <input name="title" class="form-input" placeholder="제목" required maxlength="200" value="${escapeAttribute(post.title)}">
          <select name="category" class="form-input" required>
            ${["자유", "질문", "정보", "후기", "기술"].map((category) => `
              <option ${category === post.category ? "selected" : ""}>${category}</option>
            `).join("")}
          </select>
        </div>
        <textarea name="content" class="form-textarea min-h-[150px]" required>${escapeHtml(post.content)}</textarea>
        <div class="flex justify-end gap-sm">
          <button type="button" class="button-secondary" data-action="cancel-edit">취소</button>
          <button type="submit" class="button-primary">저장</button>
        </div>
      </form>
    </section>
  `;
}

function renderCommentsSection() {
  return `
    <section class="space-y-lg">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-xl">댓글 <span class="text-primary">${countComments(state.comments)}</span></h2>
        <button class="button-secondary" data-action="refresh-comments">
          <span class="material-symbols-outlined text-[18px]">refresh</span>
          새로고침
        </button>
      </div>
      <div class="bg-surface-container-lowest rounded-xl border border-outline-variant p-md shadow-sm">
        <form class="flex gap-md" data-form="comment">
          <div class="avatar small"><span class="material-symbols-outlined">person</span></div>
          <div class="flex-1 min-w-0">
            ${state.replyTarget ? renderReplyNotice() : ""}
            <div class="mb-sm">
              <textarea name="content" class="form-textarea min-h-[110px]" placeholder="${state.replyTarget ? "답글을 작성하세요" : "댓글을 작성하세요"}" required></textarea>
              <div class="toxic-result-box text-xs mt-sm hidden rounded-lg p-sm border"></div>
            </div>
            <div class="flex items-center justify-between gap-sm">
              <button type="button" class="button-secondary" data-action="check-toxic">
                <span class="material-symbols-outlined text-[18px]">shield</span>
                악플 검사
              </button>
              <button type="submit" class="button-primary">${state.replyTarget ? "답글 등록" : "댓글 등록"}</button>
            </div>
          </div>
        </form>
      </div>
      <div class="space-y-lg">
        ${state.comments.length ? state.comments.map(renderComment).join("") : `<div class="panel text-center text-on-surface-variant">댓글이 없습니다.</div>`}
      </div>
    </section>
  `;
}

function renderReplyNotice() {
  return `
    <div class="reply-notice mb-sm">
      <span class="material-symbols-outlined text-[18px]">subdirectory_arrow_right</span>
      <span>#${state.replyTarget.id} 댓글에 답글 작성 중${state.replyTarget.authorId ? ` · ${escapeHtml(shortId(state.replyTarget.authorId))}` : ""}</span>
      <button type="button" class="reply-cancel" data-action="cancel-reply">취소</button>
    </div>
  `;
}

function renderComment(comment) {
  const statusBadge = comment.is_toxic === null ? `
    <span class="inline-flex items-center gap-[2px] bg-tertiary-fixed text-tertiary px-[6px] py-[1px] rounded text-[10px] font-bold shrink-0">
      <span class="material-symbols-outlined text-[10px] animate-spin">sync</span>
      <span>AI 검증 중</span>
    </span>
  ` : '';

  const contentHtml = comment.is_toxic ? `
    <div class="toxic-blur-container rounded-lg p-sm border border-error-container bg-error-container/10 my-xs">
      <div class="flex items-center gap-xs text-error font-semibold text-xs mb-xs">
        <span class="material-symbols-outlined text-[16px]">report_problem</span>
        <span>부적절한 내용이 포함된 댓글일 수 있습니다.</span>
        <button class="ml-auto text-primary hover:underline text-xs" data-action="reveal-comment" data-comment-id="${comment.id}">보기</button>
      </div>
      <p id="comment-content-${comment.id}" class="text-on-surface/40 select-none whitespace-pre-wrap break-words" style="filter: blur(4px); pointer-events: none;">${escapeHtml(comment.content)}</p>
      <div id="comment-reason-${comment.id}" class="hidden text-xs text-on-surface-variant mt-sm pt-xs border-t border-outline-variant/30">
        <strong>AI 판정 사유:</strong> ${escapeHtml(comment.toxic_reason || "악성 댓글 감지")}
      </div>
    </div>
  ` : `
    <p class="text-on-surface whitespace-pre-wrap break-words">${escapeHtml(comment.content)}</p>
  `;

  return `
    <div class="comment-thread">
      <div class="flex flex-col items-center">
        <div class="avatar small"><span class="material-symbols-outlined">person</span></div>
        <div class="comment-line"></div>
      </div>
      <div class="comment-body space-y-sm">
        <div class="flex items-center gap-xs text-sm">
          <span class="font-semibold text-on-surface">${escapeHtml(shortId(comment.author_id))}</span>
          ${statusBadge}
          <span class="text-on-surface-variant">· ${formatDate(comment.created_at)}</span>
          <span class="text-on-surface-variant">· #${comment.id}</span>
        </div>
        ${contentHtml}
        <div class="flex items-center gap-md">
          <button class="engage-button" data-action="like-comment" data-comment-id="${comment.id}">
            <span class="material-symbols-outlined text-[18px]">thumb_up</span>
            <span>${comment.likes_count}</span>
          </button>
          <button class="text-sm font-semibold text-on-surface-variant hover:text-secondary" data-action="reply-comment" data-comment-id="${comment.id}" data-author-id="${escapeAttribute(comment.author_id)}">답글</button>
          <button class="text-sm font-semibold text-error hover:opacity-80" data-action="delete-comment" data-comment-id="${comment.id}">삭제</button>
        </div>
        ${(comment.replies || []).length ? `<div class="comment-replies space-y-lg">${comment.replies.map(renderComment).join("")}</div>` : ""}
      </div>
    </div>
  `;
}

async function loadComments(showToast = true) {
  if (!state.selectedPost) return;
  const comments = await run(
    () => api(`/posts/${state.selectedPost.id}/comments`),
    "댓글 목록 갱신",
    {silent: !showToast},
  );
  if (!comments) return;
  state.comments = comments;

  // AI 검증 중인 댓글이 있는지 재귀적으로 확인
  const hasPending = comments.some(hasPendingComment);
  if (hasPending) {
    if (state.toxicPollTimer) clearTimeout(state.toxicPollTimer);
    state.toxicPollTimer = setTimeout(async () => {
      if (state.selectedPost) {
        await loadComments(false);
        renderPosts();
      }
    }, 2000);
  }
}

function hasPendingComment(comment) {
  if (comment.is_toxic === null) return true;
  if (comment.replies && comment.replies.length > 0) {
    return comment.replies.some(hasPendingComment);
  }
  return false;
}

async function createPost(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const post = await run(
    () => api("/posts/", {
      method: "POST",
      auth: true,
      body: {
        title: $("postTitleInput").value.trim(),
        content: $("postContentInput").value.trim(),
        category: $("postCategoryInput").value,
      },
    }),
    "게시글 등록 완료",
  );
  if (!post) return;
  form.reset();
  elements.composer.classList.add("hidden");
  collapsePost();
  await loadPosts();
}

async function updatePost(form) {
  if (!state.selectedPost) return;
  const formData = new FormData(form);
  const updated = await run(
    () => api(`/posts/${state.selectedPost.id}`, {
      method: "PUT",
      auth: true,
      body: {
        title: String(formData.get("title")).trim(),
        content: String(formData.get("content")).trim(),
        category: String(formData.get("category")),
      },
    }),
    "게시글 수정 완료",
  );
  if (!updated) return;
  state.selectedPost = updated;
  state.editing = false;
  await loadPosts();
}

async function deletePost() {
  if (!state.selectedPost) return;
  const deleted = await run(
    () => api(`/posts/${state.selectedPost.id}`, {method: "DELETE", auth: true}),
    "게시글 삭제 완료",
  );
  if (!deleted) return;
  collapsePost();
  await loadPosts();
}

async function likePost() {
  if (!state.selectedPost) return;
  await run(
    () => api(`/posts/${state.selectedPost.id}/like`, {method: "POST", auth: true}),
    "게시글 추천 변경",
  );
  const postId = state.selectedPost.id;
  const post = await api(`/posts/${postId}`);
  state.selectedPost = post;
  await loadPosts();
}

async function createComment(form) {
  if (!state.selectedPost) return;
  const formData = new FormData(form);
  const content = String(formData.get("content")).trim();
  const comment = await run(
    () => api(`/posts/${state.selectedPost.id}/comments`, {
      method: "POST",
      auth: true,
      body: {
        content,
        parent_id: state.replyTarget ? state.replyTarget.id : null,
      },
    }),
    state.replyTarget ? "답글 등록 완료" : "댓글 등록 완료",
  );
  if (!comment) return;
  state.replyTarget = null;
  await loadComments(false);
  if (state.selectedPost) {
    const postInList = state.posts.find(p => p.id === state.selectedPost.id);
    if (postInList) postInList.comments_count = countComments(state.comments);
  }
  renderPosts();
}

async function likeComment(commentId) {
  await run(
    () => api(`/comments/${commentId}/like`, {method: "POST", auth: true}),
    "댓글 좋아요 변경",
  );
  await loadComments(false);
  renderPosts();
}

async function deleteComment(commentId) {
  await run(
    () => api(`/comments/${commentId}`, {method: "DELETE", auth: true}),
    "댓글 삭제 완료",
  );
  await loadComments(false);
  if (state.selectedPost) {
    const postInList = state.posts.find(p => p.id === state.selectedPost.id);
    if (postInList) postInList.comments_count = countComments(state.comments);
  }
  renderPosts();
}

async function summarizePost(buttonElement) {
  try {
    if (!state.selectedPost) {
      setToast("요약할 게시글이 선택되지 않았습니다.", "error");
      return;
    }
    if (state.selectedPost.content.trim().length < 200) {
      setToast("요약은 200자 이상 게시글에서만 사용할 수 있습니다.", "warn");
      return;
    }

    const clickedButton = buttonElement || document.querySelector("[data-action='summarize-post']");
    const card = clickedButton ? clickedButton.closest(".post-list-card") : null;
    const box = card ? (card.querySelector("#llmResultBox") || document.getElementById("llmResultBox")) : document.getElementById("llmResultBox");

    console.log("summarizePost starting", { clickedButton, card, box });

    if (clickedButton) {
      clickedButton.disabled = true;
      clickedButton.innerHTML = `
        <span class="material-symbols-outlined text-[18px] animate-spin">sync</span>
        요약 중...
      `;
    }
    
    if (box) {
      box.classList.remove("hidden");
      box.innerHTML = `
        <div class="flex items-center gap-sm text-primary font-semibold mb-sm animate-pulse">
          <span class="material-symbols-outlined animate-spin text-[18px]">sync</span>
          <span>AI 요약 생성 중...</span>
        </div>
        <div class="space-y-2 animate-pulse mt-sm" id="llmLoadingSkeleton">
          <div class="h-4 bg-outline-variant/30 rounded w-11/12"></div>
          <div class="h-4 bg-outline-variant/30 rounded w-full"></div>
          <div class="h-4 bg-outline-variant/30 rounded w-4/5"></div>
        </div>
      `;
    }

    setToast("요약 요청 중...", "warn");
    const targetUrl = apiPath(`/posts/${state.selectedPost.id}/summarize`);
    console.log("Fetching summary from:", targetUrl);
    const response = await fetch(targetUrl, {
      method: "POST"
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP error! status: ${response.status}`);
    }

    // Restore results layout structure
    if (box) {
      box.innerHTML = `
        <div class="flex items-center gap-sm text-primary font-semibold mb-sm">
          <span class="material-symbols-outlined">auto_awesome</span>
          <span>LLM 결과</span>
        </div>
        <pre id="llmResult" class="whitespace-pre-wrap break-words text-sm"></pre>
      `;
    }

    const freshOutput = card ? (card.querySelector("#llmResult") || document.getElementById("llmResult")) : document.getElementById("llmResult");
    if (freshOutput) freshOutput.textContent = "";

    if (response.body && typeof response.body.getReader === "function") {
      console.log("Streaming response using getReader()");
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        if (freshOutput) {
          freshOutput.textContent += chunk;
        }
      }
    } else {
      console.log("Streaming not supported or response.body is null, falling back to text()");
      const text = await response.text();
      if (freshOutput) freshOutput.textContent = text;
    }
    
    setToast("요약 완료", "ok");
  } catch (error) {
    console.error("summarizePost error:", error);
    setToast(`요약 실패: ${error.message}`, "error");
    const clickedButton = buttonElement || document.querySelector("[data-action='summarize-post']");
    const card = clickedButton ? clickedButton.closest(".post-list-card") : null;
    const box = card ? (card.querySelector("#llmResultBox") || document.getElementById("llmResultBox")) : document.getElementById("llmResultBox");
    if (box) {
      box.innerHTML = `
        <div class="flex items-center gap-sm text-error font-semibold mb-sm">
          <span class="material-symbols-outlined">report</span>
          <span>오류 발생</span>
        </div>
        <pre id="llmResult" class="whitespace-pre-wrap break-words text-sm text-error"></pre>
      `;
      const freshOutput = card ? (card.querySelector("#llmResult") || document.getElementById("llmResult")) : document.getElementById("llmResult");
      if (freshOutput) freshOutput.textContent = error.message;
    }
  } finally {
    const clickedButton = buttonElement || document.querySelector("[data-action='summarize-post']");
    if (clickedButton) {
      clickedButton.disabled = false;
      clickedButton.innerHTML = `
        <span class="material-symbols-outlined text-[18px]">summarize</span>
        요약
      `;
    }
  }
}

async function checkToxic(form) {
  const content = String(new FormData(form).get("content")).trim();
  if (!content) {
    setToast("검사할 댓글 내용을 입력하세요", "warn");
    return;
  }
  
  const resultBox = form.querySelector(".toxic-result-box");
  if (resultBox) {
    resultBox.classList.remove("hidden");
    resultBox.className = "toxic-result-box text-xs mt-sm rounded-lg p-sm border border-tertiary-fixed bg-tertiary-fixed/20 text-tertiary";
    resultBox.textContent = "AI가 댓글 유해성을 검사 중입니다...";
  }

  const result = await run(
    () => api("/llm/check-toxic", {method: "POST", body: {content}}),
    "악플 검사 완료",
  );
  
  if (!resultBox) return;

  if (!result) {
    resultBox.className = "toxic-result-box text-xs mt-sm rounded-lg p-sm border border-error-container bg-error-container/20 text-error";
    resultBox.textContent = "검사 중 오류가 발생했습니다.";
    return;
  }

  const isToxic = result.is_toxic;
  if (isToxic) {
    resultBox.className = "toxic-result-box text-xs mt-sm rounded-lg p-sm border border-error-container bg-error-container/40 text-error font-semibold";
  } else {
    resultBox.className = "toxic-result-box text-xs mt-sm rounded-lg p-sm border border-secondary-container bg-secondary-container/20 text-secondary font-semibold";
  }
  resultBox.textContent = result.analysis || (isToxic ? "⚠️ 악플 위험이 감지되었습니다." : "✅ 정상적인 댓글입니다.");
}

function setCategory(category) {
  state.category = category;
  $("breadcrumbCategory").textContent = category || "전체";
  document.querySelectorAll("[data-category]").forEach((button) => {
    button.classList.toggle("active", button.dataset.category === category);
  });
  collapsePost();
  loadPosts();
}

function setSort(sort) {
  state.sort = sort;
  $("sortSelect").value = sort;
  document.querySelectorAll("[data-sort-shortcut]").forEach((button) => {
    button.classList.toggle("active", button.dataset.sortShortcut === sort);
  });
  loadPosts();
}

function bindEvents() {
  $("statusButton").addEventListener("click", () => checkStatus(true));
  $("refreshPostsButton").addEventListener("click", loadPosts);
  $("openComposerButton").addEventListener("click", () => elements.composer.classList.remove("hidden"));
  $("rightComposerButton").addEventListener("click", () => elements.composer.classList.remove("hidden"));
  $("closeComposerButton").addEventListener("click", () => elements.composer.classList.add("hidden"));
  $("postForm").addEventListener("submit", createPost);
  $("sortSelect").addEventListener("change", (event) => setSort(event.target.value));
  $("searchInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadPosts();
  });
  elements.baseUrl.addEventListener("change", () => {
    saveSettings();
    checkStatus(true);
  });
  elements.anonymousId.addEventListener("change", saveSettings);
  document.querySelectorAll("[data-category]").forEach((button) => {
    button.addEventListener("click", () => setCategory(button.dataset.category));
  });
  document.querySelectorAll("[data-sort-shortcut]").forEach((button) => {
    button.addEventListener("click", () => setSort(button.dataset.sortShortcut));
  });

  ensurePostRail().addEventListener("click", handleRailClick);
  ensurePostRail().addEventListener("keydown", handleRailKeydown);
  ensurePostRail().addEventListener("submit", handleRailSubmit);
}

function handleRailKeydown(event) {
  const target = event.target.closest("[data-action='toggle-post']");
  if (!target || (event.key !== "Enter" && event.key !== " ")) return;
  event.preventDefault();
  openPost(Number(target.dataset.postId));
}

async function handleRailClick(event) {
  const actionTarget = event.target.closest("[data-action]");
  if (!actionTarget) return;
  const action = actionTarget.dataset.action;

  if (action === "toggle-post") return openPost(Number(actionTarget.dataset.postId));
  if (action === "edit-post") {
    state.editing = true;
    return renderPosts();
  }
  if (action === "cancel-edit") {
    state.editing = false;
    return renderPosts();
  }
  if (action === "delete-post") return deletePost();
  if (action === "like-post") return likePost();
  if (action === "focus-comment") {
    state.replyTarget = null;
    renderPosts();
    requestAnimationFrame(() => document.querySelector("[data-form='comment'] textarea")?.focus());
    return;
  }
  if (action === "refresh-comments") {
    await loadComments(true);
    return renderPosts();
  }
  if (action === "reply-comment") {
    state.replyTarget = {
      id: Number(actionTarget.dataset.commentId),
      authorId: actionTarget.dataset.authorId || "",
    };
    renderPosts();
    requestAnimationFrame(() => document.querySelector("[data-form='comment'] textarea")?.focus());
    return;
  }
  if (action === "cancel-reply") {
    state.replyTarget = null;
    return renderPosts();
  }
  if (action === "like-comment") return likeComment(Number(actionTarget.dataset.commentId));
  if (action === "delete-comment") return deleteComment(Number(actionTarget.dataset.commentId));
  if (action === "summarize-post") return summarizePost(actionTarget);
  if (action === "check-toxic") return checkToxic(actionTarget.closest("form"));
  if (action === "reveal-comment") {
    const commentId = actionTarget.dataset.commentId;
    const contentText = $(`comment-content-${commentId}`);
    const reasonText = $(`comment-reason-${commentId}`);
    if (contentText && reasonText) {
      const isBlurred = contentText.style.filter !== "none";
      if (isBlurred) {
        contentText.style.filter = "none";
        contentText.style.pointerEvents = "auto";
        contentText.classList.remove("select-none");
        reasonText.classList.remove("hidden");
        actionTarget.textContent = "숨기기";
      } else {
        contentText.style.filter = "blur(4px)";
        contentText.style.pointerEvents = "none";
        contentText.classList.add("select-none");
        reasonText.classList.add("hidden");
        actionTarget.textContent = "보기";
      }
    }
    return;
  }
}

function handleRailSubmit(event) {
  const form = event.target.closest("form[data-form]");
  if (!form) return;
  event.preventDefault();
  if (form.dataset.form === "edit-post") updatePost(form);
  if (form.dataset.form === "comment") createComment(form);
}

function countComments(comments) {
  return comments.reduce((total, comment) => total + 1 + countComments(comment.replies || []), 0);
}

function shortId(value) {
  if (!value) return "";
  return value.length > 10 ? `${value.slice(0, 8)}...` : value;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

init();
