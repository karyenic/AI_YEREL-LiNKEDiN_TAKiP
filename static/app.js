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

  const urlParams = new URLSearchParams(window.location.search);
  const metrikFiltresi = urlParams.get("metrik");

  const goruntulenecekAdaylar =
    metrikFiltresi &&
    metrikFiltresi !== "toplam" &&
    metrikFiltresi !== ""
      ? adaylar.filter(
          a => Number(a[metrikFiltresi] || 0) === 1
        )
      : adaylar;
  let siraNo = 0;
  for (const a of goruntulenecekAdaylar) {
    siraNo++;

    const tr = document.createElement("tr");
    tr.className = "aday-satir";
    tr.dataset.adayId = String(a.id);

    const bool = v =>
      v == 1
        ? '<span class="yes">✓</span>'
        : '<span class="no">✗</span>';

    tr.innerHTML = `
      <td>${siraNo}</td>

            <td>
        ${a.linkedin_url 
          ? `<a href="${htmlGuvenli(a.linkedin_url)}" 
                target="_blank" 
                onclick="event.stopPropagation();"
                class="isim-link"
                title="LinkedIn profilini aç">${htmlGuvenli(a.isim)}</a>`
          : `<strong>${htmlGuvenli(a.isim)}</strong>`}
      </td>

      <td>${htmlGuvenli(a.tarih || "")}</td>

      <td title="${htmlGuvenli(aciklamaTemizle(a.aciklama))}">
        <span class="durum-top" title="${htmlGuvenli(durumEtiketi(a.durum))}">${durumTopp(a.durum)}</span>${htmlGuvenli(aciklamaTemizle(a.aciklama).slice(0, 60))}
      </td>

      <td>${bool(a.davet)}</td>
      <td>${bool(a.randevu)}</td>
      <td>${bool(a.plan)}</td>
      <td>${bool(a.kayit)}</td>
      <td>${bool(a.takip)}</td>
      <td>${bool(a.hayir)}</td>
      <td>${bool(a.is_ariyor)}</td>

      <td style="white-space:nowrap;">
        
      </td>

      <td style="white-space:nowrap; text-align:right;">
        <button
          onclick="event.stopPropagation(); adaySilOnay(${a.id}, '${htmlGuvenli(a.isim).replace(/'/g, "\\'")}')"
          style="background:#da3633;padding:7px 11px;font-size:13px;"
          title="Adayı Sil"
        >
          🗑️ Sil
        </button>
      </td>
    `;

    tr.addEventListener("click", (e) => {
      if (e.target.closest("a") || e.target.closest("button")) {
        return;
      }
      adayKartiAc(Number(tr.dataset.adayId));
    });

    tbody.appendChild(tr);
  }

  tbody.querySelectorAll(".btn-sil").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      adaySilOnay(
        Number(btn.dataset.adayId),
        btn.dataset.adayIsim || ""
      );
    });
  });
}


