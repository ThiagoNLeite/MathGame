"""
database.py — Configuração e acesso ao banco de dados SQLite.

Aqui ficam todas as operações relacionadas ao banco:
- Criação das tabelas (init_db)
- Operações de usuário (criar, buscar, autenticar)
- Operações de partida (salvar resultado, buscar histórico, ranking)

Por que SQLite?
- Não precisa de servidor — é um arquivo .db no disco
- Perfeito para projetos pequenos/médios
- sqlite3 já vem com o Python, sem instalar nada extra
"""

import sqlite3
import hashlib
import os
from datetime import datetime

# Caminho do arquivo do banco de dados
# os.path.dirname(__file__) pega a pasta onde este arquivo está
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'mathgame.db')


def get_connection() -> sqlite3.Connection:
    """
    Retorna uma conexão com o banco de dados.
    
    row_factory=sqlite3.Row faz com que os resultados
    se comportem como dicionários (resultado['nome'] em vez de resultado[0])
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Cria as tabelas se elas ainda não existirem.
    O 'IF NOT EXISTS' garante que rodar isso várias vezes é seguro.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            total_partidas INTEGER DEFAULT 0,
            total_acertos INTEGER DEFAULT 0,
            melhor_pontuacao INTEGER DEFAULT 0
        )
    ''')

    # Tabela de partidas (cada rodada jogada)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            dificuldade INTEGER NOT NULL,
            operacao TEXT NOT NULL,
            valor1 REAL NOT NULL,
            valor2 REAL NOT NULL,
            resultado_correto REAL NOT NULL,
            resposta_usuario REAL,
            acertou INTEGER NOT NULL DEFAULT 0,
            tempo_resposta REAL,
            pontos INTEGER DEFAULT 0,
            jogado_em TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # Tabela de sessões de jogo (agrupamento de rodadas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pontuacao_total INTEGER DEFAULT 0,
            rodadas INTEGER DEFAULT 0,
            acertos INTEGER DEFAULT 0,
            dificuldade_max INTEGER DEFAULT 1,
            iniciado_em TEXT NOT NULL,
            encerrado_em TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    conn.commit()
    conn.close()


def hash_senha(senha: str) -> str:
    """Converte senha em hash SHA-256 para não guardar senha em texto puro."""
    return hashlib.sha256(senha.encode()).hexdigest()


# ── OPERAÇÕES DE USUÁRIO ────────────────────────────────────────────────────

def criar_usuario(username: str, senha: str) -> dict:
    """
    Cria um novo usuário.
    Retorna {'ok': True, 'id': id} ou {'ok': False, 'erro': mensagem}
    """
    conn = get_connection()
    try:
        conn.execute(
            'INSERT INTO usuarios (username, senha_hash, criado_em) VALUES (?, ?, ?)',
            (username, hash_senha(senha), datetime.now().isoformat())
        )
        conn.commit()
        usuario_id = conn.execute(
            'SELECT id FROM usuarios WHERE username = ?', (username,)
        ).fetchone()['id']
        return {'ok': True, 'id': usuario_id}
    except sqlite3.IntegrityError:
        return {'ok': False, 'erro': 'Username já existe'}
    finally:
        conn.close()


def autenticar_usuario(username: str, senha: str) -> dict | None:
    """
    Verifica username e senha.
    Retorna o dicionário do usuário ou None se inválido.
    """
    conn = get_connection()
    usuario = conn.execute(
        'SELECT * FROM usuarios WHERE username = ? AND senha_hash = ?',
        (username, hash_senha(senha))
    ).fetchone()
    conn.close()
    return dict(usuario) if usuario else None


def buscar_usuario(usuario_id: int) -> dict | None:
    conn = get_connection()
    u = conn.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    conn.close()
    return dict(u) if u else None


# ── OPERAÇÕES DE SESSÃO ─────────────────────────────────────────────────────

def iniciar_sessao(usuario_id: int, dificuldade: int) -> int:
    """Cria uma nova sessão de jogo e retorna o ID."""
    conn = get_connection()
    cursor = conn.execute(
        'INSERT INTO sessoes (usuario_id, dificuldade_max, iniciado_em) VALUES (?, ?, ?)',
        (usuario_id, dificuldade, datetime.now().isoformat())
    )
    sessao_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sessao_id


def encerrar_sessao(sessao_id: int) -> dict:
    """Marca a sessão como encerrada e retorna o resumo."""
    conn = get_connection()
    conn.execute(
        'UPDATE sessoes SET encerrado_em = ? WHERE id = ?',
        (datetime.now().isoformat(), sessao_id)
    )
    conn.commit()
    sessao = conn.execute('SELECT * FROM sessoes WHERE id = ?', (sessao_id,)).fetchone()
    
    # Atualiza estatísticas do usuário
    usuario_id = sessao['usuario_id']
    pontos = sessao['pontuacao_total']
    conn.execute('''
        UPDATE usuarios SET
            total_partidas = total_partidas + ?,
            total_acertos = total_acertos + ?,
            melhor_pontuacao = MAX(melhor_pontuacao, ?)
        WHERE id = ?
    ''', (sessao['rodadas'], sessao['acertos'], pontos, usuario_id))
    conn.commit()
    result = dict(sessao)
    conn.close()
    return result


# ── OPERAÇÕES DE PARTIDA ────────────────────────────────────────────────────

def salvar_partida(sessao_id: int, usuario_id: int, dados: dict) -> int:
    """
    Salva o resultado de uma rodada e atualiza a sessão.
    dados = {dificuldade, operacao, valor1, valor2, resultado_correto,
             resposta_usuario, acertou, tempo_resposta, pontos}
    """
    conn = get_connection()
    cursor = conn.execute('''
        INSERT INTO partidas 
        (usuario_id, dificuldade, operacao, valor1, valor2, resultado_correto,
         resposta_usuario, acertou, tempo_resposta, pontos, jogado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        usuario_id,
        dados['dificuldade'],
        dados['operacao'],
        dados['valor1'],
        dados['valor2'],
        dados['resultado_correto'],
        dados.get('resposta_usuario'),
        1 if dados['acertou'] else 0,
        dados.get('tempo_resposta'),
        dados['pontos'],
        datetime.now().isoformat()
    ))
    partida_id = cursor.lastrowid

    # Atualiza totais da sessão
    conn.execute('''
        UPDATE sessoes SET
            rodadas = rodadas + 1,
            pontuacao_total = pontuacao_total + ?,
            acertos = acertos + ?
        WHERE id = ?
    ''', (dados['pontos'], 1 if dados['acertou'] else 0, sessao_id))
    
    conn.commit()
    conn.close()
    return partida_id


def buscar_historico(usuario_id: int, limite: int = 20) -> list[dict]:
    """Busca as últimas partidas do usuário."""
    conn = get_connection()
    rows = conn.execute('''
        SELECT * FROM partidas 
        WHERE usuario_id = ? 
        ORDER BY jogado_em DESC 
        LIMIT ?
    ''', (usuario_id, limite)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_ranking(limite: int = 10) -> list[dict]:
    """Retorna o ranking global por melhor pontuação."""
    conn = get_connection()
    rows = conn.execute('''
        SELECT username, melhor_pontuacao, total_partidas, total_acertos
        FROM usuarios
        WHERE total_partidas > 0
        ORDER BY melhor_pontuacao DESC
        LIMIT ?
    ''', (limite,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_estatisticas(usuario_id: int) -> dict:
    """Estatísticas detalhadas do usuário."""
    conn = get_connection()
    
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    
    # Operação favorita (a que mais acertou)
    op_fav = conn.execute('''
        SELECT operacao, COUNT(*) as total, SUM(acertou) as acertos
        FROM partidas WHERE usuario_id = ?
        GROUP BY operacao
        ORDER BY acertos DESC
        LIMIT 1
    ''', (usuario_id,)).fetchone()
    
    # Média de tempo de resposta
    tempo_medio = conn.execute('''
        SELECT AVG(tempo_resposta) as media
        FROM partidas WHERE usuario_id = ? AND tempo_resposta IS NOT NULL
    ''', (usuario_id,)).fetchone()
    
    conn.close()
    
    u = dict(usuario)
    taxa_acerto = round(u['total_acertos'] / u['total_partidas'] * 100, 1) if u['total_partidas'] > 0 else 0
    
    return {
        **u,
        'taxa_acerto': taxa_acerto,
        'operacao_favorita': dict(op_fav) if op_fav else None,
        'tempo_medio_resposta': round(tempo_medio['media'], 2) if tempo_medio and tempo_medio['media'] else None
    }