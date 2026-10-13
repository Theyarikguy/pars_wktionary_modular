import re
from typing import Dict, List

from common import (
    HEADING_RE, clean_common, find_headings, numbered_until, split_lines,
    split_synonyms,
)
from fp import mapcat, pipe
from parser_types import Parser

LANG_RU_RE = re.compile(r'^=\s*\{\{-([a-z-]+)\}\}\s*=\s*$', re.I)

clean_wikitext = clean_common


# --- чистые функции ---

def _get_section(wikitext: str, lang: str = 'ru') -> str:
    lines = split_lines(wikitext)
    start = end = None
    for i, line in enumerate(lines):
        m = LANG_RU_RE.match(line.strip())
        if not m:
            continue
        if start is None:
            if m.group(1).lower() == lang.lower():
                start = i
        elif end is None:
            end = i
            break
    if start is None:
        return wikitext
    return '\n'.join(lines[start:end if end is not None else len(lines)])


def _senses_from_heading(
    lines: List[str],
    headings: List[tuple[int, int, str]],
    idx: int,
) -> List[Dict]:
    """Значения для одного заголовка 'Значение'."""
    i, level, _ = headings[idx]
    definitions = numbered_until(lines, i, level)

    # ищем следующую секцию 'Синонимы' до следующего 'Значение'
    synonyms_raw: List[str] = []
    for j in range(idx + 1, len(headings)):
        j_i, j_level, j_title = headings[j]
        if j_title == 'Значение':
            break
        if j_title == 'Синонимы':
            synonyms_raw = numbered_until(lines, j_i, j_level)
            break

    def build(pair: tuple[int, str]) -> Dict:
        k, raw = pair
        syn_text = synonyms_raw[k] if k < len(synonyms_raw) else ''
        return {
            'no': k + 1,
            'definition': clean_wikitext(raw),
            'synonyms': split_synonyms(clean_wikitext(syn_text)),
        }

    return [build(p) for p in enumerate(definitions)]


def _parse_meanings(wikitext: str) -> list[dict]:
    section = get_section(wikitext, 'ru')
    lines = section.splitlines()
    headings = find_headings(lines)

    result: list[dict] = []
    for idx, (_, _, title) in enumerate(headings):
        if title != 'Значение':
            continue
        for item in _senses_from_heading(lines, headings, idx):
            result.append({
                'lang': 'ru',
                'pos': None,
                'definition': item['definition'],
                'synonyms': item['synonyms'],
            })
    return result


def _extract(wikitext: str, title: str) -> dict:
    return {
        'title': title,
        'meanings': _parse_meanings(wikitext),
    }

# --- значение парсера ---

def _matches(text: str) -> bool:
    return any(
        (m := LANG_RU_RE.match(line.strip())) and m.group(1).lower() == 'ru'
        for line in text.splitlines()
    )


def _extract(wikitext: str, title: str) -> dict:
    return {
        'title': title,
        'lexemes': [
            {'lang': 'ru', 'pos': None, 'meanings': _parse_meanings(wikitext)},
        ],
    }


RU_PARSER = Parser(code='ru', matches=_matches, extract=_extract)