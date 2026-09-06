# Tanal Premium — yordamchi ustoz boti

Yopiq kurs uchun Telegram bot: materiallar PDF, javoblar botga yuboriladi,
baholash va daraja avtomatik. To'rt bo'lim, oldindan kiritilgan o'quvchilar
ro'yxati, takrorlanadigan kurs oqimlari.

Stack: Python 3.12 · aiogram 3 · PostgreSQL 16 · Redis · Docker Compose ·
**polling** (domen va webhook shart emas).

---

## Hozircha nima ishlaydi

| Faza | Holat | Nima kiradi |
|---|---|---|
| 1. Skelet, kirish, oqimlar | ✅ | Docker, migratsiyalar, `/start` → raqam → avtomatik ochilish, `AccessMiddleware`, oqimlar, `access_until` |
| 2. Kontent importi va PDF nusxalash | ✅ | 4 ta Excel importi (qator raqamli xatolar bilan), fayl yuklash → `file_id`, ism yozilgan PDF + kesh |
| 3. Javob dvigateli | ✅ | Parser · tasdiqlash ekrani · normalizatsiya · baholash · daraja · «noto'g'ri baholandi» signali · **95 avtotest** |
| 4. Grammatika | ✅ | Mavzular, qulf (`requires`), urinishlar cheklovi, mocklar |
| 5. O'qish & Eshitish | ✅ | Reading/Listening mocklari, audio va qayta tinglash |
| 6. Yozish (Gemini) | ✅ | Topshiriq banki, ko'p varaqli insho rasmi, structured JSON, kunlik limit, tuzatilgan matn |
| 7. Speaking (Gemini) | ✅ | Part 1/2/3, cue card + 1 daqiqa taymer, `.ogg` to'g'ridan-to'g'ri, transkript va band, namuna javob |
| 8. Yordamchi ustoz | ✅ (1–2 daraja) | Tag tahlili, natijadan keyingi tavsiya, yakshanba xulosasi, eslatma |
| 9. Statistika | ✅ (asosiy) | O'quvchi natijalari, `/stats`, `/sets`, `/cohorts`, e'lon |
| 10. Deploy | ✅ | Docker Compose, backup skripti |
| 11. Beta | ⏳ | Kontent tayyor bo'lgach |

---

## Ishga tushirish

### 1. Tayyorgarlik

```bash
cp .env.example .env
```

`.env` da to'ldiriladi:

- `BOT_TOKEN` — @BotFather dan
- `ADMIN_CHAT_ID` — yopiq admin guruhi ID si (bot o'sha guruhda admin bo'lsin)
- `ADMIN_IDS` — sizning Telegram ID(lar)ingiz, vergul bilan
- `POSTGRES_PASSWORD` — o'zingiznikini qo'ying

### 2. VPS da

```bash
docker compose up -d --build
```

Migratsiyalar konteyner ichida avtomatik ishlaydi (`alembic upgrade head`).
Loglar:

```bash
docker compose logs -f bot
```

