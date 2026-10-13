from setup_database import Base
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Word(Base):
    __tablename__ = 'word'
    __table_args__ = (
        UniqueConstraint('title', 'lang', 'pos', name='uq_word_title_lang_pos'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    lang: Mapped[str] = mapped_column(String(10), index=True, default='ru')
    pos: Mapped[str | None] = mapped_column(String(32), nullable=True)

    senses: Mapped[list['Sense']] = relationship(
        back_populates='word',
        cascade='all, delete-orphan',
        order_by='Sense.sense_no',
    )

    def __repr__(self) -> str:
        return f'<Word id={self.id} title={self.title!r} lang={self.lang!r} pos={self.pos!r}>'


class Sense(Base):
    __tablename__ = 'sense'
    __table_args__ = (
        UniqueConstraint('word_id', 'sense_no', name='uq_sense_word_no'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    word_id: Mapped[int] = mapped_column(
        ForeignKey('word.id', ondelete='CASCADE'), index=True
    )
    sense_no: Mapped[int] = mapped_column()
    definition: Mapped[str] = mapped_column(Text)

    word: Mapped['Word'] = relationship(back_populates='senses')
    synonyms: Mapped[list['Synonym']] = relationship(
        back_populates='sense',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'<Sense id={self.id} no={self.sense_no} def={self.definition!r}>'


class Synonym(Base):
    __tablename__ = 'synonym'
    __table_args__ = (
        UniqueConstraint('sense_id', 'synonym', name='uq_synonym_sense_text'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sense_id: Mapped[int] = mapped_column(
        ForeignKey('sense.id', ondelete='CASCADE'), index=True
    )
    synonym: Mapped[str] = mapped_column(String(255))

    sense: Mapped['Sense'] = relationship(back_populates='synonyms')

    def __repr__(self) -> str:
        return f'<Synonym id={self.id} text={self.synonym!r}>'