// ═══════════════════════════════════════════════════════
// ADAY LİSTESİ
// ═══════════════════════════════════════════════════════
async function adaylariYukle() {
  const r = await fetch("/api/candidates");
  const adaylar = await r.json();
  const tbody = document.querySelector("#aday-tablo tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  for (const a of adaylar) {
    const tr = document.createElement("tr");
    const bool = v => v == 1 ? '<span class="yes">✓</span>' : '<span class="no">✗</span>';
    tr.innerHTML = `
      <td>${a.id}</td>
      <td>${a.isim}</td>
      <td>${a.tarih || ""}</td>
      <td>${(a.aciklama || "").slice(0, 40)}</td>
      <td>${bool(a.davet)}</td><td>${bool(a.randevu)}</td>
      <td>${bool(a.plan)}</td><td>${bool(a.kayit)}</td>
      <td>${bool(a.takip)}</td><td>${bool(a.hayir)}</td>
      <td>${bool(a.is_ariyor)}</td>
      <td><button onclick="adaySil(${a.id})" style="background:#da3633">Sil</button></td>
    `;
    tbody.appendChild(tr);
  }
}

async function adayEkle() {
  const d = {
    isim: document.getElementById("isim").value,
    tarih: document.getElementById("tarih").value,
    aciklama: document.getElementById("aciklama").value,
    davet: document.getElementById("davet").checked ? 1 : 0,
    randevu: document.getElementById("randevu").checked ? 1 : 0,
    plan: document.getElementById("plan").checked ? 1 : 0,
    kayit: document.getElementById("kayit").checked ? 1 : 0,
    takip: document.getElementById("takip").checked ? 1 : 0,
    hayir: document.getElementById("hayir").checked ? 1 : 0,
    is_ariyor: document.getElementById("is_ariyor").checked ? 1 : 0,
  };
  if (!d.isim.trim()) return alert("İsim zorunlu");
  await fetch("/api/candidates", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(d)
  });
  adaylariYukle();
}

async function excelIceAktar() {
  const not = document.getElementById("watcher-not");
  if (not) not.textContent = "⏳ okunuyor...";
  try {
    const r = await fetch("/api/excel/import", { method: "POST" });
    const d = await r.json();
    if (not) not.textContent = d.ok ? `✅ ${d.msg}` : `❌ ${d.msg}`;
    if (d.ok) adaylariYukle();
  } catch (e) {
    if (not) not.textContent = "❌ İçe aktarma hatası: " + e;
  }
}

async function adaySil(id) {
  if (!confirm("Silinsin mi?")) return;
  await fetch(`/api/candidates/${id}`, {method: "DELETE"});
  adaylariYukle();
}

// ═══════════════════════════════════════════════════════
// CHAT
// ═══════════════════════════════════════════════════════
let streamDevam = false;
let aktifController = null;

function _zamanFormatla(dbZaman) {
  // DB "YYYY-MM-DD HH:MM:SS" -> "DD.MM HH:MM"
  if (!dbZaman) return "";
  const [tarih, saat] = dbZaman.split(" ");
  if (!tarih || !saat) return dbZaman;
  const [y, ay, gun] = tarih.split("-");
  return `${gun}.${ay} ${saat.slice(0, 5)}`;
}

async function chatYukle() {
  const r = await fetch("/api/chat/gecmis");
  const msgs = await r.json();
  const kutu = document.getElementById("chat-messages");
  if (!kutu) return;
  kutu.innerHTML = "";
  for (const m of msgs) {
    mesajGoster(m.role, m.content, {
      zaman: _zamanFormatla(m.zaman),
      model: m.model,
      fallback: m.fallback,
    });
  }
  kutu.scrollTop = kutu.scrollHeight;
}