### 3. Kompyuterda ishlab chiqish

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q
.venv/bin/ruff check .
```

---

## Excel shablonlari

```bash
python -m tools.make_templates
```

`templates/` papkasida to'rtta fayl paydo bo'ladi — har birida namuna qatorlar
va `izoh` varag'i:

| Fayl | Nima uchun |
|---|---|
| `sets.xlsx` | Har bir test/mockning pasporti: kod, bo'lim, savollar soni, urinishlar, `reveal`, fayl nomlari |
| `answer_keys.xlsx` | Javob kaliti: `set_code · q_no · answer · accept_also · tag` |
| `levels.xlsx` | Daraja shkalasi — koddan emas, shu yerdan |
| `students.xlsx` | Kimga ruxsat: ism, telefon, oqim |
| `ai_tasks.xlsx` | Writing topshiriqlari va speaking savollari banki |

**Excel — haqiqat manbai.** Bazani qo'lda tahrirlamang; o'zgarish kerak bo'lsa
Excelni yangilab, qayta import qiling.

### Import tartibi

1. `students.xlsx` → o'quvchilar va oqimlar
2. `sets.xlsx` → to'plamlar
3. `answer_keys.xlsx` → kalit (avval `sets` bo'lishi shart)
4. `levels.xlsx` → daraja shkalasi
5. `ai_tasks.xlsx` → writing/speaking banki
6. `/upload` → PDF, audio va Task 1 grafiklarini yuborish

Fayl nomi `sets.xlsx` dagi `pdf_file` / `audio_file` / `theory_file` bilan
**aynan** mos kelsin. Bo'shliq va o'zbek harflari ishlatilmasin:
`03_present-perfect_test.pdf` yaxshi, `3-mavzu test.pdf` yomon.

Import bir butun: bitta xato qator bo'lsa hech nima yozilmaydi va xabar
qator raqami bilan qaytadi —
`answer_keys, 214-qator: GR-M07 uchun 33-savol ikki marta`.

---

## Admin buyruqlari

| Buyruq | Nima qiladi |
|---|---|
| `/help` | Buyruqlar ro'yxati |
| `/import` | Excel yuborish rejimi (fayl nomi bo'yicha turi aniqlanadi) |
| `/upload` | PDF/audio/rasm yuklash rejimi, tugagach `/done` |
| `/demo` | Demo kontent yozish. `/demo +998901234567` — sinov o'quvchisini ham qo'shadi |
| `/ai` | AI rejimi (demo yoki model nomi), kunlik limit, bugungi so'rov va tokenlar |
| `/sets` | To'plamlar holati: qaysi fayl yuklanmagan, kalit to'liqmi |
| `/stats` | O'quvchilar, urinishlar, o'rtacha ball, eng ko'p xato qilinadigan teglar |
| `/cohorts` | Oqimlar va ulardagi o'quvchilar soni |
| `/preview GR-T03` | O'quvchi ko'radigan ekranni sinash |
| `/broadcast` | E'lon (tasdiqlashdan keyin, navbat bilan yuboriladi) |

Adminga avtomatik keladigan signallar: ro'yxatda yo'q raqam · hisob ulashish
urinishi · «⚠️ Noto'g'ri baholandi» tugmasi.

---

## Javob dvigateli

Botning yuragi — `app/services/answer_engine/`. Bir modul to'rt bo'limga
xizmat qiladi.

**Parser** (`parser.py`) quyidagilarning hammasini tushunadi:

```
1a 2b 3c 4d 5a        1. A  2. B        1-A, 2-B        a b c d
1) moon               2) TRUE           3) 15 minutes   4) NOT GIVEN
```

Javob bir necha xabarda kelsa yig'iladi; `1a 2b 3c` dan keyin `2. d` yuborilsa
2-savol javobi yangilanadi.

**Tasdiqlash** — hech qachon darhol baholanmaydi. O'quvchi bot uni qanday
tushunganini ko'radi va tuzatadi.

**Normalizatsiya** (`normalize.py`) — katta/kichik harf, ortiqcha bo'shliq,
tinish belgilari, artikllar, bo'shliq/defis (`car park` = `carpark`),
raqam ↔ so'z (`15` = `fifteen`), `T` = `TRUE`, `NG` = `NOT GIVEN`,
plus kalitdagi `accept_also`.

**Natija** — `sets.reveal` ga qarab ikki xil: mavzu testida to'g'ri javoblar
ko'rsatiladi, mockda faqat ball, daraja va xato raqamlari.

O'quvchi yuborgan asl matn `attempts.submitted_raw` da o'zgarishsiz saqlanadi —
nizo chiqqanda aynan nima yozganini ko'rasiz.

Sinash:

```bash
pytest -q
```

---

## Yozish va Speaking (Gemini)

### Demo rejimi — hozir sinash uchun

`GEMINI_API_KEY` bo'sh bo'lsa (yoki `AI_DEMO=true`) bot **demo rejimida**
ishlaydi: butun oqim — topshiriq tanlash, rasm yig'ish, «⏳ Tekshirilyapti…»,
natija ekrani, tugmalar, kunlik limit, bazaga yozish — haqiqiy holatdagidek
ishlaydi, faqat baho namunaviy va tepasida `🧪 DEMO rejimi` yozuvi turadi.
Gemini chaqirilmaydi, pul ketmaydi.

Kalit qo'yilgach hech narsani o'zgartirish shart emas — bot avtomatik
haqiqiy rejimga o'tadi.

### Nol daqiqada sinab ko'rish

Admin sifatida botda:

```
/demo +998901234567
```

Demo to'plamlar (grammatika mavzu testi, mock, reading), javob kalitlari,
daraja shkalasi va AI topshiriqlari yoziladi; raqam berilsa o'sha o'quvchi
ham qo'shiladi. Keyin `/start` → raqamni yuborish → menyu.

Konteynerdan tashqarida: `python -m tools.seed_demo --phone +998901234567`

### Yozish oqimi

Task 1 / Task 2 / o'z topshirig'i → topshiriq matni (Task 1 bo'lsa grafik
rasmi bilan) → insho varaqlarini ketma-ket suratga olib yuborish →
«✅ Tayyor» → bitta so'rovda hammasi Gemini'ga boradi (alohida OCR kerak emas)
→ band, to'rt kriteriya, raqamlangan xatolar, kuchli tomon, «nimani tuzatish»
va alohida tugmada tuzatilgan to'liq matn.

### Speaking oqimi

Part 1 / 2 / 3 → bankdan tasodifiy savol. Part 2 da cue card va 1 daqiqalik
tayyorgarlik taymeri (vaqt tugagach bot eslatadi) → ovozli xabar → transkript,
to'rt kriteriya, nutq tezligi va uzun pauzalar, 3 ta aniq tavsiya, alohida
tugmada 7.5 darajali namuna javob.

Telegram ovozi `.ogg` (Opus) — Gemini uni to'g'ridan-to'g'ri qabul qiladi,
konvertatsiya yo'q. 15 soniyadan qisqa va 3 daqiqadan uzun yozuvlar
baholanmaydi (`SPEAKING_MIN_SEC` / `SPEAKING_MAX_SEC`).

### Nazorat

- Kunlik limit: `AI_DAILY_LIMIT` yoki `settings` jadvalidagi `ai_daily_limit`
  (bazadagisi ustun) — har natija ostida qolgan soni ko'rsatiladi
- Har so'rov `ai_submissions` ga yoziladi: `model`, `prompt_version`, `scores`,
  `feedback`, `tokens_in/out` — xarajat hisobi ham, promptni yaxshilaganda
  eski va yangi baholarni solishtirish ham shundan
- Har natija ostida: *«Bu AI bahosi, real imtihon natijasi emas»*

## Yordamchi ustoz

`answer_keys.tag` ustuni to'ldirilgan bo'lsa bot xatolarni mavzuga bog'laydi:

```
💡 4 ta xatoning 3 tasi (1, 3, 5) — for / since.
   Shu mavzuni qayta ko'rib chiqing.