async function adayEkle() {

  const d = {
    isim: document.getElementById("isim").value,
    tarih: (function() {
      const d = new Date();
      return String(d.getDate()).padStart(2, "0") + " " +
             String(d.getMonth() + 1).padStart(2, "0") + " " +
             String(d.getFullYear()).slice(-2);
    })(),
    aciklama: document.getElementById("aciklama").value,

    davet: 0,
    randevu: 0,
    plan: 0,
    kayit: 0,
    takip: 0,
    hayir: 0,
    is_ariyor: 0,
    durum: document.getElementById("yeni-aday-durum") ? document.getElementById("yeni-aday-durum").value : "🆕 Yeni",
    linkedin_url: (document.getElementById("linkedin-url")?.value || "").trim() || null,
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

  linkedinLinkGuncelle(data.linkedin_url || "");
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
          durum,
          // Checkbox'lar (kart gelisme formundan)
          davet: document.getElementById("gelisme-davet")?.checked ? 1 : 0,
          plan: document.getElementById("gelisme-plan")?.checked ? 1 : 0,
          kayit: document.getElementById("gelisme-kayit")?.checked ? 1 : 0,
          hayir: document.getElementById("gelisme-hayir")?.checked ? 1 : 0
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

    // Listeyi ANINDA yenile (durum degisti)
    if (typeof adaylariYukle === "function") {
      adaylariYukle();
    }

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

    // Filtre dropdown degerini al
  const filtreEl =
    document.getElementById("kategori-filtre");

  const filtre =
    filtreEl ? filtreEl.value : "hepsi";

  kutu.innerHTML = "";

  for (const m of msgs) {

    // Kategori filtresi
    const mesajKat =
      m.kategori || "sohbet";

    if (
      filtre !== "hepsi" &&
      mesajKat !== filtre
    ) {
      continue;
    }

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
      document.createElement(
        "div"
      );

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
          ),
        model: model === "otomatik" ? "otomatik (seçiliyor...)" : model
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
    let rozetGuncellendi = false;

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

          if (obj.model && !rozetGuncellendi) {
            const mevcutRozet = wrap.querySelector(".model-rozet");
            if (mevcutRozet) {
              mevcutRozet.className =
                "model-rozet" +
                (obj.fallback ? " fb" : "");
              mevcutRozet.textContent =
                obj.fallback
                  ? `🤖 ${obj.model} · FB`
                  : `🤖 ${obj.model}`;
              rozetGuncellendi = true;
            }
          }

          if (obj.done) {
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

            const _kutu = document.getElementById("chat-messages");
            if (_kutu) {
              const _enAltMi =
                (_kutu.scrollHeight - _kutu.scrollTop - _kutu.clientHeight) < 80;
              if (_enAltMi) {
                _kutu.scrollTop = _kutu.scrollHeight;
              }
            }
          }

        } catch (e) {
          /* Bozuk paket atlanır */
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

  sel.innerHTML = "";

  const otomatikOpt = document.createElement("option");
  otomatikOpt.value = "otomatik";
  otomatikOpt.textContent = "🤖 Otomatik (Akıllı Seçim)";
  sel.appendChild(otomatikOpt);

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

  try {

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

      const deger =
        Number(m[k] || 0);

      const aktifSinif =
        deger > 0
          ? " metric-active"
          : "";

      kutu.innerHTML +=
        `
        <button
          type="button"
          class="metric-card${aktifSinif}"
          onclick="raporMetrikAc('${k}')"
          title="${lbl} adaylarını göster"
        >
          <div class="val">
            ${deger}
          </div>

          <div class="lbl">
            ${lbl}
          </div>

          <div class="metric-hint">
            Görüntüle →
          </div>
        </button>
        `;
    }

    const oran =
      document.getElementById(
        "oranlar"
      );

    if (oran) {

      oran.textContent =
        `📊 Kaba→Davet: %${m.oran_kabadan_davete ?? 0} · Davet→Randevu: %${m.oran_davetten_randevuya ?? m.davet_randevu_oran ?? 0} · Randevu→Plan: %${m.oran_randevudan_plana ?? 0} · Plan→Kayıt: %${m.oran_plandan_kayda ?? m.plan_kayit_oran ?? 0} · Uçtan uca: %${m.oran_uctan_uca ?? 0}`;
    }

  } catch (e) {

    console.error(
      "Metrik yükleme hatası:",
      e
    );
  }
}


