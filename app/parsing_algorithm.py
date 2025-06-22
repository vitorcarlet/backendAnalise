import re

# ---------------------------------------------------------------------------
# Configurações e utilidades
# ---------------------------------------------------------------------------

SYNC_SYMBOLS = {
    ';', '}', ']', ')', '$',            # delimitadores usuais
    'a', 'b'                            # terminais simples dos exemplos-base
}

TOKEN_RE = re.compile(r"""
    [A-Za-z_][A-Za-z_0-9]* |        # identificadores / palavras-chave
    \d+\.\d+ | \d+                  |  # números
    \+\+|--|==|!=|<=|>=             |  # operadores de 2 chars
    [+\-*/%(){}\[\];|&]                # operadores / pontuação de 1 char
""", re.VERBOSE)


def tokenize(text: str) -> list[str]:
    """Separa a entrada em tokens simples (usado só para a fita)."""
    return TOKEN_RE.findall(text)

def build_error_message(action_table, state: int, token: str) -> str:
    """
    Retorna uma string amigável indicando o que era esperado naquele estado.

    • Inclui '$' quando ele é o único símbolo aceitável.
    • Coloca '$' sempre por último na lista.
    """

    # tokens cujo movimento NÃO é "ERRO!" na linha (state + 1) da tabela
    expected = [
        t for t, col in action_table.items()
        if col.get(state + 1) != "ERRO!"
    ]

    # ordena de modo que '$' apareça por último
    expected.sort(key=lambda s: (s == "$", s))

    # monta string dos esperados
    exp = ", ".join(expected) if expected else "$"

    # mensagens finais
    if token == "$":
        return f"Fim de entrada prematuro. Esperava: {exp}."
    else:
        return f"Símbolo inesperado '{token}'. Esperava: {exp}."
# ---------------------------------------------------------------------------
# Algoritmo LR (SLR / LALR / LR(1) – bottom-up)
# ---------------------------------------------------------------------------

