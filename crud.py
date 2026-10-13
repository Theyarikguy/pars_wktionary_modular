from sqlalchemy.orm import Session, selectinload

from sqlalchemy import select, insert
from database_models import Word, Sense, Synonym

from sqlalchemy import select,func


def save_batch(db: Session, batch: list[dict]) -> int:
    if not batch:
        return 0

    # собираем все ключи (title, lang, pos), которые есть в батче
    all_keys: set[tuple[str, str, str | None]] = set()
    for data in batch:
        title = data['title']
        for item in data.get('meanings', []):
            all_keys.add((title, item.get('lang', 'ru'), item.get('pos')))

    if all_keys:
        existing_rows = db.execute(
            select(Word.title, Word.lang, Word.pos)
            .where(Word.title.in_({t for t, _, _ in all_keys}))
        ).all()
        existing = {(r.title, r.lang, r.pos) for r in existing_rows}
    else:
        existing = set()

    words: list[Word] = []
    for data in batch:
        title = data['title']

        # группируем значения одного title по (lang, pos)
        groups: dict[tuple[str, str | None], list[dict]] = {}
        for item in data.get('meanings', []):
            key = (item.get('lang', 'ru'), item.get('pos'))
            groups.setdefault(key, []).append(item)

        for (lang, pos), items in groups.items():
            key = (title, lang, pos)
            if key in existing:
                continue

            senses: list[Sense] = []
            counter = 0
            for item in items:
                definition = (item.get('definition') or '').strip()
                if not definition:
                    continue
                counter += 1

                seen = set()
                synonyms = []
                for s in item.get('synonyms', []):
                    s = (s or '').strip()
                    if not s or s in seen:
                        continue
                    seen.add(s)
                    synonyms.append(Synonym(synonym=s))

                senses.append(Sense(
                    sense_no=counter,
                    definition=definition,
                    synonyms=synonyms,
                ))

            if not senses:
                continue

            words.append(Word(
                title=title,
                lang=lang,
                pos=pos,
                senses=senses,
            ))
            existing.add(key)   # защита от дублей внутри батча

    db.add_all(words)
    db.commit()
    return len(words)
def show_nums(db: Session):
    """Сохраняет пачку распарсенных страниц одним коммитом."""

    query = select(func.count()).select_from(Word)
    total = db.scalar(query)
    print(total)

def select_target(db: Session, target: str):
    """Возвращает все Word с заданным title вместе со значениями и синонимами."""
    query = (
        select(Word)
        .where(Word.title == target)
        .options(
            selectinload(Word.senses).selectinload(Sense.synonyms)
        )
        .order_by(Word.lang, Word.pos)
    )
    words = db.execute(query).scalars().all()

    if not words:
        print(f"page not found: {target}")
        return []

    print(f"Page: {target} ({len(words)} lexeme(s))")
    for word in words:
        label = f"{word.lang}/{word.pos}" if word.pos else word.lang
        print(f"  [{label}] (id={word.id})")
        for sense in word.senses:
            syns = ', '.join(s.synonym for s in sense.synonyms) or '—'
            print(f"    {sense.sense_no}. {sense.definition} | синонимы: {syns}")

    return words
