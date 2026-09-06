"""Botning barcha matnlari bir joyda — o'zgartirish uchun kod titkilash shart emas."""

from __future__ import annotations

# --- kirish ----------------------------------------------------------------

WELCOME = (
    "Assalomu alaykum!\n\n"
    "Bu — kurs materiallari va testlari uchun yopiq bot.\n"
    "Ro'yxatdan o'tish uchun pastdagi tugma orqali telefon raqamingizni yuboring."
)

ASK_CONTACT_BUTTON = "📱 Raqamni yuborish"

CONTACT_NOT_OWN = (
    "Iltimos, <b>o'zingizning</b> raqamingizni yuboring — tugmadan foydalaning."
)

CONTACT_BAD_FORMAT = (
    "Raqamni o'qiy olmadim. Iltimos, pastdagi tugma orqali qayta yuboring."
)

ACCESS_OK = (
    "✅ Xush kelibsiz, {name}!\n"
    "Oqim: <b>{cohort}</b>\n\n"
    "Quyidagi bo'limlardan birini tanlang."
)

ACCESS_NOT_FOUND = (
    "❌ Raqamingiz ro'yxatda topilmadi.\n\n"
    "Agar kursga yozilgan bo'lsangiz, admin bilan bog'laning — "
    "raqamingizni ro'yxatga qo'shib qo'yadi."
)

ACCESS_TAKEN = (
    "⚠️ Bu raqam allaqachon boshqa Telegram akkauntga biriktirilgan.\n\n"
    "Bir raqam — bir akkaunt. Admin bilan bog'laning."
)

ACCESS_BLOCKED = "⛔️ Kirish yopilgan. Admin bilan bog'laning."

ACCESS_EXPIRED = (
    "⏳ Kursga kirish muddati tugagan ({until}).\n"
    "Davom ettirish uchun admin bilan bog'laning."
)

NEED_REGISTRATION = "Avval ro'yxatdan o'ting: /start"

# --- menyu -----------------------------------------------------------------

MAIN_MENU = "Bo'limni tanlang:"

MENU_GRAMMAR = "📐 Grammatika"
MENU_READING_LISTENING = "📖 O'qish & Eshitish"
MENU_WRITING = "✍️ Yozish"
MENU_SPEAKING = "🎙 Speaking"
MENU_STATS = "📊 Natijalarim"

GRAMMAR_MENU = "📐 Grammatika — nimadan boshlaymiz?"
GRAMMAR_TOPICS = "A. Mavzular"
GRAMMAR_MOCKS = "B. Mocklar"

RL_MENU = "📖 Qaysi bo'lim?"
SECTION_EMPTY = "Bu bo'limda hozircha material yo'q."

# --- to'plam / test --------------------------------------------------------

SET_LOCKED = "🔒 Avval «{required}» ni yakunlang."
SET_NO_ATTEMPTS = (
    "Bu test uchun urinishlar tugagan ({allowed} tadan {used} ta ishlatilgan)."
)

SET_CARD = (
    "<b>{title}</b>\n"
    "Savollar soni: {total_q}\n"
    "Urinish: {used}/{allowed}\n\n"
    "{extra}"
)

SEND_ANSWERS_HINT = (
    "Testni yechib bo'lgach javoblaringizni yuboring.\n\n"
    "Qanday yozsangiz ham tushunaman:\n"
    "<code>1a 2b 3c</code>  ·  <code>1. A  2. B</code>  ·  <code>1-A, 2-B</code>\n"
    "So'zli javoblar uchun: <code>1) moon</code>, <code>2) TRUE</code>\n\n"
    "Bir necha xabarda yuborsangiz ham bo'ladi — hammasini yig'ib boraman.\n"
    "Tugagach <b>«✅ Tugatdim»</b> tugmasini bosing."
)

ANSWERS_COLLECTED = "Qabul qilindi: {filled}/{total} ta javob.\nYana yuborishingiz mumkin."

ANSWERS_EMPTY = (
    "Bu xabardan javob ajratib ololmadim.\n"
    "Namuna: <code>1a 2b 3c</code> yoki <code>1) moon</code>"
)

CONFIRM_HEADER = "<b>Javoblaringizni shunday o'qidim:</b>"
CONFIRM_MISSING = "⚠️ Topilmagan savollar: {nos}"
CONFIRM_OUT_OF_RANGE = "⚠️ Testda yo'q raqamlar e'tiborsiz qoldirildi: {nos}"
CONFIRM_ASK = "Hammasi to'g'rimi?"
CONFIRM_NOTHING = "Hali birorta javob yubormadingiz."