function raporMetrikAc(metrik) {

  if (!metrik) return;

  window.location.href =
    `/?metrik=${encodeURIComponent(metrik)}`;
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

    temaUygula();
    gunlukNotYukle();

    adaylariYukle();
    chatYukle();
    modelleriYukle();
    metrikYukle();
    ollamaDurumGuncelle();
    excelBildirimGoster();
    linkedinUrlIzle();

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

/* ============================================================
   TEMA
   ============================================================ */

function temaUygula() {

  const kayitliTema =
    localStorage.getItem(
      "linkedin_tema"
    ) || "dark";

  document.documentElement.setAttribute(
    "data-theme",
    kayitliTema
  );

  const buton =
    document.getElementById(
      "theme-toggle"
    );

  if (buton) {

    buton.textContent =
      kayitliTema === "dark"
        ? "☀️"
        : "🌙";

    buton.title =
      kayitliTema === "dark"
        ? "Açık temaya geç"
        : "Koyu temaya geç";
  }
}


function temaDegistir() {

  const mevcut =
    document.documentElement.getAttribute(
      "data-theme"
    ) || "dark";

  const yeni =
    mevcut === "dark"
      ? "light"
      : "dark";

  localStorage.setItem(
    "linkedin_tema",
    yeni
  );

  document.documentElement.setAttribute(
    "data-theme",
    yeni
  );

  const buton =
    document.getElementById(
      "theme-toggle"
    );

  if (buton) {

    buton.textContent =
      yeni === "dark"
        ? "☀️"
        : "🌙";

    buton.title =
      yeni === "dark"
        ? "Açık temaya geç"
        : "Koyu temaya geç";
  }
}


/* ============================================================
   GÜNLÜK RAPOR NOTU
   ============================================================ */

function gunlukAnahtar() {

  const d =
    new Date();

  const yyyy =
    d.getFullYear();

  const mm =
    String(
      d.getMonth() + 1
    ).padStart(2, "0");

  const dd =
    String(
      d.getDate()
    ).padStart(2, "0");

  return `linkedin_gunluk_${yyyy}-${mm}-${dd}`;
}


function gunlukNotYukle() {

  const alan =
    document.getElementById(
      "gunluk-not"
    );

  if (!alan) return;

  const kayit =
    localStorage.getItem(
      gunlukAnahtar()
    );

  if (kayit) {

    alan.value =
      kayit;

    const durum =
      document.getElementById(
        "gunluk-not-durum"
      );

    if (durum) {

      durum.textContent =
        "📓 Bugünkü kayıt yüklendi.";
    }
  }
}


function gunlukNotKaydet() {

  const alan =
    document.getElementById(
      "gunluk-not"
    );

  if (!alan) return;

  const metin =
    alan.value.trim();

  const durum =
    document.getElementById(
      "gunluk-not-durum"
    );

  if (!metin) {

    if (durum) {

      durum.textContent =
        "⚠️ Kaydedilecek bir not yok.";
    }

    return;
  }

  localStorage.setItem(
    gunlukAnahtar(),
    metin
  );

  if (durum) {

    durum.textContent =
      "✅ Bugünkü çalışma notu kaydedildi.";
  }
}


function gunlukNotTemizle() {

  const alan =
    document.getElementById(
      "gunluk-not"
    );

  if (alan) {

    alan.value = "";
    alan.focus();
  }

  const durum =
    document.getElementById(
      "gunluk-not-durum"
    );

  if (durum) {

    durum.textContent =
      "";
  }
}


/* ============================================================
   AI ÖNERİ ALANI
   ============================================================ */

async function aiOneriHazirla() {

  const kutu =
    document.getElementById(
      "ai-onerileri"
    );

  if (!kutu) return;

  kutu.innerHTML = `
    <div class="ai-placeholder">
      <div class="ai-icon">⏳</div>
      <div>
        <strong>Analiz ediliyor...</strong>
        <p>Model huni verisini ve temassızlık sürelerini değerlendiriyor, birkaç saniye sürebilir.</p>
      </div>
    </div>
  `;

  try {
    const r = await fetch("/api/metrics/ozet", { method: "POST" });
    const d = await r.json();

    if (!d.ozet) {
      kutu.innerHTML = `
        <div class="ai-placeholder">
          <div class="ai-icon">⚠️</div>
          <div><strong>Öneri alınamadı.</strong></div>
        </div>
      `;
      return;
    }

    const satirlar = d.ozet.split("\n").filter(s => s.trim() !== "");
    let html = "";
    for (const satir of satirlar) {
      const baslikEslesme = satir.match(/^\*\*(.+?)\*\*:?\s*(.*)$/);
      if (baslikEslesme) {
        html += `<h4 class="ai-oneri-baslik">${baslikEslesme[1]}</h4>`;
        if (baslikEslesme[2]) html += `<p>${baslikEslesme[2]}</p>`;
      } else {
        html += `<p>${satir.replace(/^-\s*/, "• ")}</p>`;
      }
    }
    kutu.innerHTML = `<div class="ai-oneri-metin">${html}</div>`;
  } catch (e) {
    kutu.innerHTML = `
      <div class="ai-placeholder">
        <div class="ai-icon">⚠️</div>
        <div><strong>Hata:</strong> ${e}</div>
      </div>
    `;
  }
}

// ============================================================
// ADAY ARAMA
// ============================================================
function adayAra() {
    const arama = document
        .getElementById("aday-ara")
        .value
        .toLowerCase()
        .trim();

    const satirlar = document.querySelectorAll(
        "#aday-tablo tbody tr"
    );

    let gorunen = 0;

    satirlar.forEach(satir => {
        const metin = satir.textContent.toLowerCase();

        if (arama === "" || metin.includes(arama)) {
            satir.style.display = "";
            gorunen++;
        } else {
            satir.style.display = "none";
        }
    });
}

// ============================================================
// SUTUN SIRALAMA
// ============================================================
let _siralaDurum = { kolon: null, yon: "asc" };

function sirala(kolon) {
  const tbody = document.querySelector("#aday-tablo tbody");
  if (!tbody) return;

  const satirlar = Array.from(tbody.querySelectorAll("tr"));
  if (satirlar.length === 0) return;

  let yon = "asc";
  if (_siralaDurum.kolon === kolon) {
    yon = _siralaDurum.yon === "asc" ? "desc" : "asc";
  }
  _siralaDurum = { kolon, yon };

  const kolonMap = {
    "id": 0, "isim": 1, "tarih": 2, "aciklama": 3,
    "davet": 4, "randevu": 5, "plan": 6, "kayit": 7,
    "takip": 8, "hayir": 9, "is_ariyor": 10
  };

  const idx = kolonMap[kolon];
  if (idx === undefined) return;

  const boolKolonlar = ["davet", "randevu", "plan", "kayit", "takip", "hayir", "is_ariyor"];

  function _tarihParse(s) {
    s = (s || "").trim();
    const m = s.match(/^(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})$/);
    if (!m) return 0;
    let gun = parseInt(m[1]);
    let ay = parseInt(m[2]);
    let yil = parseInt(m[3]);
    if (yil < 100) yil += 2000;
    return new Date(yil, ay - 1, gun).getTime();
  }

  function _norm(s) {
    return (s || "").toString().toLowerCase()
      .replace(/\u0130/g, "i")
      .replace(/\u0131/g, "i")
      .replace(/\u00e7/g, "c")
      .replace(/\u015f/g, "s")
      .replace(/\u011f/g, "g")
      .replace(/\u00fc/g, "u")
      .replace(/\u00f6/g, "o");
  }

  satirlar.sort((a, b) => {
    const aCell = a.children[idx];
    const bCell = b.children[idx];
    if (!aCell || !bCell) return 0;

    const aTxt = aCell.textContent.trim();
    const bTxt = bCell.textContent.trim();

    let aVal, bVal;
    if (kolon === "tarih") {
      aVal = _tarihParse(aTxt);
      bVal = _tarihParse(bTxt);
    } else if (boolKolonlar.includes(kolon)) {
      aVal = aTxt.includes("✓") ? 1 : 0;
      bVal = bTxt.includes("✓") ? 1 : 0;
    } else if (kolon === "id") {
      aVal = parseInt(aTxt) || 0;
      bVal = parseInt(bTxt) || 0;
    } else {
      aVal = _norm(aTxt);
      bVal = _norm(bTxt);
    }

    if (aVal < bVal) return yon === "asc" ? -1 : 1;
    if (aVal > bVal) return yon === "asc" ? 1 : -1;
    return 0;
  });

  satirlar.forEach(tr => tbody.appendChild(tr));

  const ths = document.querySelectorAll("#aday-tablo thead th");
  ths.forEach((th, i) => {
    th.textContent = th.textContent.replace(/\s*[\^v▲▼]\s*$/, "").trim();
    if (i === idx) {
      th.textContent += yon === "asc" ? " ▲" : " ▼";
    }
  });
}


