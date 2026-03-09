"""
app.py — Servidor Flask (backend web).

O Flask é um micro-framework web para Python.
Ele mapeia URLs para funções Python (chamadas de "rotas" ou "views").

Fluxo de uma requisição:
Browser → URL → Flask encontra a função correta → função processa → retorna resposta

Por que session?
- HTTP é sem estado (cada requisição é independente)
- Flask.session usa um cookie criptografado para "lembrar" o usuário entre requisições
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import sys

# Adiciona o diretório raiz ao path para importar models
sys.path.insert(0, os.path.dirname(__file__))

from models.database import (
    init_db, criar_usuario, autenticar_usuario, buscar_usuario,
    iniciar_sessao, encerrar_sessao, salvar_partida,
    buscar_historico, buscar_ranking, buscar_estatisticas
)
from models.calcular import Calcular, Questao

app = Flask(__name__)

# SECRET_KEY: usada para criptografar os cookies de sessão
# Em produção, use uma chave longa e aleatória guardada em variável de ambiente
app.secret_key = 'mathgame-dev-secret-2024'

# Inicializa o banco de dados ao iniciar o app
init_db()


# ── HELPERS ──────────────────────────────────────────────────────────────────

def usuario_logado() -> dict | None:
    """Verifica se tem usuário na sessão e retorna seus dados."""
    uid = session.get('usuario_id')
    if uid:
        return buscar_usuario(uid)
    return None


def exige_login():
    """Redireciona para login se não estiver logado."""
    if not usuario_logado():
        return redirect(url_for('login'))
    return None


# ── ROTAS DE PÁGINAS (HTML) ───────────────────────────────────────────────────

@app.route('/')
def index():
    """Página inicial — redireciona para jogo se logado, senão para login."""
    if usuario_logado():
        return redirect(url_for('jogo'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    if usuario_logado():
        return redirect(url_for('jogo'))
    return render_template('login.html')


@app.route('/jogo')
def jogo():
    redir = exige_login()
    if redir:
        return redir
    usuario = usuario_logado()
    return render_template('jogo.html', usuario=usuario)


@app.route('/ranking')
def ranking():
    redir = exige_login()
    if redir:
        return redir
    usuario = usuario_logado()
    dados_ranking = buscar_ranking(20)
    return render_template('ranking.html', usuario=usuario, ranking=dados_ranking)


@app.route('/perfil')
def perfil():
    redir = exige_login()
    if redir:
        return redir
    usuario = usuario_logado()
    stats = buscar_estatisticas(usuario['id'])
    historico = buscar_historico(usuario['id'], 10)
    return render_template('perfil.html', usuario=usuario, stats=stats, historico=historico)


# ── ROTAS DE API (JSON) ───────────────────────────────────────────────────────
# Estas rotas são chamadas via JavaScript (fetch/AJAX), não pelo navegador diretamente.
# Retornam JSON em vez de HTML.

@app.route('/api/registrar', methods=['POST'])
def api_registrar():
    """Cria um novo usuário."""
    data = request.json
    username = data.get('username', '').strip()
    senha = data.get('senha', '')

    if not username or not senha:
        return jsonify({'ok': False, 'erro': 'Preencha todos os campos'})
    if len(username) < 3:
        return jsonify({'ok': False, 'erro': 'Username deve ter ao menos 3 caracteres'})
    if len(senha) < 4:
        return jsonify({'ok': False, 'erro': 'Senha deve ter ao menos 4 caracteres'})

    resultado = criar_usuario(username, senha)
    if resultado['ok']:
        session['usuario_id'] = resultado['id']
    return jsonify(resultado)


@app.route('/api/login', methods=['POST'])
def api_login():
    """Autentica o usuário."""
    data = request.json
    usuario = autenticar_usuario(data.get('username', ''), data.get('senha', ''))
    if usuario:
        session['usuario_id'] = usuario['id']
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'erro': 'Username ou senha inválidos'})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Remove o usuário da sessão."""
    session.clear()
    return jsonify({'ok': True})


