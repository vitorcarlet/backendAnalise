# Importacoes
import pandas as pd
import re

TOKEN_RE = re.compile(r"""
    [A-Za-z_][A-Za-z_0-9]* |  # identificadores e palavras-chave (id, if, while)
    \d+\.\d+ | \d+          |  # números
    \+\+|--|==|!=|<=|>=     |  # operadores de 2 chars
    [+\-*/%(){}\[\];|&]       # operadores / pontuação de 1 char
""", re.VERBOSE)

def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text)

# Obtem a tabela de analise do site: https://smlweb.cpsc.ucalgary.ca/
def get_parsing_table(grammar, analysis_type):
    if analysis_type == "ll1":
        aux_type = "ll1-table"
    elif analysis_type == "slr1":
        aux_type = "lr0"
    else:
        aux_type = analysis_type

    print(aux_type, grammar)
    url = f"https://smlweb.cpsc.ucalgary.ca/{aux_type}.php?grammar={grammar}"
    url = url.replace(" ", "%20")

    parsing_table = pd.read_html(url)
    if analysis_type == "lr0" or analysis_type == "lr1":
        return parsing_table[2]
    elif analysis_type == "ll1":
        return parsing_table[1]
    elif analysis_type == "slr1" or analysis_type == "lalr1":
        return parsing_table[3]
    else:
        return {"Erro": "Houve um erro!"}


# Converter tabela em dicionario
def get_parsing_dict(parsing_table):
    parsing_table = parsing_table.drop([0], axis=1)
    # ➜ tira espaços antes/depois de cada nome de coluna
    parsing_table.columns = parsing_table.iloc[0].str.strip()
    parsing_table = parsing_table[1:]
    parsing_table = parsing_table.fillna(" ")
    return parsing_table.to_dict()


# Separar terminais e nao-terminais
def sep_terminals_nonterminals(grammar: str):
    nonterminals, terminals = set(), []

    for rule in grammar.split("."):
        if not rule.strip():
            continue
        lhs, rhs = rule.split("->")
        lhs = lhs.strip()
        nonterminals.add(lhs)

        # tokeniza o lado direito inteiro
        for tok in tokenize(rhs):
            terminals.append(tok)

    # remove duplicados e símbolos que são não-terminais
    terminals = [t for t in set(terminals) if t not in nonterminals]
    return {"terminals": terminals, "nonterminals": list(nonterminals)}



# Separar tabela de acoes e transicoes
def get_goto_action_tables(grammar, analysis_type):
    parsing_table = get_parsing_dict(get_parsing_table(grammar, analysis_type))
    term_nterm = sep_terminals_nonterminals(grammar)

    action = {
        key: parsing_table[key]
        for key in parsing_table.keys() & term_nterm["terminals"]
    }
    action["$"] = parsing_table["$"]

    action = replace_dict(action, " ", "ERRO!")
    action = replace_dict(action, "acc", "ACEITO")
    action = replace_functions(action)
    action = replace_functions(action)

    goto = {
        key: parsing_table[key]
        for key in parsing_table.keys() & term_nterm["nonterminals"]
    }

    goto = replace_functions(goto)

    return {
        "terminals_nonterminals": term_nterm,
        "action_table": action,
        "goto_table": goto,
    }


def replace_dict(dictionary, original, final):
    for key in dictionary.keys():
        for index, value in dictionary[key].items():
            if value == original:
                dictionary[key][index] = value.replace(original, final)

    return dictionary


def replace_functions(dictionary):
    for key in dictionary.keys():
        for index, value in dictionary[key].items():
            if value[0] == "r":
                dictionary[key][index] = value.replace(
                    value, f"REDUZIR[ {value[2:-1]} ]"
                )
            elif value[0] == "s":
                # print(value[1:])
                dictionary[key][index] = value.replace(
                    value, f"EMPILHAR[ {value[1:]} ]"
                )
    return dictionary


# open_site('https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/')
# print(get_parsing_table('SOMA->A|d.A->b.A->c.', 'slr1'))
# print(get_parsing_dict(get_parsing_table('SOMA->A|d.A->b.A->c.', 'slr1')))
# print(
#    get_goto_action_tables(
#        "E->E v T.E->T.T->T and F.T->F.F->parenteses_esq E parenteses_dir.F->id.",
#        "slr1",
#    )
# )