async function excelBildirimGoster() {
  try {
    const r = await fetch("/api/excel/durum");
    if (!r.ok) return;
    const d = await r.json();

    if (!d.zaman) return;

    const main = document.querySelector("main");
    if (!main) return;

    const eski = document.querySelector(".excel-bildirim");
    if (eski) eski.remove();

    const b = document.createElement("div");
    b.className = "excel-bildirim " + (d.eklenen > 0 ? "yeni" : "bilgi");

    let metin;
    if (d.eklenen > 0) {
      metin = `📥 <strong>${d.eklenen} yeni aday eklendi</strong>`;
      if (d.atlanan > 0) {
        metin += `, ${d.atlanan} zaten mevcuttu`;
      }
    } else {
      metin = `✅ Excel tarandı, yeni aday yok (${d.atlanan} mevcut)`;
    }

    b.innerHTML = `
      <span>${metin} <span class="zaman">(${d.zaman})</span></span>
      <button onclick="this.parentElement.remove()" title="Kapat">✕</button>
    `;

    main.insertBefore(b, main.firstChild);

    setTimeout(() => {
      if (b.parentElement) {
        b.style.opacity = "0";
        setTimeout(() => b.remove(), 300);
      }
    }, 10000);

  } catch (e) {
    console.error("Bildirim hatası:", e);
  }
}

