import re
import sys
from pathlib import Path

from lang_parsers.ru import _get_section, RU_POS_RE
from main import get_article_by_title

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select

from crud import select_target
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.database_models import Sense, Synonym, Word

from database.connection import SessionLocal

PATH = "../ruwiktionary-20260101-pages-articles-multistream.xml.bz2"
def find_template_suspects(section: str) -> list[str]:
    """Все шаблоны, начинающиеся как часть речи, но не поймавшиеся RU_POS_RE."""
    suspects = []
    # ищем {{xxx ... }} где xxx — кириллическое «слово» длиной 2–12
    for m in re.finditer(r'\{\{\s*([а-яё]{2,12})[^\w]', section, re.IGNORECASE):
        name = m.group(1).lower()
        if name in {'сущ', 'прил', 'гл', 'нар', 'мест', 'числ',
                    'предл', 'союз', 'част', 'межд', 'предик',
                    'прич', 'деепр', 'фразеол', 'нареч'}:
            fragment = section[m.start():m.start() + 120].split('\n')[0]
            suspects.append(fragment)
    return suspects


def pick_random_no_pos(db, lang: str = 'ru') -> str | None:
    """Случайный Word(lang=lang, pos IS NULL)."""
    return db.scalar(
        select(Word.title)
        .where(Word.lang == lang, Word.pos.is_(None))
        .order_by(func.random())
        .limit(1)
    )


def main() -> None:
    with SessionLocal() as db:
        total = db.scalar(
            select(func.count(Word.id))
            .where(Word.lang == 'ru', Word.pos.is_(None))
        )
        print(f"Word(lang='ru', pos IS NULL): {total}")

        if not total:
            print("нет записей без pos")
            return

        title = pick_random_no_pos(db)
        print(f"случайное слово: {title!r}\n")

    text = get_article_by_title(PATH, title)
    if not text:
        print(f"статья {title!r} не найдена в дампе")
        return

    section = _get_section(text, 'ru')

    print("=== секция «Морфологические и синтаксические свойства» ===")
    m = re.search(
        r'==+\s*Морфологические и синтаксические свойства\s*==+(.*?)(?=\n==+|\Z)',
        section, re.DOTALL,
    )
    if m:
        print(m.group(1).strip()[:1500])
    else:
        print("(раздел не найден)")

    print("\n=== RU_POS_RE на этой секции ===")
    matches = RU_POS_RE.findall(section)
    print(matches if matches else "(нет совпадений)")

    print("\n=== подозрительные шаблоны (первый аргумент похож на часть речи) ===")
    suspects = find_template_suspects(section)
    if suspects:
        for s in suspects[:10]:
            print(" ", s)
    else:
        print("(ничего похожего на морфологический шаблон не найдено)")

    print("\n=== все шаблоны в разделе «Морфология» (первые 10) ===")
    if m:
        morph = m.group(1)
        for tpl in re.findall(r'\{\{[^{}]*\}?\}?', morph)[:10]:
            print(" ", tpl)


if __name__ == '__main__':
    main()