function mesajGoster(rol, icerik, opts = {}) {
  const { model = null, fallback = false, zaman = null, liveTimer = false } = opts;
  const kutu = document.getElementById("chat-messages");
  const wrap = document.createElement("div");
  wrap.className = `msg-wrap ${rol}`;

  if (rol === "assistant" && model) {
    const rozet = document.createElement("div");
    rozet.className = "model-rozet" + (fallback ? " fb" : "");
    rozet.textContent = fallback ? `🤖 ${model} · FB` : `🤖 ${model}`;
    rozet.title = fallback ? "Bu yanıt fallback modelden geldi" : "Yanıtı üreten model";
    wrap.appendChild(rozet);
  }

  const d = document.createElement("div");
  d.className = `msg ${rol}`;
  d.textContent = icerik;

  const meta = document.createElement("div");
  meta.className = "msg-meta";

  // Sol: sabit tarih/saat damgası + (varsa) canlı kronometre
  const sol = document.createElement("span");
  sol.className = "meta-left";

  const zamanEl = document.createElement("span");
  zamanEl.className = "zaman-damga";
  zamanEl.textContent = zaman !== null ? zaman : (liveTimer ? new Date().toLocaleTimeString("tr-TR", {hour: "2-digit", minute: "2-digit"}) : new Date().toLocaleTimeString("tr-TR"));
  sol.appendChild(zamanEl);

  const kronoEl = document.createElement("span");
  kronoEl.className = "kronometre";
  sol.appendChild(kronoEl);

  meta.appendChild(sol);

  // Sağ: (canlıysa) Dur + kopyala + sil
  const sag = document.createElement("span");
  sag.className = "meta-right";

  if (liveTimer) {
    const durBtn = document.createElement("button");
    durBtn.textContent = "⏹️";
    durBtn.title = "Yanıtı durdur";
    durBtn.className = "dur-btn";
    durBtn.onclick = () => { if (aktifController) aktifController.abort(); };
    sag.appendChild(durBtn);
  }

  const kopyalaBtn = document.createElement("button");
  kopyalaBtn.textContent = "📋";
  kopyalaBtn.title = "Kopyala";
  kopyalaBtn.onclick = () => {
    navigator.clipboard.writeText(d.textContent).then(() => {
      kopyalaBtn.textContent = "✅";
      setTimeout(() => kopyalaBtn.textContent = "📋", 1200);
    });
  };

  const silBtn = document.createElement("button");
  silBtn.textContent = "🗑️";
  silBtn.title = "Bu mesajı sil";
  silBtn.onclick = () => wrap.remove();

  sag.appendChild(kopyalaBtn);
  sag.appendChild(silBtn);
  meta.appendChild(sag);

  wrap.appendChild(d);
  wrap.appendChild(meta);
  kutu.appendChild(wrap);
  kutu.scrollTop = kutu.scrollHeight;
  return d;
}

async function chatGonder() {
  if (streamDevam) return;
  const inp = document.getElementById("chat-input");
  const metin = inp.value.trim();
  if (!metin) return;
  inp.value = "";

  mesajGoster("user", metin);

  const model = document.getElementById("model-select").value;
  const cevap = mesajGoster("assistant", "", { liveTimer: true, zaman: new Date().toLocaleTimeString("tr-TR") });
  const wrap = cevap.parentElement;
  const kronoEl = wrap.querySelector(".kronometre");
  const durBtn = wrap.querySelector(".dur-btn");

  // ⏱️ Kronometre başlat (zaman damgasının sağında, ayrı span)
  const baslangic = Date.now();
  const kronometre = setInterval(() => {
    const sn = ((Date.now() - baslangic) / 1000).toFixed(1);
    kronoEl.textContent = ` · ⏱️ ${sn} sn`;
  }, 100);

  streamDevam = true;
  aktifController = new AbortController();
  let durduruldu = false;

  try {
    const r = await fetch("/api/chat/stream", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({mesaj: metin, model}),
      signal: aktifController.signal,
    });
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buf += dec.decode(value, {stream: true});
      const parts = buf.split("\n\n");
      buf = parts.pop();
      for (const p of parts) {
        if (!p.startsWith("data: ")) continue;
        try {
          const obj = JSON.parse(p.slice(6));
          if (obj.done) {
            if (obj.model) {
              const rozet = document.createElement("div");
              rozet.className = "model-rozet" + (obj.fallback ? " fb" : "");
              rozet.textContent = obj.fallback ? `🤖 ${obj.model} · FB` : `🤖 ${obj.model}`;
              wrap.insertBefore(rozet, wrap.firstChild);
            }
            break;
          }
          if (obj.err) { cevap.textContent += "\n[HATA] " + obj.err; continue; }
          if (obj.t) {
            cevap.textContent += obj.t;
            document.getElementById("chat-messages").scrollTop = 999999;
          }
        } catch (e) { /* bozuk paketi atla */ }
      }
    }
  } catch (e) {
    if (e.name === "AbortError") {
      durduruldu = true;
      cevap.textContent += "\n⏹️ (durduruldu)";
    } else {
      cevap.textContent += "\n[HATA] " + e;
    }
  }

  // ⏱️ Kronometre durdur, süreyi sabitle
  clearInterval(kronometre);
  const toplamSn = ((Date.now() - baslangic) / 1000).toFixed(1);
  kronoEl.textContent = durduruldu ? ` · ⏹️ ${toplamSn} sn` : ` · ${toplamSn} sn`;
  if (durBtn) durBtn.remove();
  streamDevam = false;
  aktifController = null;
}