def bottom_up_algorithm(action_table: dict,
                        goto_table: dict,
                        input: str) -> tuple[list[dict], list[dict]]:
    """
    Executa a análise sintática.

    Retorna:
        detailed_steps  – lista com logs passo-a-passo (já existente)
        errors          – lista de dicionários
                          { index, lexeme, message } para o front-end
    """
    stack:    list[str] = ["0"]
    pointer:  int       = 0
    aux_cont: int       = 0

    input_tape = tokenize(input) + ["$"]

    # -----------------------------------------------------------------------
    # Estrutura de resultado
    # -----------------------------------------------------------------------
    detailed_steps: list[dict] = [{
        "stepByStep":         ["Inicio da análise"],
        "stepByStepDetailed": [["A análise sintática será iniciada!"]],
        "stack":              stack[::-1].copy(),
        "input":              input_tape.copy(),
        "pointer":            pointer,
        "stepMarker":         ["", ""],
    }]

    errors: list[dict] = []        # ← NOVO: lista acumulada de erros

    # -----------------------------------------------------------------------
    # Loop principal
    # -----------------------------------------------------------------------
    while True:
        aux_cont += 1
        if aux_cont > 1_000:                          # trava de segurança
            break

        # rótulos convenientes
        step_by_step, step_by_step_detailed = [], []

        action, transition = ["", ""], ["", ""]

        if not stack:
            # pilha vazia → impossível recuperar
            detailed_steps.append({
                "stepByStep":         ["Erro fatal: não foi possível sincronizar."],
                "stepByStepDetailed": [["A pilha esvaziou sem estado válido."]],
                "stack":              stack[::-1].copy(),
                "input":              input_tape.copy(),
                "pointer":            pointer,
                "stepMarker":         ["", ""],
            })
            errors.append({
                "index":   pointer,
                "lexeme":  input_tape[pointer] if pointer < len(input_tape) else "$",
                "message": "Erro fatal: pilha vazia durante a recuperação."
            })
            return detailed_steps, errors

        state = int(stack[-1])
        token = input_tape[pointer]

        # -------------------------------------------------------------------
        # MODO PÂNICO – já existe, mas adicionamos logs de erro
        # -------------------------------------------------------------------
        while True:
            if not stack:
                detailed_steps.append({
                    "stepByStep":         ["Erro fatal: não foi possível sincronizar."],
                    "stepByStepDetailed": [["A pilha esvaziou sem estado válido."]],
                    "stack":              stack[::-1].copy(),
                    "input":              input_tape.copy(),
                    "pointer":            pointer,
                    "stepMarker":         ["", ""],
                })
                errors.append({
                    "index":   pointer,
                    "lexeme":  token,
                    "message": "Erro fatal: pilha vazia durante a recuperação."
                })
                return detailed_steps, errors

            state = int(stack[-1])
            if (action_table.get(token)
                    and action_table[token].get(state + 1) != "ERRO!"):
                # ponto de sincronização encontrado
                detailed_steps.append({
                    "stepByStep":         [f"Recuperação concluída em '{token}'."],
                    "stepByStepDetailed": [["Token atual pode ser consumido pelo estado da pilha."]],
                    "stack":              stack[::-1].copy(),
                    "input":              input_tape.copy(),
                    "pointer":            pointer,
                    "stepMarker":         ["", ""],
                })
                break                 # sai do while-interno (modo-pânico)
            else:
                detailed_steps.append({
                    "stepByStep":         [f"Descartando símbolo '{token}' para recuperar."],
                    "stepByStepDetailed": [["Este símbolo não pode ser consumido pelo estado atual."]],
                    "stack":              stack[::-1].copy(),
                    "input":              input_tape.copy(),
                    "pointer":            pointer,
                    "stepMarker":         ["", ""],
                })
                errors.append({
                    "index":   pointer,
                    "lexeme":  token,
                    "message": build_error_message(action_table, state, token)
                })
                pointer += 1
                if pointer >= len(input_tape):
                    detailed_steps.append({
                        "stepByStep":         ["Erro fatal: esgotou a entrada durante a recuperação."],
                        "stepByStepDetailed": [["Não foi possível sincronizar até um símbolo válido."]],
                        "stack":              stack[::-1].copy(),
                        "input":              input_tape.copy(),
                        "pointer":            pointer,
                        "stepMarker":         ["", ""],
                    })
                    return detailed_steps, errors
                token = input_tape[pointer]

        # -------------------------------------------------------------------
        # PARTE NORMAL DO ALGORITMO (SHIFT / REDUCE / ACC / ERRO)
        # -------------------------------------------------------------------
        action_cell = action_table[token][state + 1]  # (+1: cabeçalho)
        action_movement = action_cell.split("[")

        action[0] = state + 1
        action[1] = token

        # ----- ERRO LÉXICO (token não existe na tabela) --------------------
        if token not in action_table:
            step_by_step.append("A entrada foi rejeitada devido a um erro léxico!")
            step_by_step_detailed.append([
                f"A entrada tem um erro léxico em: {token}.",
                "Um token identificado não pertence à gramática da linguagem fonte.",
            ])
            detailed_steps.append({
                "stepByStep":         step_by_step.copy(),
                "stepByStepDetailed": step_by_step_detailed.copy(),
                "stack":              stack[::-1].copy(),
                "input":              input_tape.copy(),
                "pointer":            pointer,
                "stepMarker":         ["", ""],
            })
            errors.append({
                "index":   pointer,
                "lexeme":  token,
                "message": "Erro léxico: token desconhecido."
            })
            return detailed_steps, errors

        action_tag = action_movement[0].strip()

        # normaliza argumento de shift/reduce
        if action_tag not in ("ACEITO", "ERRO!"):
            action_movement[1] = action_movement[1].strip(" ]")

        # log padrão
        step_by_step.append(f"AÇÃO[{token}, {state}] => {action_cell}")
        step_by_step_detailed.append([
            "Realizada uma busca na tabela de ações.",
            f"Na coluna >>{token}<< e linha >>{state}<< encontrado movimento: {action_cell}",
        ])
        detailed_steps.append({
            "stepByStep":         step_by_step.copy(),
            "stepByStepDetailed": step_by_step_detailed.copy(),
            "stack":              stack[::-1].copy(),
            "input":              input_tape.copy(),
            "pointer":            pointer,
            "stepMarker":         [token, state],
        })

        # -------------------------------------------------------------------
        # Movimento REDUZIR
        # -------------------------------------------------------------------
        if action_tag.startswith("REDUZIR"):
            array_action_movement = action_movement[1].split(" ")

            reduce_elements = array_action_movement[2:]
            qt_unstack = 2 * len(reduce_elements)
            for _ in range(qt_unstack):
                stack.pop()

            # logging (mesmo que antes) …

            transition[0] = int(stack[-1]) + 1
            transition[1] = array_action_movement[0]
            goto_movement = goto_table[transition[1]][transition[0]]

            stack.append(array_action_movement[0])
            stack.append(str(int(goto_movement.split()[1])))

        # -------------------------------------------------------------------
        # Movimento SHIFT
        # -------------------------------------------------------------------
        elif action_tag.startswith("EMPILHAR"):
            stack.append(token)
            stack.append(action_movement[1])
            pointer += 1

        # -------------------------------------------------------------------
        # Entrada aceita
        # -------------------------------------------------------------------
        elif action_tag == "ACEITO":
            detailed_steps.append({
                "stepByStep":         ["A entrada foi aceita!"],
                "stepByStepDetailed": [["Aceito"]],
                "stack":              stack[::-1].copy(),
                "input":              input_tape.copy(),
                "pointer":            pointer,
                "stepMarker":         ["", ""],
            })
            break

        # -------------------------------------------------------------------
        # ERRO! – dispara modo-pânico
        # -------------------------------------------------------------------
        elif action_tag == "ERRO!":
            msg = build_error_message(action_table, state, token)
            errors.append({
                "index":   pointer,
                "lexeme":  token,
                "message": msg
            })

            detailed_steps.append({
                "stepByStep":         [msg, "Entrando em modo pânico…"],
                "stepByStepDetailed": [[msg],
                                       ["O analisador tentará descartar símbolos "
                                        "até encontrar um ponto de sincronização."]],
                "stack":              stack[::-1].copy(),
                "input":              input_tape.copy(),
                "pointer":            pointer,
                "stepMarker":         ["", ""],
            })

            # --- a) DESCARTE DE ENTRADA ------------------------------------
            while token not in SYNC_SYMBOLS:
                pointer += 1
                if pointer >= len(input_tape):
                    return detailed_steps, errors
                token = input_tape[pointer]

            # --- b) PODA DA PILHA -----------------------------------------
            recovered = False
            while stack:
                state = int(stack[-1])
                if action_table[token][state + 1] != "ERRO!":
                    recovered = True
                    break
                stack.pop()          # estado
                if stack:
                    stack.pop()      # símbolo

            if not recovered:
                detailed_steps.append({
                    "stepByStep":         ["Erro fatal: não foi possível sincronizar."],
                    "stepByStepDetailed": [["A pilha esvaziou sem estado válido."]],
                    "stack":              stack[::-1].copy(),
                    "input":              input_tape.copy(),
                    "pointer":            pointer,
                    "stepMarker":         ["", ""],
                })
                errors.append({
                    "index":   pointer,
                    "lexeme":  token,
                    "message": "Erro fatal: pilha vazia durante recuperação."
                })
                return detailed_steps, errors

            # log de sincronização
            detailed_steps.append({
                "stepByStep":         [f"Sincronizado em '{token}'. Continuando análise…"],
                "stepByStepDetailed": [["Símbolo de sincronização encontrado.",
                                        "Estado válido localizado na pilha. "
                                        "Retomando o laço principal."]],
                "stack":              stack[::-1].copy(),
                "input":              input_tape.copy(),
                "pointer":            pointer,
                "stepMarker":         ["", ""],
            })
            continue        # volta ao topo do while principal

    # -----------------------------------------------------------------------
    # Fim da análise
    # -----------------------------------------------------------------------
    return detailed_steps, errors
