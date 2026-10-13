from register import ParserRegistry
from ru import RU_PARSER
from en import EN_PARSER


def default_registry() -> ParserRegistry:
    return ParserRegistry([RU_PARSER, EN_PARSER])