async function chatTemizle() {
  if (!confirm("Sohbet temizlensin mi?")) return;
  await fetch("/api/chat/temizle", {method: "POST"});
  chatYukle();
}

async function modelleriYukle() {
  const sel = document.getElementById("model-select");
  if (!sel) return;
  const modeller = ["qwen2.5:7b", "deepseek-r1:7b", "llama3.1:latest"];
  for (const m of modeller) {
    const o = document.createElement("option");
    o.value = m; o.textContent = m;
    sel.appendChild(o);
  }
}

// ═══════════════════════════════════════════════════════
// METRİKLER
// ═══════════════════════════════════════════════════════
async function metrikYukle() {
  const kutu = document.getElementById("metrik-kutulari");
  if (!kutu) return;
  const r = await fetch("/api/metrics");
  const m = await r.json();
  const etiketler = {
    toplam: "Toplam", davet: "Davet", randevu: "Randevu",
    plan: "Plan", kayit: "Kayıt", takip: "Takip",
    is_ariyor: "İş Arıyor", hayir: "Hayır"
  };
  kutu.innerHTML = "";
  for (const [k, lbl] of Object.entries(etiketler)) {
    kutu.innerHTML += `<div class="metric-card"><div class="val">${m[k] || 0}</div><div class="lbl">${lbl}</div></div>`;
  }
  const oran = document.getElementById("oranlar");
  if (oran) oran.textContent =
    `📊 Davetten Randevuya: %${m.davet_randevu_oran || 0} | Plandan Kayıta: %${m.plan_kayit_oran || 0}`;
}

// ═══════════════════════════════════════════════════════
// OLLAMA DURUM PİLİ
// ═══════════════════════════════════════════════════════
async function ollamaDurumGuncelle() {
  const pill = document.getElementById("ollama-pill");
  const cpuBadge = document.getElementById("cpu-badge");
  const gpuBadge = document.getElementById("gpu-badge");
  if (!pill) return;
  try {
    const r = await fetch("/api/ollama/durum");
    const d = await r.json();

    if (cpuBadge) {
      cpuBadge.textContent = (d.cpu_percent === null || d.cpu_percent === undefined)
        ? "CPU --%" : `CPU ${Math.round(d.cpu_percent)}%`;
    }
    if (gpuBadge) {
      gpuBadge.textContent = d.gpu_aktif ? "GPU ✅" : "GPU --";
    }

    if (!d.ok) {
      pill.textContent = "🔴 Ollama Kapalı";
      pill.className = "pill pill-off";
      return;
    }
    if (d.models && d.models.length) {
      pill.textContent = `✅ Ollama Aktif (${d.models[0].name})`;
      pill.className = "pill pill-on";
    } else {
      pill.textContent = "🟡 Ollama Boşta";
      pill.className = "pill pill-warn";
    }
  } catch (e) {
    pill.textContent = "🔴 Ollama Kapalı";
    pill.className = "pill pill-off";
  }
}

// ═══════════════════════════════════════════════════════
// SİSTEM KAPAT
// ═══════════════════════════════════════════════════════
async function sistemKapat() {
  if (!confirm("Sistem ve Ollama kapatılacak. Emin misin?")) return;
  try {
    await fetch("/api/system/kapat", { method: "POST" });
    document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-size:24px;color:#c9d1d9;background:#0d1117;text-align:center;">✅ Sistem kapatıldı.<br>Bu sekmeyi kapatabilirsiniz.</div>';
    setTimeout(() => window.close(), 2000);
  } catch (e) {
    alert("Kapatma hatası: " + e);
  }
}

// ═══════════════════════════════════════════════════════
// BAŞLANGIÇ
// ═══════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  adaylariYukle();
  chatYukle();
  modelleriYukle();
  metrikYukle();
  ollamaDurumGuncelle();
  setInterval(ollamaDurumGuncelle, 5000);
  const inp = document.getElementById("chat-input");
  if (inp) {
    inp.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatGonder();
      }
    });
  }
});