@app.route('/api/nova-questao', methods=['POST'])
def api_nova_questao():
    """
    Gera uma nova questão.
    
    O frontend envia: {dificuldade: 1-5, sessao_id: int|null}
    Retorna: dados da questão em JSON (sem o resultado, claro!)
    """
    usuario = usuario_logado()
    if not usuario:
        return jsonify({'ok': False, 'erro': 'Não autenticado'}), 401

    data = request.json
    dificuldade = int(data.get('dificuldade', 1))

    # Inicia sessão se não existe
    sessao_id = data.get('sessao_id')
    if not sessao_id:
        sessao_id = iniciar_sessao(usuario['id'], dificuldade)

    questao = Calcular.gerar_questao(dificuldade)
    questao_dict = Calcular.questao_para_dict(questao)

    # Guardamos o resultado na sessão do servidor (não enviamos ao browser!)
    # Isso evita que o jogador faça trampa olhando o JS
    session['questao_atual'] = questao_dict
    session['sessao_jogo_id'] = sessao_id

    # Remove o resultado antes de enviar ao browser
    resposta_para_browser = {k: v for k, v in questao_dict.items() if k != 'resultado'}
    resposta_para_browser['sessao_id'] = sessao_id

    return jsonify({'ok': True, 'questao': resposta_para_browser})


@app.route('/api/responder', methods=['POST'])
def api_responder():
    """
    Recebe a resposta do usuário e verifica.
    
    Recebe: {resposta: float, tempo_resposta: float (segundos)}
    Retorna: {ok, acertou, pontos, resultado_correto, feedback}
    """
    usuario = usuario_logado()
    if not usuario:
        return jsonify({'ok': False, 'erro': 'Não autenticado'}), 401

    questao_dict = session.get('questao_atual')
    sessao_id = session.get('sessao_jogo_id')

    if not questao_dict or not sessao_id:
        return jsonify({'ok': False, 'erro': 'Nenhuma questão ativa'})

    data = request.json
    try:
        resposta_usuario = float(data.get('resposta', 0))
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'erro': 'Resposta inválida'})

    tempo_resposta = float(data.get('tempo_resposta', 30))

    # Reconstrói o objeto Questao a partir do dict guardado na sessão.
    # Precisamos remover 'enunciado' pois é um campo calculado,
    # não faz parte do dataclass Questao.
    from models.calcular import Questao
    campos_questao = {k: v for k, v in questao_dict.items() if k != 'enunciado'}
    questao = Questao(**campos_questao)

    acertou = Calcular.verificar_resposta(questao, resposta_usuario)
    pontos = Calcular.calcular_pontos(questao, acertou, tempo_resposta)

    # Salva no banco
    salvar_partida(sessao_id, usuario['id'], {
        'dificuldade': questao.dificuldade,
        'operacao': questao.operacao,
        'valor1': questao.valor1,
        'valor2': questao.valor2,
        'resultado_correto': questao.resultado,
        'resposta_usuario': resposta_usuario,
        'acertou': acertou,
        'tempo_resposta': tempo_resposta,
        'pontos': pontos,
    })

    # Limpa a questão atual da sessão
    session.pop('questao_atual', None)

    return jsonify({
        'ok': True,
        'acertou': acertou,
        'pontos': pontos,
        'resultado_correto': questao.resultado,
        'enunciado': Calcular.formatar_enunciado(questao),
    })


@app.route('/api/encerrar-sessao', methods=['POST'])
def api_encerrar_sessao():
    """Encerra a sessão de jogo atual e retorna o resumo."""
    usuario = usuario_logado()
    if not usuario:
        return jsonify({'ok': False}), 401

    sessao_id = session.get('sessao_jogo_id')
    if not sessao_id:
        return jsonify({'ok': False, 'erro': 'Nenhuma sessão ativa'})

    resumo = encerrar_sessao(sessao_id)
    session.pop('sessao_jogo_id', None)
    session.pop('questao_atual', None)

    return jsonify({'ok': True, 'resumo': resumo})


@app.route('/api/ranking')
def api_ranking():
    return jsonify({'ok': True, 'ranking': buscar_ranking(10)})


@app.route('/api/historico')
def api_historico():
    usuario = usuario_logado()
    if not usuario:
        return jsonify({'ok': False}), 401
    return jsonify({'ok': True, 'historico': buscar_historico(usuario['id'])})


if __name__ == '__main__':
    # debug=True: reinicia o servidor ao salvar arquivos (ótimo para desenvolvimento)
    # host='0.0.0.0': aceita conexões de qualquer IP (não só localhost)
    app.run(debug=True, host='0.0.0.0', port=5000)