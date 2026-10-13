import re
from typing import List

HEADING_RE = re.compile(r'^(={1,6})\s*(.*?)\s*\1\s*$')


def clean_common(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r'\{\{[^{}]*\}\}', '', text)
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\[https?://[^\s\]]+\s+([^\]]+)\]', r'\1', text)
    text = re.sub(r'\[https?://[^\]]+\]', '', text)
    text = re.sub(r"'{2,5}", '', text)
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.S)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^[\s,;:.!?—\-]+', '', text)
    text = re.sub(r'[\s,;:.!?—\-]+$', '', text)
    text = re.sub(r'(?:\s*[,;]\s*)+', ', ', text)
    text = re.sub(r'^[\s,;:.!?—\-]+', '', text)
    text = re.sub(r'[\s,;:.!?—\-]+$', '', text)
    return text.strip()


def split_lines(text: str) -> List[str]:
    return text.splitlines()


def find_headings(lines: List[str]) -> List[tuple[int, int, str]]:
    """Возвращает [(index, level, title), ...]."""
    return [
        (i, len(m.group(1)), m.group(2).strip())
        for i, line in enumerate(lines)
        if (m := HEADING_RE.match(line))
    ]


def numbered_until(lines: List[str], start: int, level: int) -> List[str]:
    """Строки '# ...' до следующего заголовка уровня <= level."""
    out = []
    i = start + 1
    while i < len(lines):
        m = HEADING_RE.match(lines[i])
        if m and len(m.group(1)) <= level:
            break
        if lines[i].startswith('# ') and not lines[i].startswith('##'):
            out.append(lines[i][1:].strip())
        i += 1
    return out


def split_synonyms(text: str) -> List[str]:
    text = text.lstrip(':').strip()
    result, seen = [], set()
    for p in re.split(r'[,;]', text):
        p = re.sub(r'\(\s*\)', '', p).strip().strip(':,;.').strip()
        p = re.sub(r'\s+', ' ', p)
        if p and p not in {'?', '—', '-'} and p not in seen:
            seen.add(p)
            result.append(p)
    return result