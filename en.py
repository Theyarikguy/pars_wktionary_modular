import re
from typing import Dict, List

from common import (
    HEADING_RE, clean_common, find_headings, split_lines,
)
from functools import reduce
from parser_types import Parser

LANG_EN_RE = re.compile(r'^==\s*([A-Za-z][A-Za-z ]*?)\s*==\s*$')

EN_POS = frozenset({
    'Noun', 'Verb', 'Adjective', 'Adverb', 'Pronoun', 'Preposition',
    'Conjunction', 'Interjection', 'Numeral', 'Determiner', 'Article',
    'Particle', 'Proper noun', 'Contraction', 'Phrase', 'Prefix', 'Suffix',
})

def _pipeline(*steps):
    return lambda x: reduce(lambda acc, f: f(acc), steps, x)

def _expand_templates(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = re.sub(
            r'\{\{\s*(?:l|m|m-self|mention|link)\s*\|[^|}]*\|([^{}|]+)(?:\|[^{}]*)?\}\}',
            r'\1', text, flags=re.I,
        )
        text = re.sub(
            r'\{\{\s*lb\s*\|[^|}]+\|([^{}]*)\}\}',
            lambda m: '(' + ', '.join(a.strip() for a in m.group(1).split('|') if a.strip()) + ')',
            text, flags=re.I,
        )
        text = re.sub(
            r'\{\{\s*(?:qualifier|q)\s*\|([^{}]*)\}\}',
            lambda m: '(' + ', '.join(a.strip() for a in m.group(1).split('|') if a.strip()) + ')',
            text, flags=re.I,
        )
        text = re.sub(r'\{\{\s*tax(?:fmt|link)\s*\|([^|}]+)[^{}]*\}\}', r'\1', text, flags=re.I)
        text = re.sub(r'\{\{\s*vern\s*\|([^|}]+)\}\}', r'\1', text, flags=re.I)
        text = re.sub(r'\{\{\s*i\s*\|([^|}]+)\}\}', r'\1', text, flags=re.I)
        text = re.sub(r'\{\{\s*senseid\s*\|[^{}]*\}\}', '', text, flags=re.I)
    return text


# цепочка «развернуть шаблоны → очистить общее»
clean_wikitext = _pipeline(_expand_templates, clean_common)


def _get_section(wikitext: str, lang: str = 'English') -> str:
    lines = split_lines(wikitext)
    start = end = None
    for i, line in enumerate(lines):
        m = LANG_EN_RE.match(line.strip())
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


def _parse_syn_template(text: str) -> List[str]:
    result = []
    for m in re.finditer(r'\{\{\s*(?:synonyms?|syn)\s*\|([^{}]*)\}\}', text, re.I):
        for arg in m.group(1).split('|')[1:]:
            s = clean_wikitext(arg).strip()
            if s and s not in result:
                result.append(s)
    return result


def _senses_in_pos(lines: list[str], start: int, end: int) -> list[dict]:
    """Значения внутри одной POS-секции. Нумерация — с 1."""
    result: list[dict] = []
    counter = 0
    current = None

    for k in range(start + 1, end):
        line = lines[k]

        m_def = re.match(r'^#\s+(.*)', line)
        if m_def and not line.startswith('#:') and not line.startswith('#*'):
            definition = clean_wikitext(m_def.group(1))
            if not definition:
                continue
            counter += 1
            current = {
                'no': counter,
                'definition': definition,
                'synonyms': [],
            }
            result.append(current)
            continue

        if line.startswith('#:') and current is not None:
            for s in _parse_syn_template(line[2:]):
                if s not in current['synonyms']:
                    current['synonyms'].append(s)

    return result


def _parse_meanings(wikitext: str) -> list[dict]:
    en = _get_section(wikitext, 'English')
    lines = en.splitlines()
    headings = find_headings(lines)

    result: list[dict] = []
    for idx, (i, level, title) in enumerate(headings):
        if title not in EN_POS:
            continue

        end = len(lines)
        for j in range(idx + 1, len(headings)):
            j_i, j_level, _ = headings[j]
            if j_level <= level:
                end = j_i
                break

        for item in _senses_in_pos(lines, i, end):
            result.append({
                'lang': 'en',
                'pos': title,
                'definition': item['definition'],
                'synonyms': item['synonyms'],
            })

    return result


def _extract(wikitext: str, title: str) -> dict:
    return {
        'title': title,
        'meanings': _parse_meanings(wikitext),
    }


def _extract(wikitext: str, title: str) -> dict:
    return {
        'title': title,
        'lexemes': _parse_meanings(wikitext),
    }


def _matches(text: str) -> bool:
    return any(
        (m := LANG_EN_RE.match(line.strip())) and m.group(1).lower() == 'english'
        for line in text.splitlines()
    )


def _extract(wikitext: str, title: str) -> dict:
    return {
        'title': title,
        'lang': 'en',
        'meanings': _parse_meanings(wikitext),
    }


EN_PARSER = Parser(code='en', matches=_matches, extract=_extract)