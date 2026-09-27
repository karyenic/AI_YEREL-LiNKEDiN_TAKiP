/* ============================================================
   ADAY LİSTESİ
   ============================================================ */

let aktifAdayId = null;


function htmlGuvenli(metin) {
  const div = document.createElement("div");
  div.textContent = metin == null ? "" : String(metin);
  return div.innerHTML;
}


async function adaylariYukle() {

  const r = await fetch("/api/candidates");
  const adaylar = await r.json();

  const tbody = document.querySelector("#aday-tablo tbody");

  if (!tbody) return;

  tbody.innerHTML = "";

  for (const a of adaylar) {

    const tr = document.createElement("tr");
    tr.className = "aday-satir";

    const bool = v =>
      v == 1
        ? '<span class="yes">✓</span>'
        : '<span class="no">✗</span>';

    tr.innerHTML = `
      <td>${htmlGuvenli(a.id)}</td>

      <td>
        <strong>${htmlGuvenli(a.isim)}</strong>
      </td>

      <td>${htmlGuvenli(a.tarih || "")}</td>

      <td title="${htmlGuvenli(a.aciklama || "")}">
        ${htmlGuvenli((a.aciklama || "").slice(0, 60))}
      </td>

      <td>${bool(a.davet)}</td>
      <td>${bool(a.randevu)}</td>
      <td>${bool(a.plan)}</td>
      <td>${bool(a.kayit)}</td>
      <td>${bool(a.takip)}</td>
      <td>${bool(a.hayir)}</td>
      <td>${bool(a.is_ariyor)}</td>

      <td>
        <button
          onclick="event.stopPropagation(); adayKartiAc(${a.id})"
          style="background:#1f6feb;padding:7px 11px;font-size:13px;"
        >
          👤 Kart
        </button>
      </td>
    `;

    tr.addEventListener("click", () => {
      adayKartiAc(a.id);
    });

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

  if (!d.isim.trim()) {
    alert("İsim zorunlu");
    return;
  }

  const r = await fetch(
    "/api/candidates",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(d)
    }
  );

  const sonuc = await r.json();

  if (!sonuc.ok) {
    alert("Aday eklenemedi.");
    return;
  }

  document.getElementById("isim").value = "";
  document.getElementById("tarih").value = "";
  document.getElementById("aciklama").value = "";

  adaylariYukle();
}


/* ============================================================
   ADAY KARTI
   ============================================================ */

async function adayKartiAc(adayId) {

  aktifAdayId = adayId;

  const modal = document.getElementById("aday-modal");

  if (!modal) return;

  modal.classList.remove("hidden");

  document.body.style.overflow = "hidden";

  document.getElementById("kart-isim").textContent = "Yükleniyor...";
  document.getElementById("aday-gecmis").innerHTML =
    '<div class="gecmis-bos">⏳ Aday bilgileri okunuyor...</div>';

  try {

    const r = await fetch(
      `/api/candidates/${adayId}`
    );

    const sonuc = await r.json();

    if (!r.ok || !sonuc.ok) {
      throw new Error(
        sonuc.error || "Aday bilgileri alınamadı."
      );
    }

    adayKartiDoldur(sonuc.data);

  } catch (e) {

    document.getElementById("kart-isim").textContent =
      "Hata";

    document.getElementById("aday-gecmis").innerHTML =
      `<div class="gecmis-bos">❌ ${htmlGuvenli(e.message)}</div>`;
  }
}


function adayKartiDoldur(data) {

  document.getElementById("kart-isim").textContent =
    data.isim || "Aday";

  document.getElementById("kart-telefon").value =
    data.telefon || "";

  document.getElementById("kart-email").value =
    data.email || "";

  document.getElementById("kart-adres").value =
    data.adres || "";

  document.getElementById("kart-durum").textContent =
    data.durum || "🟢 Aktif";

  adayGecmisiGoster(data.gecmis || []);

  gelismeFormuKapat();
}


function adayKartiKapat() {

  const modal = document.getElementById("aday-modal");

  if (!modal) return;

  modal.classList.add("hidden");

  document.body.style.overflow = "";

  aktifAdayId = null;

  gelismeFormuKapat();
}


