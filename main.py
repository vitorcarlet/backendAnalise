# ---------------------------------------------------------------------------
# main.py – FastAPI do SASC
# ---------------------------------------------------------------------------

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Módulos internos
from app import parsing_table
from app import parsing_algorithm
from app import utils

app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Rotas de teste
# ---------------------------------------------------------------------------

@app.get("/")
async def home() -> dict:
    return {"boas-vindas": "Bem-vindo à API do SASC."}


@app.get("/test/")
async def read_root() -> dict:
    return {"message": "Testando API"}


# ---------------------------------------------------------------------------
# Rota principal de análise
#  /analyze/{analysis_type}/{grammar}/{input}
# ---------------------------------------------------------------------------

@app.get("/analyze/{analysis_type}/{grammar}/{input}")
async def analyze(input: str, grammar: str, analysis_type: str) -> dict:
    """
    Devolve:
      • parsingTable   – tabelas action/goto + terminais/não-terminais
      • stepsParsing   – passo-a-passo detalhado (para a UI)
      • errors         – lista de erros {index, lexeme, message}
      • grammar        – gramática já formatada (lista de produções)
    """
    try:
        # 1) Normaliza gramática (espaços, →, ponto final…)
        formatted_grammar = utils.grammar_formatter(grammar)
        grammar_list      = formatted_grammar.split(".")[:-1]

        # 2) Gera tabelas de análise (action/goto)
        tables = parsing_table.get_goto_action_tables(
            formatted_grammar,
            analysis_type
        )

        # 3) Executa o parser  →  retorna (steps, errors)
        steps_parsing, errors = parsing_algorithm.bottom_up_algorithm(
            tables["action_table"],
            tables["goto_table"],
            input
        )

        # 4) Resposta
        return {
            "ERROR_CODE":   0,
            "parsingTable": tables,
            "stepsParsing": steps_parsing,
            "errors":       errors,           # << NOVO CAMPO
            "grammar":      grammar_list,
        }

    except Exception as e:
        # Envuelve qualquer exceção num JSON padronizado
        return {
            "ERROR_CODE":   1,
            "errorMessage": f"Houve um erro! {e}"
        }


# ---------------------------------------------------------------------------
# Execução local (opcional)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=8000)
