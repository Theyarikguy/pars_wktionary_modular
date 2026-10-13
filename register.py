from parser_types import Parser


class ParserRegistry:
    def __init__(self, parsers: list[Parser] | None = None) -> None:
        self._parsers: tuple[Parser, ...] = tuple(parsers or ())

    def register(self, *parsers: Parser) -> 'ParserRegistry':
        """Возвращает новый реестр — не мутирует существующий."""
        return ParserRegistry(self._parsers + tuple(parsers))

    def get(self, lang: str) -> Parser | None:
        return next((p for p in self._parsers if p.code == lang), None)

    def detect(self, wikitext: str) -> list[Parser]:
        return [p for p in self._parsers if p.matches(wikitext)]

    def __len__(self) -> int:
        return len(self._parsers)

    def __iter__(self):
        return iter(self._parsers)