function adayGecmisiGoster(gecmis) {

  const kutu = document.getElementById("aday-gecmis");

  if (!kutu) return;

  kutu.innerHTML = "";

  if (!gecmis.length) {

    kutu.innerHTML =
      '<div class="gecmis-bos">Henüz gelişme kaydı bulunmuyor.</div>';

    return;
  }

  for (const olay of gecmis) {

    const item = document.createElement("div");
    item.className = "gecmis-item";

    const tip = olay.olay_tipi || "Not";
    const tarih = olay.tarih || "";

    item.innerHTML = `
      <div class="gecmis-ust">

        <span class="gecmis-tip">
          ${htmlGuvenli(tip)}
        </span>

        <span class="gecmis-tarih">
          ${htmlGuvenli(tarih)}
        </span>

      </div>

      <div class="gecmis-metin">
        ${htmlGuvenli(olay.olay_metni || "Açıklama yok.")}
      </div>

      ${
        olay.durum
          ? `<span class="gecmis-durum">${htmlGuvenli(olay.durum)}</span>`
          : ""
      }
    `;

    kutu.appendChild(item);
  }
}


/* ============================================================
   PROFİL KAYDET
   ============================================================ */

async function adayProfilKaydet() {

  if (!aktifAdayId) return;

  const telefon =
    document.getElementById("kart-telefon").value.trim();

  const email =
    document.getElementById("kart-email").value.trim();

  const adres =
    document.getElementById("kart-adres").value.trim();

  try {

    const r = await fetch(
      `/api/candidates/${aktifAdayId}/profil`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          telefon,
          email,
          adres
        })
      }
    );

    const sonuc = await r.json();

    if (!r.ok || !sonuc.ok) {
      throw new Error(
        sonuc.error || "Bilgiler kaydedilemedi."
      );
    }

    alert("Aday bilgileri kaydedildi.");

  } catch (e) {

    alert("Kayıt hatası: " + e.message);
  }
}


/* ============================================================
   GELİŞME FORMU
   ============================================================ */

function bugununTarihiniAyarla() {

  const input =
    document.getElementById("gelisme-tarih");

  if (!input) return;

  if (input.value) return;

  const d = new Date();

  const yyyy = d.getFullYear();

  const mm = String(
    d.getMonth() + 1
  ).padStart(2, "0");

  const dd = String(
    d.getDate()
  ).padStart(2, "0");

  input.value =
    `${yyyy}-${mm}-${dd}`;
}


function gelismeFormuAc() {

  const form =
    document.getElementById("gelisme-formu");

  if (!form) return;

  form.classList.remove("hidden");

  bugununTarihiniAyarla();

  setTimeout(() => {

    const alan =
      document.getElementById("gelisme-aciklama");

    if (alan) alan.focus();

  }, 50);
}


function gelismeFormuKapat() {

  const form =
    document.getElementById("gelisme-formu");

  if (!form) return;

  form.classList.add("hidden");

  const aciklama =
    document.getElementById("gelisme-aciklama");

  if (aciklama) {
    aciklama.value = "";
  }

  const mesaj =
    document.getElementById("gelisme-mesaj");

  if (mesaj) {
    mesaj.textContent = "";
  }

  const durum =
    document.getElementById("gelisme-durum");

  if (durum) {
    durum.value = "";
  }
}


async function gelismeKaydet() {

  if (!aktifAdayId) {
    alert("Önce bir aday kartı açın.");
    return;
  }

  const tarih =
    document.getElementById("gelisme-tarih").value;

  const olay_tipi =
    document.getElementById("gelisme-tip").value;

  const olay_metni =
    document.getElementById("gelisme-aciklama").value.trim();

  const durum =
    document.getElementById("gelisme-durum").value;

  if (!olay_metni) {

    alert(
      "Lütfen gelişmeyi / görüşme notunu yazın."
    );

    return;
  }

  const mesaj =
    document.getElementById("gelisme-mesaj");

  if (mesaj) {
    mesaj.textContent =
      "⏳ Kaydediliyor...";
  }

  try {

    const r = await fetch(
      `/api/candidates/${aktifAdayId}/gelisme`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          tarih,
          olay_tipi,
          olay_metni,
          durum
        })
      }
    );

    const sonuc = await r.json();

    if (!r.ok || !sonuc.ok) {
      throw new Error(
        sonuc.error || "Gelişme kaydedilemedi."
      );
    }

    if (mesaj) {
      mesaj.textContent =
        "✅ Gelişme kaydedildi.";
    }

    document.getElementById(
      "gelisme-aciklama"
    ).value = "";

    document.getElementById(
      "gelisme-durum"
    ).value = "";

    await adayKartiAc(aktifAdayId);

    setTimeout(() => {
      gelismeFormuAc();
    }, 100);

  } catch (e) {

    if (mesaj) {
      mesaj.textContent =
        "❌ " + e.message;
    }
  }
}


