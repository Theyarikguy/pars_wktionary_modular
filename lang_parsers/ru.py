import re
from typing import Dict, List

from common import (
    HEADING_RE, clean_common, find_headings, numbered_until, split_lines,
    split_synonyms,
)

from lang_parsers.parser_types import Parser

RU_POS_BY_NAME = {
    'сущ':      'Noun',
    'прил':     'Adjective',
    'гл':       'Verb',
    'нар':      'Adverb',
    'нареч':    'Adverb',
    'adv':      'Adverb',
    'мест':     'Pronoun',
    'числ':     'Numeral',
    'предл':    'Preposition',
    'prep'      'Preposition'
    'союз':     'Conjunction',
    'част':     'Particle',
    'межд':     'Interjection',
    'interj':   'Interjection',
    'предик':   'Predicative',
    'вводн':    'Parenthetical',
    'прич':     'Participle',
    'деепр':    'Gerund',
    'фразеол':  'Phrase',
    'phrase':   'Phrase',
    'поговорк': 'Proverb',
    'посл':     'Proverb',
    'abbrev':  'Abbreviation',

}

RU_NON_POS_NAMES = {
    'морфо', 'слобр', 'transcription', 'transcriptions', 'transcription-ru',
    'по-слогам', 'пример', 'илл', 'иллюстрация', 'семантика',
    'категория', 'wikipedia', 'wikt', 'омонимы', 'also', 'cf',
}

RU_BARE_POS_RE = re.compile(
    r'\{\{\s*(фразеол|поговорк|посл)\s*[\|}]',
    re.IGNORECASE,
)

RU_SURNAME_RE = re.compile(r'\{\{\s*Фам(?=[\s\|}])', re.IGNORECASE)

RU_POS_RE = re.compile(r'\{\{\s*([а-яё]+)[\s\-]+ru\b', re.IGNORECASE)

LANG_RU_RE = re.compile(r'^=\s*\{\{-([a-z-]+)-\}\}\s*=\s*$', re.I)



# {{прил-ru|...}} / {{прил ru|...}}
RU_POS_LANG_RE = re.compile(
    r'\{\{\s*([a-zA-Zа-яё]+)[\s\-]+ru\b',
    re.IGNORECASE,
)



clean_wikitext = clean_common
# --- чистые функции ---

def _has_template_for_ru(section: str, template_name: str) -> bool:
    """Шаблон присутствует и либо без lang, либо с lang=ru."""
    for span in _iter_balanced_templates(section, template_name):
        body = section[span[0]:span[1]]
        m = re.search(r'\|\s*lang\s*=\s*([a-zA-Z\-]+)', body)
        if not m or m.group(1).lower() == 'ru':
            return True
    return False

def _iter_balanced_templates(text: str, name: str):
    """Итерируется по всем {{name ...}} с учётом вложенности."""
    pattern = re.compile(r'\{\{\s*' + re.escape(name) + r'(?=[\s\|}])')
    for m in pattern.finditer(text):
        i = m.start()
        depth = 0
        j = i
        while j < len(text) - 1:
            if text[j:j + 2] == '{{':
                depth += 1
                j += 2
            elif text[j:j + 2] == '}}':
                depth -= 1
                j += 2
                if depth == 0:
                    yield (i, j)
                    break
            else:
                j += 1

def _find_balanced_template(text: str, name: str) -> tuple[int, int] | None:
    """Находит {{name ...}} с учётом вложенных {{...}}, возвращает (start, end)."""
    pattern = re.compile(r'\{\{\s*' + re.escape(name) + r'(?=[\s\|}])')
    m = pattern.search(text)
    if not m:
        return None
    i = m.start()
    depth = 0
    j = i
    while j < len(text) - 1:
        if text[j:j + 2] == '{{':
            depth += 1
            j += 2
        elif text[j:j + 2] == '}}':
            depth -= 1
            j += 2
            if depth == 0:
                return (i, j)
        else:
            j += 1
    return None


def _split_template_args(body: str) -> list[str]:
    """Разбивает 'a=1|b=2|c={{x|y}}' по | верхнего уровня."""
    parts, current = [], []
    depth = 0
    i = 0
    while i < len(body):
        if body[i:i + 2] == '{{':
            depth += 1
            current.append('{{')
            i += 2
        elif body[i:i + 2] == '}}':
            depth -= 1
            current.append('}}')
            i += 2
        elif body[i] == '|' and depth == 0:
            parts.append(''.join(current))
            current = []
            i += 1
        else:
            current.append(body[i])
            i += 1
    parts.append(''.join(current))
    return parts


