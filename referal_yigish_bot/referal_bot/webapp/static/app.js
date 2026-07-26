const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const initData = tg.initData || "";

function apiFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Init-Data": initData,
      ...(options.headers || {}),
    },
  }).then(async (res) => {
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Xatolik yuz berdi");
    }
    return data;
  });
}

function showToast(text) {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = text;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 1800);
}

function showError(msg) {
  document.getElementById("loading").classList.add("hidden");
  document.getElementById("main-view").classList.add("hidden");
  const box = document.getElementById("error-box");
  box.classList.remove("hidden");
  document.getElementById("error-text").textContent = msg;
}

let isAdmin = false;

async function init() {
  try {
    const me = await apiFetch("/api/me");
    isAdmin = me.is_admin;
    renderProfile(me.user);

    if (isAdmin) {
      document.getElementById("admin-tab-btn").classList.remove("hidden");
    }

    const linkData = await apiFetch("/api/referral-link");
    document.getElementById("referral-link-input").value = linkData.link || "Havola topilmadi";

    document.getElementById("loading").classList.add("hidden");
    document.getElementById("main-view").classList.remove("hidden");

    setupTabs();
    setupProfileActions(linkData.link);
    loadLeaderboard();

    if (isAdmin) {
      setupAdmin();
    }
  } catch (e) {
    showError(e.message || "Yuklashda xatolik yuz berdi. Botni qaytadan oching.");
  }
}

function renderProfile(user) {
  document.getElementById("user-name").textContent = user.name || "Foydalanuvchi";
  document.getElementById("avatar-letter").textContent = (user.name || "?").charAt(0).toUpperCase();
  document.getElementById("user-rank").textContent = `Reytingdagi o'rin: ${user.rank ?? "—"}`;
  document.getElementById("stat-count").textContent = user.referral_count;

  const bonusBox = document.getElementById("bonus-progress");
  if (user.next_tier) {
    bonusBox.classList.remove("hidden");
    const remaining = user.next_tier.threshold - user.referral_count;
    document.getElementById("bonus-remaining").textContent = remaining;
    document.getElementById("bonus-reward-text").textContent = `Mukofot: ${user.next_tier.reward}`;
    const progressPct = Math.min(100, (user.referral_count / user.next_tier.threshold) * 100);
    document.getElementById("progress-fill").style.width = `${progressPct}%`;
  } else {
    bonusBox.classList.add("hidden");
  }
}

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".tab-content").forEach((sec) => sec.classList.add("hidden"));
      document.getElementById(`tab-${btn.dataset.tab}`).classList.remove("hidden");
    });
  });
}

