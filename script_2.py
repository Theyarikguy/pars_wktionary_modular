from crud import select_target
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.database_models import Sense, Synonym, Word

from database.connection import SessionLocal
with SessionLocal() as db:
    select_target(db, target = "украинский")

with SessionLocal() as db:
    total = db.scalar(
        select(func.count(Word.id)).where(Word.lang == 'ru')
    )
    with_pos = db.scalar(
        select(func.count(Word.id))
        .where(Word.lang == 'ru', Word.pos.is_not(None))
    )
    without_pos = db.scalar(
        select(func.count(Word.id))
        .where(Word.lang == 'ru', Word.pos.is_(None))
    )

print(f"всего ru: {total}")
print(f"с pos:    {with_pos}")
print(f"без pos:  {without_pos}")