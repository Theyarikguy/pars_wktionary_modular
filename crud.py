from sqlalchemy.orm import Session, selectinload

from sqlalchemy import select, insert
from database_models import Word, Sense, Synonym

from sqlalchemy import select,func


def save_batch(db: Session, batch: list[dict]) -> int:
    if not batch:
        return 0

    # проверяем существующие страницы одним запросом
    titles = list({d['title'] for d in batch})
    existing = set(db.scalars(
        select(Word.title).where(Word.title.in_(titles))
    ).all())

    pages: list[Word] = []
    for data in batch:
        if data['title'] in existing:
            continue

        senses = []
        counter = 0
        for item in data['meanings']:
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
                lang=data.get('lang') or 'ru',
                pos=item.get('pos'),
                synonyms=synonyms,
            ))

        if not senses:
            continue

        pages.append(Word(title=data['title'], senses=senses))

    db.add_all(pages)
    db.commit()
    return len(pages)

def show_nums(db: Session):
    """Сохраняет пачку распарсенных страниц одним коммитом."""

    query = select(func.count()).select_from(Word)
    total = db.scalar(query)
    print(total)

def select_target(db: Session, target: str):
    """Возвращает страницу с заданным title вместе со значениями и синонимами."""
    query = (
        select(Word)
        .where(Word.title == target)
        .options(
            selectinload(Word.senses).selectinload(Sense.synonyms)
        )
    )
    page = db.execute(query).scalar_one_or_none()

    if page is None:
        print(f"page not found: {target}")
        return None

    print(f"Page: {page.title} (id={page.id})")
    for sense in page.senses:
        syns = ', '.join(s.synonym for s in sense.synonyms) or '—'
        print(f"  {sense.sense_no}. {sense.definition} | синонимы: {syns}")

    return page