/* ============================================================
   ESC ile aday kartını kapat
   ============================================================ */

document.addEventListener(
  "keydown",
  e => {

    if (e.key === "Escape") {

      const modal =
        document.getElementById("aday-modal");

      if (
        modal &&
        !modal.classList.contains("hidden")
      ) {
        adayKartiKapat();
      }
    }
  }
);


/* ============================================================
   EXCEL
   ============================================================ */

async function excelIceAktar() {

  const not =
    document.getElementById("watcher-not");

  if (not) {
    not.textContent = "⏳ okunuyor...";
  }

  try {

    const r = await fetch(
      "/api/excel/import",
      {
        method: "POST"
      }
    );

    const d = await r.json();

    if (not) {
      not.textContent =
        d.ok
          ? `✅ ${d.msg}`
          : `❌ ${d.msg}`;
    }

    if (d.ok) {
      adaylariYukle();
    }

  } catch (e) {

    if (not) {
      not.textContent =
        "❌ İçe aktarma hatası: " + e;
    }
  }
}


async function adaySil(id) {

  if (!confirm("Silinsin mi?")) return;

  await fetch(
    `/api/candidates/${id}`,
    {
      method: "DELETE"
    }
  );

  adaylariYukle();
}


/* ============================================================
   CHAT
   ============================================================ */

let streamDevam = false;
let aktifController = null;


function _zamanFormatla(dbZaman) {

  if (!dbZaman) return "";

  const [tarih, saat] =
    dbZaman.split(" ");

  if (!tarih || !saat) {
    return dbZaman;
  }

  const [y, ay, gun] =
    tarih.split("-");

  return `${gun}.${ay} ${saat.slice(0, 5)}`;
}


async function chatYukle() {

  const r =
    await fetch("/api/chat/gecmis");

  const msgs =
    await r.json();

  const kutu =
    document.getElementById("chat-messages");

  if (!kutu) return;

  kutu.innerHTML = "";

  for (const m of msgs) {

    mesajGoster(
      m.role,
      m.content,
      {
        zaman: _zamanFormatla(m.zaman),
        model: m.model,
        fallback: m.fallback
      }
    );
  }

  kutu.scrollTop =
    kutu.scrollHeight;
}


function mesajGoster(
  rol,
  icerik,
  opts = {}
) {

  const {
    model = null,
    fallback = false,
    zaman = null,
    liveTimer = false
  } = opts;

  const kutu =
    document.getElementById(
      "chat-messages"
    );

  const wrap =
    document.createElement("div");

  wrap.className =
    `msg-wrap ${rol}`;

  if (
    rol === "assistant" &&
    model
  ) {

    const rozet =
      document.createElement("div");

    rozet.className =
      "model-rozet" +
      (fallback ? " fb" : "");

    rozet.textContent =
      fallback
        ? `🤖 ${model} · FB`
        : `🤖 ${model}`;

    rozet.title =
      fallback
        ? "Bu yanıt fallback modelden geldi"
        : "Yanıtı üreten model";

    wrap.appendChild(rozet);
  }

  const d =
    document.createElement("div");

  d.className =
    `msg ${rol}`;

  d.textContent =
    icerik;

  const meta =
    document.createElement("div");

  meta.className =
    "msg-meta";

  const sol =
    document.createElement("span");

  sol.className =
    "meta-left";

  const zamanEl =
    document.createElement("span");

  zamanEl.className =
    "zaman-damga";

  zamanEl.textContent =
    zaman !== null
      ? zaman
      : (
          liveTimer
            ? new Date().toLocaleTimeString(
                "tr-TR",
                {
                  hour: "2-digit",
                  minute: "2-digit"
                }
              )
            : new Date().toLocaleTimeString(
                "tr-TR"
              )
        );

  sol.appendChild(zamanEl);

  const kronoEl =
    document.createElement("span");

  kronoEl.className =
    "kronometre";

  sol.appendChild(kronoEl);

  meta.appendChild(sol);

  const sag =
    document.createElement("span");

  sag.className =
    "meta-right";

  if (liveTimer) {

    const durBtn =
      document.createElement("button");

    durBtn.textContent =
      "⏹️";

    durBtn.title =
      "Yanıtı durdur";

    durBtn.className =
      "dur-btn";

    durBtn.onclick = () => {

      if (aktifController) {
        aktifController.abort();
      }
    };

    sag.appendChild(durBtn);
  }

  const kopyalaBtn =
    document.createElement("button");

  kopyalaBtn.textContent =
    "📋";

  kopyalaBtn.title =
    "Kopyala";

  kopyalaBtn.onclick = () => {

    navigator.clipboard
      .writeText(d.textContent)
      .then(() => {

        kopyalaBtn.textContent =
          "✅";

        setTimeout(
          () =>
            kopyalaBtn.textContent =
              "📋",
          1200
        );
      });
  };

  const silBtn =
    document.createElement("button");

  silBtn.textContent =
    "🗑️";

  silBtn.title =
    "Bu mesajı sil";

  silBtn.onclick = () =>
    wrap.remove();

  sag.appendChild(kopyalaBtn);
  sag.appendChild(silBtn);

  meta.appendChild(sag);

  wrap.appendChild(d);
  wrap.appendChild(meta);

  kutu.appendChild(wrap);

  kutu.scrollTop =
    kutu.scrollHeight;

  return d;
}


