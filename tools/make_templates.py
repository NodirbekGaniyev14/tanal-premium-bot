"""To'rtta Excel shablonini yasaydi: sets · answer_keys · levels · students.

Ishga tushirish:
    python -m tools.make_templates            # ./templates papkasiga
    python -m tools.make_templates ./chiqish  # boshqa papkaga
"""

from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HEADER_FILL = PatternFill("solid", fgColor="0B6152")
HEADER_FONT = Font(color="FFFFFF", bold=True)
NOTE_FONT = Font(color="65746C", italic=True)


def _write_sheet(
    workbook: Workbook,
    title: str,
    headers: list[str],
    rows: list[list[object]],
    widths: list[int],
) -> None:
    sheet = workbook.active
    sheet.title = title

    sheet.append(headers)
    for cell in sheet[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center")
    sheet.freeze_panes = "A2"

    for row in rows:
        sheet.append(row)

    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width


def _add_notes(workbook: Workbook, lines: list[str]) -> None:
    sheet = workbook.create_sheet("izoh")
    sheet.column_dimensions["A"].width = 110
    for line in lines:
        cell = sheet.cell(row=sheet.max_row + 1 if sheet.max_row > 1 else 1, column=1)
        cell.value = line
        cell.font = NOTE_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="top")


def _yes_no(sheet, column: str, last_row: int = 500) -> None:
    validation = DataValidation(type="list", formula1='"yes,no"', allow_blank=False)
    sheet.add_data_validation(validation)
    validation.add(f"{column}2:{column}{last_row}")


def build_sets(path: Path) -> None:
    workbook = Workbook()
    headers = [
        "set_code",
        "section",
        "title",
        "topic_no",
        "total_q",
        "attempts",
        "reveal",
        "requires",
        "sort_order",
        "pdf_file",
        "audio_file",
        "theory_file",
    ]
    rows: list[list[object]] = [
        [
            "GR-T01", "grammar_topic", "Ega va kesim — test", 1, 20, 3, "yes",
            None, 1, "01_subject-verb_test.pdf", None, "01_subject-verb_theory.pdf",
        ],
        [
            "GR-T02", "grammar_topic", "Articles — test", 2, 20, 3, "yes",
            "GR-T01", 2, "02_articles_test.pdf", None, "02_articles_theory.pdf",
        ],
        [
            "GR-T03", "grammar_topic", "Present Perfect — test", 3, 20, 3, "yes",
            "GR-T02", 3, "03_present-perfect_test.pdf", None,
            "03_present-perfect_theory.pdf",
        ],
        [
            "GR-M01", "grammar_mock", "Grammatika mock 1", None, 50, 1, "no",
            None, 1, "gr_mock_01.pdf", None, None,
        ],
        [
            "RD-M01", "reading", "Reading mock 1", None, 40, 1, "no",
            None, 1, "rd_mock_01.pdf", None, None,
        ],
        [
            "LS-M01", "listening", "Listening mock 1", None, 40, 1, "no",
            None, 1, "ls_mock_01.pdf", "ls_mock_01.mp3", None,
        ],
    ]
    _write_sheet(
        workbook,
        "sets",
        headers,
        rows,
        [12, 16, 34, 10, 9, 10, 9, 12, 11, 30, 22, 30],
    )
    sheet = workbook["sets"]

    section_validation = DataValidation(
        type="list",
        formula1='"grammar_topic,grammar_mock,reading,listening"',
        allow_blank=False,
    )
    sheet.add_data_validation(section_validation)
    section_validation.add("B2:B500")
    _yes_no(sheet, "G")

    _add_notes(
        workbook,
        [
            "sets.xlsx — har bir test yoki mockning pasporti.",
            "",
            "set_code — takrorlanmas kod. Tavsiya: GR-T01 (mavzu testi), GR-M01 (grammatika mock), RD-M01, LS-M01.",
            "section — grammar_topic | grammar_mock | reading | listening. Boshqa qiymat qabul qilinmaydi.",
            "title — o'quvchi menyuda ko'radigan nom.",
            "topic_no — faqat grammar_topic uchun mavzu tartib raqami.",
            "total_q — savollar soni. Javob kaliti shuncha qatordan iborat bo'lishi kerak.",
            "attempts — necha marta yechish mumkin. Mavzu testlarida 3, mocklarda 1.",
            "reveal — yes bo'lsa natijada to'g'ri javoblar ko'rsatiladi (mavzu testi), no bo'lsa faqat xato raqamlari (mock).",
            "requires — shu to'plamdan oldin yakunlanishi shart bo'lgan set_code. Bo'sh qoldirilsa qulf yo'q.",
            "sort_order — menyudagi tartib. Bo'sh bo'lsa topic_no ishlatiladi.",
            "pdf_file / audio_file / theory_file — fayl nomlari. Botga yuklanadigan fayl nomi bilan AYNAN bir xil bo'lsin.",
            "",
            "Fayl nomlashda bo'shliq va o'zbek harflari ishlatilmasin:",
            "  yaxshi: 03_present-perfect_test.pdf",
            "  yomon:  3-mavzu test.pdf",
        ],
    )
    workbook.save(path)