function _siraNumaralariniYenile() {
  const satirlar = document.querySelectorAll("#aday-tablo tbody tr");
  let no = 0;
  for (const tr of satirlar) {
    no++;
    const ilkHucre = tr.querySelector("td");
    if (ilkHucre) {
      ilkHucre.textContent = String(no);
    }
  }
}

async function adaySilOnay(id, isim) {
  const emin = confirm(
    `"${isim}" adlı adayı silmek istediğinizden emin misiniz?\n\n` +
    `Bu işlem GERİ ALINAMAZ!`
  );

  if (!emin) return;

  try {
    const r = await fetch(`/api/candidates/${id}`, {
      method: "DELETE"
    });

    const d = await r.json();

    if (d.ok) {
      const satirlar = document.querySelectorAll("#aday-tablo tbody tr");
      for (const tr of satirlar) {
        if (tr.dataset.adayId === String(id)) {
          tr.style.transition = "opacity 0.3s, transform 0.3s";
          tr.style.opacity = "0";
          tr.style.transform = "translateX(-20px)";
          setTimeout(() => {
            adaylariYukle();
          }, 300);;
          break;
        }
      }
    } else {
      alert("❌ Silme başarısız!");
    }
  } catch (e) {
    console.error("Silme hatası:", e);
  }
}


function yazdirmaModu() {
  const tarihEl = document.getElementById("print-tarih");
  if (tarihEl) {
    const simdi = new Date();
    const formatli = simdi.toLocaleString("tr-TR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
    tarihEl.textContent = "Yazdırma tarihi: " + formatli;
  }

  const eskiBaslik = document.title;
  const simdi = new Date();
  const tarihKisa = simdi.toLocaleDateString("tr-TR").replace(/\./g, "-");
  document.title = `LinkedIn_Aday_Listesi_${tarihKisa}`;

  window.print();

  setTimeout(() => {
    document.title = eskiBaslik;
  }, 1500);
}


document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "p") {
    e.preventDefault();
    yazdirmaModu();
  }
});


function keepModalAc() {
  const modal = document.getElementById("keep-modal");
  if (modal) {
    modal.classList.remove("hidden");
    const ta = document.getElementById("keep-metin");
    if (ta) {
      ta.value = "";
      ta.focus();
    }
    const onizleme = document.getElementById("keep-onizleme");
    if (onizleme) onizleme.classList.add("hidden");
  }
}

function keepModalKapat() {
  const modal = document.getElementById("keep-modal");
  if (modal) modal.classList.add("hidden");
}

async function keepOnizle() {
  const metin = document.getElementById("keep-metin").value.trim();
  if (!metin) {
    alert("Lütfen Keep notunu yapıştırın.");
    return;
  }

  try {
    const r = await fetch("/api/keep/parse", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({metin})
    });
    const d = await r.json();

    if (!d.ok) {
      alert("❌ " + (d.error || "Parse hatası"));
      return;
    }

    const kutu = document.getElementById("keep-onizleme-icerik");
    kutu.innerHTML = `
      <div style="margin-bottom:8px;">
        <strong>Toplam:</strong> ${d.toplam} aday
        &nbsp;|&nbsp;
        <span style="color:#3fb950;">🟢 ${d.yesil} yeşil</span>
        &nbsp;|&nbsp;
        <span style="color:#d29922;">🟡 ${d.sari} sarı</span>
      </div>
      <div style="max-height:200px;overflow-y:auto;font-size:13px;line-height:1.6;">
        ${d.adaylar.map(a => `
          <div style="padding:4px 0;border-bottom:1px solid #21262d;">
            <strong>${a.isim}</strong>${a.durum === 'yeşil' ? '🟢' : a.durum === 'sarı' ? '🟡' : ''}
            <span style="color:#8b949e;"> — ${a.aciklama}</span>
          </div>
        `).join("")}
      </div>
    `;
    document.getElementById("keep-onizleme").classList.remove("hidden");

  } catch (e) {
    alert("❌ Hata: " + e);
  }
}

