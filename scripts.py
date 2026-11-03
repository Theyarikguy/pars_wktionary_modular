from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.database_models import Sense, Synonym, Word

from database.connection import SessionLocal


def categorize_adjective_synonyms(db: Session) -> dict[str, list[str]]:
    """
    Разбивает все синонимы прилагательных на три категории:
      - no_article:    синоним не найден как прилагательное
      - one_meaning:   найден, у него ровно одно значение
      - many_meanings: найден, у него 2+ значений
    """
    # 1) все уникальные синонимы прилагательных
    synonyms: list[str] = list(db.scalars(
        select(Synonym.synonym)
        .join(Sense, Sense.id == Synonym.sense_id)
        .join(Word, Word.id == Sense.word_id)
        .where(Word.pos == 'Adjective')
        .distinct()
    ).all())

    print(f"[1] синонимов прилагательных: {len(synonyms)}")

    if not synonyms:
        return {'no_article': [], 'one_meaning': [], 'many_meanings': []}

    # 2) какие из них существуют как Word(pos='Adjective')
    existing_titles: set[str] = set(db.scalars(
        select(Word.title)
        .where(Word.title.in_(synonyms))
        .distinct()
    ).all())

    print(f"[2] из них найдено как прилагательные: {len(existing_titles)}")

    # 3) сколько senses у каждой найденной статьи
    sense_counts: dict[str, int] = dict(db.execute(
        select(Word.title, func.count(Sense.id))
        .join(Sense, Sense.word_id == Word.id)
        .where(Word.title.in_(existing_titles))
        .group_by(Word.title)
    ).all())

    print(f"[3] title с посчитанными senses: {len(sense_counts)}")
    print(f"    сумма senses: {sum(sense_counts.values())}")

    zero_count = [t for t in existing_titles if sense_counts.get(t, 0) == 0]
    print(f"    в existing, но без senses: {len(zero_count)}")
    if zero_count:
        print(f"    примеры: {zero_count[:10]}")

    # 4) распределение
    no_article: list[str] = []
    one_meaning: list[str] = []
    many_meanings: list[str] = []

    for syn in synonyms:
        if syn not in existing_titles:
            no_article.append(syn)
            continue

        cnt = sense_counts.get(syn, 0)
        if cnt >= 2:
            many_meanings.append(syn)
        elif cnt == 1:
            one_meaning.append(syn)
        else:
            no_article.append(syn)

    print(f"[4] no_article={len(no_article)} "
          f"one_meaning={len(one_meaning)} "
          f"many_meanings={len(many_meanings)} "
          f"(сумма={len(no_article)+len(one_meaning)+len(many_meanings)}, "
          f"исходных={len(synonyms)})")

    return {
        'no_article': sorted(no_article),
        'one_meaning': sorted(one_meaning),
        'many_meanings': sorted(many_meanings),
    }

with SessionLocal() as db:
    result = categorize_adjective_synonyms(db)

total = sum(len(v) for v in result.values())
for cat in ('no_article', 'one_meaning', 'many_meanings'):
    n = len(result[cat])
    pct = n / total * 100 if total else 0
    print(f"{cat:15s}: {n:6d} ({pct:5.1f}%)")
print(f"{'total':15s}: {total:6d}")

# при желании — сохранить в файлы
for cat, items in result.items():
    with open(f"{cat}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(items))