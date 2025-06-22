import re



TOKEN_SPACER = re.compile(r"([()\[\]{}+*\-/&|;=])")  # adicione mais se precisar

SYMBOLS = {
    "&": "and_symbol",
    "(": "parentheses_left_symbol",
    ")": "parentheses_right_symbol",
}

def grammar_formatter(grammar: str) -> str:
     # 1) espaça os tokens “simples”
    grammar = TOKEN_SPACER.sub(r" \1 ", grammar)
    # 2) recoloca o arrow sem espaços — QUALQUER variação “- >”, “ - > ”, etc.
    grammar = re.sub(r"\s*-\s*>", "->", grammar)
    # 3) espaços duplicados → um só
    grammar = re.sub(r"\s+", " ", grammar).strip()
    # 4) garante ponto final no fim
    if not grammar.endswith("."):
        grammar += "."
    grammar = grammar.replace(" .", ".")   # remove espaço antes do ponto
    return grammar

def symbol_treat(text: str) -> str:
    for sym, placeholder in SYMBOLS.items():
        text = text.replace(sym, placeholder)
    return text

def dict_treat(dictionary: dict[str, str]) -> dict[str, str]:
    rev = {v: k for k, v in SYMBOLS.items()}
    return {
        k: re.sub("|".join(rev), lambda m: rev[m.group(0)], v)
        for k, v in dictionary.items()
    }
