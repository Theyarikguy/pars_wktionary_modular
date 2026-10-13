import bz2
import mwxml

from crud import save_batch, show_nums, select_target
import parser_types
from connection import SessionLocal
from builtin import default_registry

import re
from typing import List, Dict

from register import ParserRegistry
from setup_database import init_db, drop_db

PATH = "enwiktionary-20261001-pages-articles-multistream.xml.bz2"
# Press the green button in the gutter to run the script.

# See PyCharm help at https://www.jetbrains.com/help/pycharm/


def write_db(registry: ParserRegistry, lang: str | None = None) -> None:
    BATCH_SIZE = 5000
    buffer: list[dict] = []
    i = 0
    N = -1

    if lang is not None and registry.get(lang) is None:
        raise ValueError(f'no parser registered for lang={lang!r}')

    with bz2.open(PATH, "rb") as f:
        dump = mwxml.Dump.from_file(f)
        with SessionLocal() as db:
            for page in dump:
                if page.namespace != 0 or page.redirect:
                    continue

                last_rev = None
                for rev in page:
                    last_rev = rev
                if last_rev is None or not last_rev.text:
                    continue

                stripped = last_rev.text.lstrip()
                if stripped.startswith('#') and stripped.upper().startswith('#REDIRECT'):
                    continue

                if lang is not None:
                    parser = registry.get(lang)
                    entries = [parser.extract(last_rev.text, page.title)]
                else:
                    entries = [
                        p.extract(last_rev.text, page.title)
                        for p in registry.detect(last_rev.text)
                    ]

                entries = [e for e in entries if e['meanings']]
                if not entries:
                    continue

                buffer.extend(entries)
                while len(buffer) >= BATCH_SIZE:
                    chunk, buffer[:] = buffer[:BATCH_SIZE], buffer[BATCH_SIZE:]
                    save_batch(db, chunk)

                i += 1
                if i == N:
                    break

            if buffer:
                save_batch(db, buffer)

if __name__ == '__main__':
    # drop_db()
    # init_db()
    with SessionLocal() as db:
        show_nums(db)
        select_target(db, target = "walk")

    # registry = default_registry()
    # write_db(registry, lang='en')