function setupProfileActions(link) {
  document.getElementById("copy-link-btn").addEventListener("click", () => {
    navigator.clipboard.writeText(link).then(() => showToast("Havola nusxalandi!"));
  });

  document.getElementById("share-link-btn").addEventListener("click", () => {
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent("Qo'shiling!")}`;
    tg.openTelegramLink(shareUrl);
  });
}

async function loadLeaderboard() {
  try {
    const data = await apiFetch("/api/leaderboard");
    const list = document.getElementById("leaderboard-list");
    list.innerHTML = "";

    if (!data.leaderboard.length) {
      list.innerHTML = `<p class="empty-note">Hozircha reytingda hech kim yo'q.</p>`;
      return;
    }

    data.leaderboard.forEach((u, i) => {
      const rankClass = i === 0 ? "top1" : i === 1 ? "top2" : i === 2 ? "top3" : "";
      const name = u.full_name || (u.username ? `@${u.username}` : "Foydalanuvchi");
      const row = document.createElement("div");
      row.className = "leaderboard-row";
      row.innerHTML = `
        <div class="rank-badge ${rankClass}">${i + 1}</div>
        <div class="lb-name">${escapeHtml(name)}</div>
        <div class="lb-count">${u.referral_count}</div>
      `;
      list.appendChild(row);
    });
  } catch (e) {
    showToast(e.message);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------------- ADMIN ----------------

function setupAdmin() {
  loadAdminStats();
  loadChannels();
  loadTiers();

  document.getElementById("add-channel-btn").addEventListener("click", async () => {
    const input = document.getElementById("new-channel-input");
    const channel = input.value.trim();
    if (!channel) return;
    try {
      await apiFetch("/api/admin/channels", {
        method: "POST",
        body: JSON.stringify({ channel }),
      });
      input.value = "";
      showToast("Kanal qo'shildi!");
      loadChannels();
    } catch (e) {
      showToast(e.message);
    }
  });

  document.getElementById("add-tier-btn").addEventListener("click", async () => {
    const thresholdInput = document.getElementById("new-tier-threshold");
    const rewardInput = document.getElementById("new-tier-reward");
    const threshold = parseInt(thresholdInput.value, 10);
    const reward = rewardInput.value.trim();
    if (!threshold || !reward) {
      showToast("Iltimos, ikkala maydonni ham to'ldiring");
      return;
    }
    try {
      await apiFetch("/api/admin/bonus-tiers", {
        method: "POST",
        body: JSON.stringify({ threshold, reward }),
      });
      thresholdInput.value = "";
      rewardInput.value = "";
      showToast("Bonus daraja qo'shildi!");
      loadTiers();
    } catch (e) {
      showToast(e.message);
    }
  });
}

async function loadAdminStats() {
  try {
    const data = await apiFetch("/api/admin/stats");
    const box = document.getElementById("admin-stats");
    box.innerHTML = `
      <div class="stat-box"><span class="stat-num">${data.stats.total}</span><span class="stat-label">Jami foydalanuvchi</span></div>
      <div class="stat-box"><span class="stat-num">${data.stats.with_ref}</span><span class="stat-label">Taklif qilganlar</span></div>
      <div class="stat-box"><span class="stat-num">${data.stats.total_refs}</span><span class="stat-label">Jami takliflar</span></div>
    `;
  } catch (e) {
    showToast(e.message);
  }
}

async function loadChannels() {
  try {
    const data = await apiFetch("/api/admin/channels");
    const list = document.getElementById("channels-list");
    list.innerHTML = "";
    if (!data.channels.length) {
      list.innerHTML = `<p class="empty-note">Majburiy kanal qo'shilmagan.</p>`;
      return;
    }
    data.channels.forEach((ch) => {
      const row = document.createElement("div");
      row.className = "item-row";
      row.innerHTML = `<span>${escapeHtml(ch)}</span><button class="del-btn" data-channel="${escapeHtml(ch)}">✕</button>`;
      row.querySelector(".del-btn").addEventListener("click", async () => {
        try {
          await apiFetch("/api/admin/channels", {
            method: "DELETE",
            body: JSON.stringify({ channel: ch }),
          });
          loadChannels();
        } catch (e) {
          showToast(e.message);
        }
      });
      list.appendChild(row);
    });
  } catch (e) {
    showToast(e.message);
  }
}

async function loadTiers() {
  try {
    const data = await apiFetch("/api/admin/bonus-tiers");
    const list = document.getElementById("tiers-list");
    list.innerHTML = "";
    if (!data.tiers.length) {
      list.innerHTML = `<p class="empty-note">Bonus daraja qo'shilmagan.</p>`;
      return;
    }
    data.tiers.forEach((t) => {
      const row = document.createElement("div");
      row.className = "item-row";
      row.innerHTML = `<span>${t.threshold} ta → ${escapeHtml(t.reward)}</span><button class="del-btn" data-threshold="${t.threshold}">✕</button>`;
      row.querySelector(".del-btn").addEventListener("click", async () => {
        try {
          await apiFetch("/api/admin/bonus-tiers", {
            method: "DELETE",
            body: JSON.stringify({ threshold: t.threshold }),
          });
          loadTiers();
        } catch (e) {
          showToast(e.message);
        }
      });
      list.appendChild(row);
    });
  } catch (e) {
    showToast(e.message);
  }
}

init();