async function chatGonder() {

  if (streamDevam) return;

  const inp =
    document.getElementById(
      "chat-input"
    );

  const metin =
    inp.value.trim();

  if (!metin) return;

  inp.value = "";

  mesajGoster(
    "user",
    metin
  );

  const model =
    document.getElementById(
      "model-select"
    ).value;

  const cevap =
    mesajGoster(
      "assistant",
      "",
      {
        liveTimer: true,
        zaman:
          new Date().toLocaleTimeString(
            "tr-TR"
          )
      }
    );

  const wrap =
    cevap.parentElement;

  const kronoEl =
    wrap.querySelector(
      ".kronometre"
    );

  const durBtn =
    wrap.querySelector(
      ".dur-btn"
    );

  const baslangic =
    Date.now();

  const kronometre =
    setInterval(
      () => {

        const sn =
          (
            (Date.now() - baslangic) /
            1000
          ).toFixed(1);

        kronoEl.textContent =
          ` · ⏱️ ${sn} sn`;

      },
      100
    );

  streamDevam = true;

  aktifController =
    new AbortController();

  let durduruldu = false;

  try {

    const r =
      await fetch(
        "/api/chat/stream",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json"
          },
          body: JSON.stringify({
            mesaj: metin,
            model
          }),
          signal:
            aktifController.signal
        }
      );

    const reader =
      r.body.getReader();

    const dec =
      new TextDecoder();

    let buf = "";

    while (true) {

      const {
        done,
        value
      } = await reader.read();

      if (done) break;

      buf += dec.decode(
        value,
        {
          stream: true
        }
      );

      const parts =
        buf.split("\n\n");

      buf =
        parts.pop();

      for (const p of parts) {

        if (
          !p.startsWith(
            "data: "
          )
        ) {
          continue;
        }

        try {

          const obj =
            JSON.parse(
              p.slice(6)
            );

          if (obj.done) {

            if (obj.model) {

              const rozet =
                document.createElement(
                  "div"
                );

              rozet.className =
                "model-rozet" +
                (
                  obj.fallback
                    ? " fb"
                    : ""
                );

              rozet.textContent =
                obj.fallback
                  ? `🤖 ${obj.model} · FB`
                  : `🤖 ${obj.model}`;

              wrap.insertBefore(
                rozet,
                wrap.firstChild
              );
            }

            break;
          }

          if (obj.err) {

            cevap.textContent +=
              "\n[HATA] " +
              obj.err;

            continue;
          }

          if (obj.t) {

            cevap.textContent +=
              obj.t;

            document.getElementById(
              "chat-messages"
            ).scrollTop =
              999999;
          }

        } catch (e) {
          /* Bozuk SSE paketi atlanır. */
        }
      }
    }

  } catch (e) {

    if (
      e.name ===
      "AbortError"
    ) {

      durduruldu = true;

      cevap.textContent +=
        "\n⏹️ (durduruldu)";

    } else {

      cevap.textContent +=
        "\n[HATA] " + e;
    }
  }

  clearInterval(
    kronometre
  );

  const toplamSn =
    (
      (Date.now() - baslangic) /
      1000
    ).toFixed(1);

  kronoEl.textContent =
    durduruldu
      ? ` · ⏹️ ${toplamSn} sn`
      : ` · ${toplamSn} sn`;

  if (durBtn) {
    durBtn.remove();
  }

  streamDevam = false;

  aktifController = null;
}


async function chatTemizle() {

  if (!confirm("Sohbet temizlensin mi?")) {
    return;
  }

  await fetch(
    "/api/chat/temizle",
    {
      method: "POST"
    }
  );

  chatYukle();
}