def build_answer_keys(path: Path) -> None:
    workbook = Workbook()
    headers = ["set_code", "q_no", "answer", "accept_also", "tag"]
    rows: list[list[object]] = [
        ["GR-T03", 1, "B", None, "for / since"],
        ["GR-T03", 2, "D", None, "already / yet"],
        ["GR-T03", 3, "A", None, "for / since"],
        ["RD-M01", 7, "car park", "carpark", "matching"],
        ["RD-M01", 12, "TRUE", "T", "true/false"],
        ["RD-M01", 13, "NOT GIVEN", "NG", "true/false"],
        ["LS-M01", 3, "15 minutes", "fifteen minutes; 15 min", "form filling"],
    ]
    _write_sheet(workbook, "answer_keys", headers, rows, [12, 8, 24, 34, 22])
    _add_notes(
        workbook,
        [
            "answer_keys.xlsx — javob kaliti. Baholash ham, tavsiyalar ham shu jadvaldan.",
            "",
            "set_code — sets.xlsx dagi kod bilan bir xil bo'lsin.",
            "q_no — savol raqami, 1 dan total_q gacha. Har to'plamda takrorlanmasin.",
            "answer — to'g'ri javob. Variantli savollarda A/B/C/D, so'zli savollarda so'zning o'zi.",
            "accept_also — muqobil javoblar, nuqtali vergul (;) bilan ajratiladi.",
            "tag — savol qaysi kichik mavzuga tegishli. IXTIYORIY, lekin eng qimmatli ustun:",
            "      bot «xatolaringizning uchtasi ham for / since ga tegishli» deya olishi shundan.",
            "",
            "Bot quyidagilarni o'zi hisobga oladi, ularni accept_also ga yozish shart emas:",
            "  katta/kichik harf · ortiqcha bo'shliq · nuqta va vergul",
            "  artikllar: «the moon» = «moon»",
            "  bo'shliq va defis: «car park» = «carpark» = «car-park»",
            "  raqam va so'z: «15» = «fifteen», «twenty five» = «25»",
            "  qisqartmalar: T = TRUE, F = FALSE, NG = NOT GIVEN",
        ],
    )
    workbook.save(path)


def build_levels(path: Path) -> None:
    workbook = Workbook()
    headers = ["scope", "raw_min", "raw_max", "level", "label"]
    rows: list[list[object]] = [
        ["grammar_mock", 0, 15, "A1", "Beginner"],
        ["grammar_mock", 16, 25, "A2", "Elementary"],
        ["grammar_mock", 26, 35, "B1", "Intermediate"],
        ["grammar_mock", 36, 44, "B2", "Upper-Intermediate"],
        ["grammar_mock", 45, 50, "C1", "Advanced"],
        ["reading", 0, 12, "A1", "Beginner"],
        ["reading", 13, 20, "A2", "Elementary"],
        ["reading", 21, 28, "B1", "Intermediate"],
        ["reading", 29, 35, "B2", "Upper-Intermediate"],
        ["reading", 36, 40, "C1", "Advanced"],
        ["listening", 0, 12, "A1", "Beginner"],
        ["listening", 13, 20, "A2", "Elementary"],
        ["listening", 21, 28, "B1", "Intermediate"],
        ["listening", 29, 35, "B2", "Upper-Intermediate"],
        ["listening", 36, 40, "C1", "Advanced"],
    ]
    _write_sheet(workbook, "levels", headers, rows, [16, 10, 10, 9, 24])
    _add_notes(
        workbook,
        [
            "levels.xlsx — daraja shkalasi. Kodda emas, shu yerda turadi.",
            "",
            "scope — grammar_topic | grammar_mock | reading | listening.",
            "raw_min / raw_max — xom ball diapazoni (ikkalasi ham diapazonga kiradi).",
            "level — A1 … C2 yoki o'zingizning belgingiz.",
            "label — daraja nomi, o'quvchiga ko'rsatiladi.",
            "",
            "MUHIM: bitta scope ichida diapazonlar kesishmasin va uzilmasin.",
            "  to'g'ri:  0–15, 16–25, 26–35",
            "  xato:     0–15, 15–25  (kesishadi)",
            "  xato:     0–15, 18–25  (16 va 17 ochiq qolgan)",
            "Import buni tekshiradi va xatoni aniq ko'rsatadi.",
            "",
            "Mavzu testlari uchun daraja shart emas — ular foizda ko'rsatiladi.",
        ],
    )
    workbook.save(path)