```

Har yakshanba 19:00 da haftalik xulosa, chorshanba 18:00 da bir haftadan beri
kirmaganlarga eslatma (`app/scheduler.py`).

---

## Backup

```bash
crontab -e
0 3 * * * /opt/tanal/scripts/backup.sh >> /var/log/tanal-backup.log 2>&1
```

Skript `pg_dump` ni yopiq Telegram kanaliga yuboradi — tafsilotlari
`scripts/backup.sh` ichida.

---

## Papka tuzilishi

```
app/
  config.py          .env dan sozlamalar
  enums.py           bo'limlar, holatlar
  texts.py           barcha o'zbekcha matnlar bir joyda
  states.py          FSM holatlari
  scheduler.py       haftalik xulosa, eslatma
  db/
    models.py        10 jadval
    repo.py          barcha so'rovlar
  middlewares/       sessiya · kirish nazorati · rate limit
  handlers/
    start.py         /start va telefon orqali kirish
    menu.py          bo'limlar
    sets.py          to'plam kartasi, material yuborish
    answers.py       yig'ish → tasdiq → baholash → natija
    writing.py       insho rasmlari → Gemini
    speaking.py      ovozli javob → Gemini
    admin/           import · upload · statistika · demo · e'lon
  services/
    answer_engine/   parser · normalize · grader · levels
    ai/              schemas · prompts · client (Gemini + demo) · service · render
    demo_seed.py     demo kontent
    importer.py      Excel → baza
    pdf_stamp.py     ism yozilgan PDF nusxasi
    files.py         material yuborish + file_id keshi
    tutor.py         tavsiyalar
    weekly.py        haftalik xulosa
migrations/          alembic
tools/               Excel shablon generatori, demo seeder
tests/               122 avtotest
```

---

## Keyingi qadam

1. Faza 0 — kontent: PDFlar va to'ldirilgan Excellar (loyihaning kritik yo'li)
2. Gemini kaliti va 10 ta insho / 10 ta speaking javobi bilan **kalibrovka**:
   o'zingiz baholab, model bilan solishtiring; farq 1 banddan katta bo'lsa
   `app/services/ai/prompts.py` ni to'g'rilab, `prompt_version` ni oshiring
3. Faza 11 — beta guruh