async function modelleriYukle() {

  const sel =
    document.getElementById(
      "model-select"
    );

  if (!sel) return;

  const modeller = [
    "qwen2.5:7b",
    "deepseek-r1:7b",
    "llama3.1:latest"
  ];

  for (const m of modeller) {

    const o =
      document.createElement(
        "option"
      );

    o.value = m;
    o.textContent = m;

    sel.appendChild(o);
  }
}


/* ============================================================
   METRİKLER
   ============================================================ */

async function metrikYukle() {

  const kutu =
    document.getElementById(
      "metrik-kutulari"
    );

  if (!kutu) return;

  const r =
    await fetch(
      "/api/metrics"
    );

  const m =
    await r.json();

  const etiketler = {
    toplam: "Toplam",
    davet: "Davet",
    randevu: "Randevu",
    plan: "Plan",
    kayit: "Kayıt",
    takip: "Takip",
    is_ariyor: "İş Arıyor",
    hayir: "Hayır"
  };

  kutu.innerHTML = "";

  for (
    const [k, lbl]
    of Object.entries(
      etiketler
    )
  ) {

    kutu.innerHTML +=
      `
      <div class="metric-card">
        <div class="val">
          ${m[k] || 0}
        </div>
        <div class="lbl">
          ${lbl}
        </div>
      </div>
      `;
  }

  const oran =
    document.getElementById(
      "oranlar"
    );

  if (oran) {

    oran.textContent =
      `📊 Davetten Randevuya: %${m.davet_randevu_oran || 0} | Plandan Kayıta: %${m.plan_kayit_oran || 0}`;
  }
}


/* ============================================================
   OLLAMA DURUM PİLİ
   ============================================================ */

async function ollamaDurumGuncelle() {

  const pill =
    document.getElementById(
      "ollama-pill"
    );

  const cpuBadge =
    document.getElementById(
      "cpu-badge"
    );

  const gpuBadge =
    document.getElementById(
      "gpu-badge"
    );

  if (!pill) return;

  try {

    const r =
      await fetch(
        "/api/ollama/durum"
      );

    const d =
      await r.json();

    if (cpuBadge) {

      cpuBadge.textContent =
        (
          d.cpu_percent === null ||
          d.cpu_percent === undefined
        )
          ? "CPU --%"
          : `CPU ${Math.round(d.cpu_percent)}%`;
    }

    if (gpuBadge) {

      gpuBadge.textContent =
        d.gpu_aktif
          ? "GPU ✅"
          : "GPU --";
    }

    if (!d.ok) {

      pill.textContent =
        "🔴 Ollama Kapalı";

      pill.className =
        "pill pill-off";

      return;
    }

    if (
      d.models &&
      d.models.length
    ) {

      pill.textContent =
        `✅ Ollama Aktif (${d.models[0].name})`;

      pill.className =
        "pill pill-on";

    } else {

      pill.textContent =
        "🟡 Ollama Boşta";

      pill.className =
        "pill pill-warn";
    }

  } catch (e) {

    pill.textContent =
      "🔴 Ollama Kapalı";

    pill.className =
      "pill pill-off";
  }
}


/* ============================================================
   SİSTEM KAPAT
   ============================================================ */

async function sistemKapat() {

  if (
    !confirm(
      "Sistem ve Ollama kapatılacak. Emin misin?"
    )
  ) {
    return;
  }

  try {

    await fetch(
      "/api/system/kapat",
      {
        method: "POST"
      }
    );

    document.body.innerHTML =
      `
      <div
        style="
          display:flex;
          align-items:center;
          justify-content:center;
          height:100vh;
          font-size:24px;
          color:#c9d1d9;
          background:#0d1117;
          text-align:center;
        "
      >
        ✅ Sistem kapatıldı.<br>
        Bu sekmeyi kapatabilirsiniz.
      </div>
      `;

    setTimeout(
      () => window.close(),
      2000
    );

  } catch (e) {

    alert(
      "Kapatma hatası: " + e
    );
  }
}


/* ============================================================
   BAŞLANGIÇ
   ============================================================ */

document.addEventListener(
  "DOMContentLoaded",
  () => {

    adaylariYukle();
    chatYukle();
    modelleriYukle();
    metrikYukle();
    ollamaDurumGuncelle();

    setInterval(
      ollamaDurumGuncelle,
      5000
    );

    const inp =
      document.getElementById(
        "chat-input"
      );

    if (inp) {

      inp.addEventListener(
        "keydown",
        e => {

          if (
            e.key === "Enter" &&
            !e.shiftKey
          ) {

            e.preventDefault();

            chatGonder();
          }
        }
      );
    }
  }
);