BTN_FINISH = "✅ Tugatdim"
BTN_CONFIRM = "✅ To'g'ri, tekshir"
BTN_REDO = "✏️ Qayta yuboraman"
BTN_CANCEL = "❌ Bekor qilish"
BTN_THEORY = "📄 Nazariya"
BTN_TEST = "📝 Test"
BTN_PDF = "📄 Savol varaqasi"
BTN_AUDIO = "🎧 Audio"
BTN_AUDIO_AGAIN = "🔁 Qayta tinglash"
BTN_RETRY = "🔁 Qayta yechish"
BTN_STATS = "📊 Natijalarim"
BTN_REPORT = "⚠️ Noto'g'ri baholandi"
BTN_BACK = "⬅️ Orqaga"

CANCELLED = "Bekor qilindi."

# --- natija ----------------------------------------------------------------

RESULT_TOPIC_HEADER = "<b>{title}</b>\n<b>{score} / {total} · {percent}%</b>"
RESULT_MOCK_HEADER = "<b>{title}</b>\n<b>{score} / {total} · {level}</b>"

RESULT_WRONG_LIST = "❌ Xato: {nos}"
RESULT_NO_WRONG = "🎉 Barcha javoblar to'g'ri!"
RESULT_COMPARE_UP = "Oldingi urinish: {prev}/{total}{prev_level}\n<b>+{delta} ball</b> 📈"
RESULT_COMPARE_DOWN = "Oldingi urinish: {prev}/{total}{prev_level}\n<b>{delta} ball</b> 📉"
RESULT_COMPARE_SAME = "Oldingi urinish: {prev}/{total} — o'zgarish yo'q."

REPORT_SENT = "Rahmat, adminga yubordim. Tekshirib chiqamiz."

# --- yozish (Gemini) -------------------------------------------------------

WRITING_MENU = "✍️ <b>Yozish</b>\n\nTopshiriq turini tanlang:"
WRITING_PICK_TASK = "Topshiriqni tanlang:"
WRITING_TASK_CARD = "<b>{title}</b>\n\n{prompt}\n\n{hint}"
WRITING_SEND_PHOTOS = (
    "📷 Insho rasmini yuboring.\n"
    "Bir necha varaq bo'lsa ketma-ket yuboring, tugagach <b>«✅ Tayyor»</b>."
)
WRITING_PAGE_ADDED = "Qabul qilindi: {count}-varaq."
WRITING_NO_PAGES = "Hali birorta varaq yubormadingiz."
WRITING_TOO_MANY_PAGES = "Ko'pi bilan {limit} ta varaq qabul qilinadi."
WRITING_NEED_PHOTO = "Inshoni <b>rasm</b> qilib yuboring (matn emas)."
WRITING_CHECKING = "⏳ Tekshirilyapti… (30–60 soniya)"
WRITING_UNREADABLE = (
    "Rasmdagi matnni o'qib bo'lmadi yoki bu insho emas.\n"
    "Yorug'roq va tik holatda suratga olib, qayta yuboring."
)
BTN_WRITING_DONE = "✅ Tayyor"
BTN_CORRECTED_TEXT = "📄 Tuzatilgan to'liq matn"
BTN_OWN_TASK = "📝 O'z topshirig'im"
WRITING_OWN_TASK_ASK = "O'z topshirig'ingiz matnini yuboring."

# --- speaking (Gemini) -----------------------------------------------------

SPEAKING_MENU = "🎙 <b>Speaking</b>\n\nQaysi qism?"
SPEAKING_QUESTION = "<b>Part {part}</b>\n\n{question}"
SPEAKING_CUE_CARD = "<b>Part 2 — cue card</b>\n\n{question}\n\n{cue}"
SPEAKING_PREP = (
    "⏱ <b>1 daqiqa tayyorgarlik.</b>\n"
    "Vaqt tugagach ovozli javob yuboring (2 daqiqagacha)."
)
SPEAKING_PREP_OVER = "⏱ Tayyorgarlik vaqti tugadi — javobni yozib yuboring."
SPEAKING_SEND_VOICE = "🎙 Ovozli xabar yuboring."
SPEAKING_NEED_VOICE = "Javobni <b>ovozli xabar</b> qilib yuboring."
SPEAKING_TOO_SHORT = (
    "Yozuv juda qisqa ({sec} soniya). Kamida {min_sec} soniya gapiring — "
    "aks holda adolatli baholab bo'lmaydi."
)
SPEAKING_TOO_LONG = "Yozuv juda uzun ({sec} soniya). {max_sec} soniyagacha bo'lsin."
SPEAKING_CHECKING = "⏳ Tinglanyapti… (30–60 soniya)"
SPEAKING_INSUFFICIENT = (
    "Yozuv tushunarsiz yoki juda qisqa bo'lgani uchun baholanmadi. "
    "Tinchroq joyda, mikrofonga yaqinroq gapirib qayta urinib ko'ring."
)
BTN_MODEL_ANSWER = "🔊 Namuna javob"
BTN_NEXT_QUESTION = "➡️ Boshqa savol"

