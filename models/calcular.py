import math
from random import randint, choice
from dataclasses import dataclass


# ── CONSTANTES ───────────────────────────────────────────────────────────────

OPERACOES = {
    'soma':        {'simbolo': '+',  'nome': 'Soma'},
    'subtracao':   {'simbolo': '-',  'nome': 'Subtração'},
    'multiplicacao': {'simbolo': 'x', 'nome': 'Multiplicação'},
    'divisao':     {'simbolo': '÷',  'nome': 'Divisão'},
    'potencia':    {'simbolo': '^',  'nome': 'Potência'},
    'raiz':        {'simbolo': '√',  'nome': 'Raiz Quadrada'},
}

# Quais operações estão disponíveis por dificuldade
OPERACOES_POR_DIFICULDADE = {
    1: ['soma', 'subtracao'],
    2: ['soma', 'subtracao', 'multiplicacao'],
    3: ['soma', 'subtracao', 'multiplicacao', 'divisao'],
    4: ['soma', 'subtracao', 'multiplicacao', 'divisao', 'potencia'],
    5: ['soma', 'subtracao', 'multiplicacao', 'divisao', 'potencia', 'raiz'],
}

# Limite dos valores gerados por dificuldade
RANGE_POR_DIFICULDADE = {
    1: (1, 10),
    2: (1, 50),
    3: (1, 100),
    4: (1, 500),
    5: (1, 1000),
}

# Pontos base por dificuldade
PONTOS_BASE = {1: 10, 2: 20, 3: 40, 4: 70, 5: 100}

# Tempo limite em segundos por dificuldade
TEMPO_LIMITE = {1: 30, 2: 25, 3: 20, 4: 15, 5: 12}


@dataclass # dataclass é uma forma simples de criar classes que são basicamente "bolsões de dados" (data containers). Ele gera automaticamente métodos como __init__, __repr__, etc., com base nos atributos definidos.
class Questao:
    """
    Representa uma questão gerada.
    dataclass cria __init__, __repr__ automaticamente.
    """
    dificuldade: int
    operacao: str       # chave do dicionário OPERACOES
    valor1: float
    valor2: float
    resultado: float
    simbolo: str
    nome_operacao: str
    tempo_limite: int


class Calcular:
    """
    Responsável por gerar questões e calcular pontuação.
    
    Cada questão é um objeto Questao imutável, mais seguro para web.
    """

    @staticmethod
    def gerar_questao(dificuldade: int) -> Questao:
        """
        Gera uma questão aleatória para a dificuldade dada.
        Retorna um objeto Questao com todos os dados necessários.
        """
        if dificuldade not in range(1, 6):
            dificuldade = 1

        ops_disponiveis = OPERACOES_POR_DIFICULDADE[dificuldade]
        operacao = choice(ops_disponiveis)
        minv, maxv = RANGE_POR_DIFICULDADE[dificuldade]

        valor1, valor2, resultado = Calcular._gerar_valores(operacao, minv, maxv)

        return Questao(
            dificuldade=dificuldade,
            operacao=operacao,
            valor1=valor1,
            valor2=valor2,
            resultado=resultado,
            simbolo=OPERACOES[operacao]['simbolo'],
            nome_operacao=OPERACOES[operacao]['nome'],
            tempo_limite=TEMPO_LIMITE[dificuldade],
        )

    @staticmethod
    def _gerar_valores(operacao: str, minv: int, maxv: int) -> tuple[float, float, float]:
        """
        Gera valores coerentes com a operação escolhida.
        Ex: divisão sempre gera dividendo divisível pelo divisor.
        """
        if operacao == 'soma':
            v1, v2 = randint(minv, maxv), randint(minv, maxv)
            return v1, v2, v1 + v2

        elif operacao == 'subtracao':
            v1, v2 = randint(minv, maxv), randint(minv, maxv)
            # garante resultado positivo
            if v2 > v1:
                v1, v2 = v2, v1
            return v1, v2, v1 - v2

        elif operacao == 'multiplicacao':
            # limita para não gerar números impossíveis
            limite = min(maxv, 30 if maxv > 30 else maxv)
            v1, v2 = randint(minv, limite), randint(minv, limite)
            return v1, v2, v1 * v2

        elif operacao == 'divisao':
            # gera divisão exata: v2 * fator = v1
            v2 = randint(2, min(maxv, 20))
            fator = randint(1, min(maxv // v2, 20))
            v1 = v2 * fator
            return float(v1), float(v2), float(fator)

        elif operacao == 'potencia':
            base = randint(2, min(maxv, 15))
            exp = randint(2, 4)
            return float(base), float(exp), float(base ** exp)

        elif operacao == 'raiz':
            # raiz de quadrado perfeito
            raiz = randint(2, min(int(math.sqrt(maxv)), 30))
            v1 = raiz ** 2
            # valor2 é 0 pois raiz quadrada tem apenas 1 operando (mostramos como √v1)
            return float(v1), 0.0, float(raiz)

        return 0.0, 0.0, 0.0

    @staticmethod
    def verificar_resposta(questao: Questao, resposta: float) -> bool:
        """
        Verifica se a resposta está correta.
        Usa tolerância de 0.01 para erros de ponto flutuante (útil em divisões/raízes).
        """
        return abs(questao.resultado - resposta) < 0.01

    @staticmethod
    def calcular_pontos(questao: Questao, acertou: bool, tempo_resposta: float) -> int:
        """
        Calcula pontos com base em:
        - Dificuldade (pontos base maiores)
        - Tempo de resposta (mais rápido = mais pontos)
        - Se acertou ou não (0 pontos para erro)
        
        Fórmula: pontos_base * multiplicador_tempo
        Onde multiplicador_tempo vai de 0.5 (lento) a 2.0 (muito rápido)
        """
        if not acertou:
            return 0

        pontos_base = PONTOS_BASE[questao.dificuldade]
        tempo_limite = questao.tempo_limite

        # Proporção do tempo usado (0 = instantâneo, 1 = no limite)
        proporcao = min(tempo_resposta / tempo_limite, 1.0)

        # Multiplicador: 2.0 se respondeu em 0s, 0.5 se usou todo o tempo
        multiplicador = 2.0 - (1.5 * proporcao)

        return max(1, round(pontos_base * multiplicador))

    @staticmethod
    def formatar_enunciado(questao: Questao) -> str:
        """Retorna a string da operação para exibir ao usuário."""
        if questao.operacao == 'raiz':
            return f'√{questao.valor1:.0f}'
        elif questao.operacao == 'potencia':
            return f'{questao.valor1:.0f} ^ {questao.valor2:.0f}'
        else:
            v1 = int(questao.valor1) if questao.valor1 == int(questao.valor1) else questao.valor1
            v2 = int(questao.valor2) if questao.valor2 == int(questao.valor2) else questao.valor2
            return f'{v1} {questao.simbolo} {v2}'

    @staticmethod
    def questao_para_dict(questao: Questao) -> dict:
        """Converte Questao em dicionário para enviar como JSON via Flask."""
        return {
            'dificuldade': questao.dificuldade,
            'operacao': questao.operacao,
            'valor1': questao.valor1,
            'valor2': questao.valor2,
            'resultado': questao.resultado,
            'simbolo': questao.simbolo,
            'nome_operacao': questao.nome_operacao,
            'tempo_limite': questao.tempo_limite,
            'enunciado': Calcular.formatar_enunciado(questao),
        }