def _parse_semantika_value(value: str) -> list[str]:
    """Значение параметра синонимы=... → список строк."""
    value = value.strip()
    if not value or value in {'—', '-', '?'}:
        return []

    # {{помета|частичн.}}: [[луг]] → [[луг]]
    value = re.sub(
        r'\{\{\s*(?:помета|разг\.|прост\.|устар\.)\s*\|[^{}]*\}\}\s*:?\s*',
        '', value,
    )
    # оставшиеся шаблоны
    value = re.sub(r'\{\{[^{}]*\}\}', '', value)
    # вики-ссылки
    value = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', value)
    value = re.sub(r'\[\[([^\]]+)\]\]', r'\1', value)
    value = value.lstrip(':').strip()

    result, seen = [], set()
    for p in re.split(r'[,;]', value):
        p = p.strip().strip(':,;.').strip()
        if not p or p in seen or p in {'?', '—', '-'}:
            continue
        seen.add(p)
        result.append(p)
    return result


def _extract_semantika_synonyms(line: str) -> list[str]:
    """Синонимы из {{семантика|синонимы=...}} в строке определения."""
    span = _find_balanced_template(line, 'семантика')
    if span is None:
        return []

    body = line[span[0] + 2:span[1] - 2]
    if body.startswith('семантика'):
        body = body[len('семантика'):]
        if body.startswith('|'):
            body = body[1:]

    for arg in _split_template_args(body):
        key, sep, val = arg.partition('=')
        if sep and key.strip() == 'синонимы':
            return _parse_semantika_value(val)
    return []

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
        return ''
    return '\n'.join(lines[start:end if end is not None else len(lines)])


def _senses_from_heading(
    lines: List[str],
    headings: List[tuple[int, int, str]],
    idx: int,
) -> List[Dict]:
    """Значения для одного заголовка 'Значение'."""
    i, level, _ = headings[idx]
    definitions = numbered_until(lines, i, level)

    # секция === Синонимы === (если используется)
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

        # 1) синонимы из {{семантика}} — обязательно ДО clean_wikitext
        from_semantika = _extract_semantika_synonyms(raw)

        # 2) синонимы из отдельной секции (если есть)
        syn_text = synonyms_raw[k] if k < len(synonyms_raw) else ''
        from_section = split_synonyms(clean_wikitext(syn_text)) if syn_text else []

        # 3) объединяем без дублей, сохраняя порядок
        merged, seen = [], set()
        for s in from_semantika + from_section:
            if s in seen:
                continue
            seen.add(s)
            merged.append(s)

        return {
            'no': k + 1,
            'definition': clean_wikitext(raw),
            'synonyms': merged,
        }

    return [build(p) for p in enumerate(definitions)]


def _parse_meanings(wikitext: str) -> list[dict]:
    section = _get_section(wikitext, 'ru')
    lines = section.splitlines()
    headings = find_headings(lines)

    pos = _detect_pos(section)

    result: list[dict] = []
    for idx, (_, _, title) in enumerate(headings):
        if title != 'Значение':
            continue
        for item in _senses_from_heading(lines, headings, idx):
            result.append({
                'lang': 'ru',
                'pos': pos,
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

def _detect_pos(section: str) -> str | None:
    # 1) шаблоны с языковым суффиксом: {{сущ-ru}}, {{прил ru}}, {{adv ru}}
    for m in RU_POS_LANG_RE.finditer(section):
        key = m.group(1).lower()
        if key in RU_NON_POS_NAMES:
            continue
        if key in RU_POS_BY_NAME:
            return RU_POS_BY_NAME[key]

    # 2) {{phrase|...|lang=ru}} — фраза / устойчивое сочетание
    if _has_template_for_ru(section, 'phrase'):
        return 'Phrase'

    # 3) {{morph|тип=p|lang=ru|...}} — морфема
    if _has_template_for_ru(section, 'morph'):
        return 'Morpheme'

    # 4) {{Фам ин ов|...}} — фамилия
    if RU_SURNAME_RE.search(section):
        return 'Proper noun'

    # 5) голые русские POS-шаблоны
    m = RU_BARE_POS_RE.search(section)
    if m:
        return RU_POS_BY_NAME.get(m.group(1).lower())

    return None

def _extract(wikitext: str, title: str) -> dict:
    return {
        'title': title,
        'meanings': _parse_meanings(wikitext),
    }

def _find_balanced_template(text: str, name: str) -> tuple[int, int] | None:
    """Находит {{name ...}} с учётом вложенных {{...}}, возвращает (start, end)."""
    pattern = re.compile(r'\{\{\s*' + re.escape(name) + r'(?=[\s\|}])')
    m = pattern.search(text)
    if not m:
        return None
    i = m.start()
    depth = 0
    j = i
    while j < len(text) - 1:
        if text[j:j + 2] == '{{':
            depth += 1
            j += 2
        elif text[j:j + 2] == '}}':
            depth -= 1
            j += 2
            if depth == 0:
                return (i, j)
        else:
            j += 1
    return None


RU_PARSER = Parser(code='ru', matches=_matches, extract=_extract)