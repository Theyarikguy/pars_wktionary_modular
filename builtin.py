from register import ParserRegistry
from lang_parsers.ru import RU_PARSER
from lang_parsers.en import EN_PARSER


def default_registry() -> ParserRegistry:
    return ParserRegistry([RU_PARSER, EN_PARSER])