# --- AI umumiy -------------------------------------------------------------

AI_EMPTY_BANK = (
    "Bu bo'lim uchun topshiriqlar hali kiritilmagan. Admin bilan bog'laning."
)
AI_LIMIT_REACHED = (
    "Bugungi AI tekshiruvlari limiti tugadi ({limit} ta).\n"
    "Ertaga davom ettirasiz."
)
AI_LEFT_TODAY = "Bugun qolgan tekshiruvlar: {left}/{limit}"
AI_FAILED = (
    "Tekshiruv bajarilmadi — xizmat vaqtincha javob bermadi.\n"
    "Birozdan keyin qayta urinib ko'ring."
)
AI_DEMO_HINT = "🧪 Demo rejimi yoqilgan — natija namunaviy."

# --- statistika ------------------------------------------------------------

STATS_EMPTY = "Hali birorta test yechmadingiz."
STATS_HEADER = "📊 <b>Natijalaringiz</b>"

# --- xizmat ----------------------------------------------------------------

MAINTENANCE = "🛠 Bot vaqtincha texnik ishlar rejimida. Birozdan keyin urinib ko'ring."
GENERIC_ERROR = "Kutilmagan xatolik. Admin xabardor qilindi, birozdan keyin urinib ko'ring."
FILE_MISSING = "Bu material hali yuklanmagan. Admin bilan bog'laning."
NOT_FOR_YOU = "Bu tugma sizniki emas."

# --- admin -----------------------------------------------------------------

ADMIN_ONLY = "Bu buyruq faqat adminlar uchun."

ADMIN_HELP = (
    "<b>Admin buyruqlari</b>\n\n"
    "/import — Excel yuborish rejimi "
    "(sets · answer_keys · levels · students · ai_tasks)\n"
    "/upload — PDF, audio va topshiriq rasmlarini yuklash rejimi\n"
    "/demo — demo kontent yozish (ixtiyoriy: /demo +998901234567)\n"
    "/ai — AI rejimi va bugungi sarf\n"
    "/sets — to'plamlar holati (qaysi fayl yuklanmagan)\n"
    "/stats — umumiy statistika\n"
    "/cohorts — oqimlar\n"
    "/broadcast — e'lon yuborish\n"
    "/preview &lt;set_code&gt; — o'quvchi ko'radigan ekranni sinash"
)

ADMIN_IMPORT_WAIT = (
    "Excel faylni yuboring. Fayl nomiga qarab turi aniqlanadi:\n"
    "<code>sets</code> · <code>answer_keys</code> · <code>levels</code> · "
    "<code>students</code>"
)
ADMIN_UPLOAD_WAIT = (
    "PDF yoki audio fayllarni yuboring (bir nechtasini ketma-ket ham mumkin).\n"
    "Fayl nomi <code>sets.xlsx</code> dagi nom bilan aynan mos kelsin.\n"
    "Tugagach /done bosing."
)

SIGNAL_UNKNOWN_PHONE = (
    "🔔 <b>Ro'yxatda yo'q raqam</b>\n"
    "Kim: {name} (@{username}, id <code>{tg_id}</code>)\n"
    "Raqam: <code>{phone}</code>"
)
SIGNAL_PHONE_TAKEN = (
    "⚠️ <b>Hisob ulashilyapti</b>\n"
    "Raqam <code>{phone}</code> ({owner}) uchun boshqa akkaunt urinmoqda:\n"
    "{name} (@{username}, id <code>{tg_id}</code>)"
)
SIGNAL_BAD_GRADING = (
    "⚠️ <b>«Noto'g'ri baholandi» signali</b>\n"
    "O'quvchi: {name} (id <code>{tg_id}</code>)\n"
    "To'plam: <code>{set_code}</code> · urinish #{attempt_no}\n"
    "Ball: {score}/{total}\n"
    "Xato deb belgilangan savollar: {wrong}\n\n"
    "Yuborilgan asl matn:\n<code>{raw}</code>"
)