def build_students(path: Path) -> None:
    workbook = Workbook()
    headers = ["full_name", "phone", "cohort", "note", "access_until"]
    rows: list[list[object]] = [
        ["Aziza Karimova", "+998901234567", "2026-kuz", "to'liq to'lov", None],
        ["Bekzod Tursunov", "+998911112233", "2026-kuz", "bo'lib to'lash", None],
    ]
    _write_sheet(workbook, "students", headers, rows, [28, 20, 14, 26, 14])
    sheet = workbook["students"]
    for row in range(2, 500):
        sheet.cell(row=row, column=2).number_format = "@"  # raqam matn bo'lib qolsin

    _add_notes(
        workbook,
        [
            "students.xlsx — kimga kirish ruxsat etilgani. Telefon raqami yagona identifikator.",
            "",
            "full_name — o'quvchining to'liq ismi. PDF nusxalariga shu ism yoziladi.",
            "phone — xalqaro formatda: +998901234567. Bo'shliq, defis va qavs bo'lsa ham bot tozalaydi.",
            "        Excel raqamni songa aylantirib yubormasligi uchun ustun matn formatida.",
            "cohort — kurs oqimi nomi: 2026-kuz, 2027-bahor. Natijalar shu bo'yicha ajratiladi.",
            "note — ichki eslatma, o'quvchiga ko'rinmaydi.",
            "access_until — kirish shu sanadan keyin avtomatik yopiladi (ixtiyoriy, YYYY-MM-DD).",
            "",
            "Yangi guruh boshlash: yangi cohort nomi bilan yangi fayl yuboriladi.",
            "Mavjud raqam qayta yuborilsa ism va oqim yangilanadi, Telegram ID tegilmaydi.",
        ],
    )
    workbook.save(path)


def build_ai_tasks(path: Path) -> None:
    workbook = Workbook()
    headers = ["code", "kind", "part", "title", "prompt_text", "cue_points", "image_file"]
    rows: list[list[object]] = [
        [
            "WR-T1-01", "writing", "task1", "Task 1 — chiziqli grafik",
            "The graph below shows the number of visitors to three museums in "
            "London between 2007 and 2012. Summarise the information by selecting "
            "and reporting the main features, and make comparisons where relevant. "
            "Write at least 150 words.",
            None, "wr_t1_01_graph.png",
        ],
        [
            "WR-T2-01", "writing", "task2", "Task 2 — ta'lim",
            "Some people think that universities should provide graduates with the "
            "knowledge and skills needed in the workplace. Others think that the "
            "true function of a university is to give access to knowledge for its "
            "own sake. Discuss both views and give your own opinion. "
            "Write at least 250 words.",
            None, None,
        ],
        [
            "SP-P1-01", "speaking", "1", "Part 1 — uy",
            "Let's talk about your home. Do you live in a house or an apartment? "
            "What do you like most about the place where you live?",
            None, None,
        ],
        [
            "SP-P2-01", "speaking", "2", "Part 2 — esda qolgan sayohat",
            "Describe a journey that you remember well.",
            "You should say:\n— where you went\n— who you went with\n"
            "— what you did there\nand explain why you remember this journey well.",
            None,
        ],
        [
            "SP-P3-01", "speaking", "3", "Part 3 — sayohat va jamiyat",
            "Why do you think people travel abroad more than they used to? "
            "Do you think tourism always benefits local communities?",
            None, None,
        ],
    ]
    _write_sheet(workbook, "ai_tasks", headers, rows, [14, 12, 8, 30, 70, 46, 24])
    sheet = workbook["ai_tasks"]

    kind_validation = DataValidation(
        type="list", formula1='"writing,speaking"', allow_blank=False
    )
    sheet.add_data_validation(kind_validation)
    kind_validation.add("B2:B500")

    part_validation = DataValidation(
        type="list", formula1='"task1,task2,1,2,3"', allow_blank=False
    )
    sheet.add_data_validation(part_validation)
    part_validation.add("C2:C500")

    _add_notes(
        workbook,
        [
            "ai_tasks.xlsx — writing topshiriqlari va speaking savollari banki.",
            "",
            "code — takrorlanmas kod: WR-T1-01, SP-P2-07 kabi.",
            "kind — writing | speaking.",
            "part — writing uchun: task1 | task2. speaking uchun: 1 | 2 | 3.",
            "title — o'quvchi ro'yxatda ko'radigan qisqa nom.",
            "prompt_text — topshiriq yoki savolning to'liq matni. Gemini'ga aynan shu matn boradi.",
            "cue_points — faqat Speaking Part 2 uchun cue card bandlari (yangi qatorlar bilan).",
            "image_file — faqat Writing Task 1 uchun grafik rasmi. Fayl nomi bilan AYNAN mos kelsin.",
            "",
            "Speaking savollari tasodifiy tanlanadi — har qism uchun 10–20 tadan bo'lgani yaxshi.",
            "Rasm /upload rejimida hujjat sifatida yuboriladi.",
        ],
    )
    workbook.save(path)


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("templates")
    out_dir.mkdir(parents=True, exist_ok=True)

    build_sets(out_dir / "sets.xlsx")
    build_answer_keys(out_dir / "answer_keys.xlsx")
    build_levels(out_dir / "levels.xlsx")
    build_students(out_dir / "students.xlsx")
    build_ai_tasks(out_dir / "ai_tasks.xlsx")

    for name in ("sets", "answer_keys", "levels", "students", "ai_tasks"):
        print(f"tayyor: {out_dir / (name + '.xlsx')}")


if __name__ == "__main__":
    main()