async function keepAktar() {
  const metin = document.getElementById("keep-metin").value.trim();
  if (!metin) {
    alert("Lütfen Keep notunu yapıştırın.");
    return;
  }

  const btn = event.target;
  btn.disabled = true;
  btn.textContent = "⏳ Aktarılıyor...";

  try {
    const r = await fetch("/api/keep/import", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({metin})
    });
    const d = await r.json();

    if (!d.ok) {
      alert("❌ " + (d.error || "Aktarma hatası"));
      return;
    }

    alert("✅ " + d.mesaj);
    keepModalKapat();

    if (typeof adaylariYukle === "function") adaylariYukle();

  } catch (e) {
    alert("❌ Hata: " + e);
  } finally {
    btn.disabled = false;
    btn.textContent = "✅ Aktar";
  }
}


function linkedinLinkGuncelle(url) {
  const input = document.getElementById("kart-linkedin-input");
  const link = document.getElementById("kart-linkedin-link");
  const yok = document.getElementById("kart-linkedin-yok");

  if (!link || !yok) return;

  if (input) {
    input.value = url || "";
  }

  if (url && url.trim()) {
    link.href = url;
    link.style.display = "inline-block";
    yok.style.display = "none";
  } else {
    link.style.display = "none";
    yok.style.display = "block";
  }
}


function isimUrlCikar(url) {
  if (!url) return "";

  const match = url.match(/linkedin\.com\/in\/([^\/\?#]+)/i);
  if (!match) return "";

  let isim = match[1].replace(/-/g, " ");

  try { isim = decodeURIComponent(isim); } catch (e) {}

  isim = isim
    .split(" ")
    .filter(w => w.length > 0)
    .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");

  return isim;
}


function linkedinUrlIzle() {
  const urlInput = document.getElementById("linkedin-url");
  const isimInput = document.getElementById("isim");

  if (!urlInput || !isimInput) return;

  urlInput.addEventListener("change", () => {
    const url = urlInput.value.trim();
    if (!url) return;

    const yeniIsim = isimUrlCikar(url);
    if (yeniIsim) {
      isimInput.value = yeniIsim;
    }
  });

  urlInput.addEventListener("blur", () => {
    const url = urlInput.value.trim();
    if (!url) return;

    const yeniIsim = isimUrlCikar(url);
    if (yeniIsim && !isimInput.value.trim()) {
      isimInput.value = yeniIsim;
    }
  });
}


function durumTopp(durum) {
  if (!durum) return "🆕";
  const d = String(durum).trim();

  if (d.includes("Yeni") || d.includes("🆕")) return "🆕";
  if (d.includes("Değerlendirilecek") || d.includes("⚪")) return "⚪";
  if (d.includes("Sıcak") || d.includes("🔥")) return "🔥";
  if (d.includes("Aktif") || d.includes("🟢")) return "🟢";
  if (d.includes("Takip") || d.includes("🔔")) return "🔔";
  if (d.includes("SG") || d.includes("🎓")) return "🎓";
  if (d.includes("DeepFreeze") || d.includes("❄")) return "❄️";
  if (d.includes("Olumsuz") || d.includes("🔴")) return "🔴";

  return "🆕";
}

function durumEtiketi(durum) {
  if (!durum) return "🆕 Yeni";
  return String(durum).trim();
}


function aciklamaTemizle(metin) {
  if (!metin) return "";
  let s = String(metin).trim();

  const emojiler = /^(🆕|⚪|🟢|🟡|🔴|🔥|❄️|❄|⚫|🟠|🟨|🟩|🟥|🟧)\s*/u;

  let onceki = "";
  let sayac = 0;
  while (s !== onceki && sayac < 5) {
    onceki = s;
    s = s.replace(emojiler, "").trim();
    sayac++;
  }

  return s;
}

function otomatikStatuBelirle() {
  const olayTipi = document.getElementById("gelisme-tip").value;
  const durumSecici = document.getElementById("gelisme-durum");

  if (!durumSecici) return;

  if (olayTipi === "Plan") {
    durumSecici.value = "🔔 Takip";
  } 
  else if (olayTipi === "Kayıt") {
    durumSecici.value = "🚀 Kayıt Sonrası Başlatma";
  } 
  else if (olayTipi === "Hayır") {
    durumSecici.value = "❄️ DeepFreeze";
  }
}