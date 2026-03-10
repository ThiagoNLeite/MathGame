# 🧮 MathGame

> Jogo de matemática interativo com ranking global, perfil de jogador e níveis de dificuldade progressivos — construído com Python e Flask.

---

## 📌 Sobre o Projeto

O **MathGame** é uma aplicação web de quiz matemático desenvolvida em Python com o micro-framework Flask. O jogador cria uma conta, escolhe um nível de dificuldade e deve responder operações matemáticas geradas aleatoriamente contra o relógio. A pontuação é calculada com base na dificuldade da questão e no tempo de resposta, incentivando respostas rápidas e precisas.

O projeto nasceu como versão terminal (`game.py`) e evoluiu para uma aplicação web completa com autenticação, banco de dados e interface moderna.

---

## ✨ Funcionalidades

- **Autenticação de usuários** — cadastro e login com senha criptografada (SHA-256)
- **5 níveis de dificuldade** — do básico (soma/subtração) ao avançado (potências e raízes)
- **6 tipos de operações** — soma, subtração, multiplicação, divisão, potência e raiz quadrada
- **Sistema de pontuação dinâmico** — quanto mais rápido e difícil, mais pontos
- **Temporizador por questão** — tempo limite varia conforme a dificuldade
- **Ranking global** — placar dos top 20 jogadores por maior pontuação
- **Perfil do jogador** — histórico de partidas, taxa de acerto, operação favorita e tempo médio de resposta
- **Anti-cheat** — o resultado das questões é armazenado no servidor (sessão Flask), nunca exposto ao browser
- **Interface dark mode** — UI responsiva com animações e tema neon

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.13, Flask 3.1 |
| Banco de dados | SQLite 3 (via módulo nativo `sqlite3`) |
| Templates | Jinja2 (HTML + CSS + JS embutidos) |
| Tipagem | `dataclasses`, type hints nativos do Python |
| Dependências | Flask, Werkzeug, Jinja2, Click, Blinker |

---

## 📁 Estrutura do Projeto

```
MathGame/
├── app.py                  # Servidor Flask — rotas HTML e API REST
├── game.py                 # Versão terminal (legado)
├── teste.py                # Scripts de teste
├── mathgame.db             # Banco de dados SQLite (gerado automaticamente)
│
├── models/
│   ├── __Init__.py
│   ├── calcular.py         # Lógica do jogo: geração de questões e pontuação
│   └── database.py         # Operações com o banco de dados
│
└── templates/
    ├── login.html          # Página de login e cadastro
    ├── jogo.html           # Interface principal do jogo
    ├── ranking.html        # Ranking global
    └── perfil.html         # Perfil e histórico do jogador
```

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.10 ou superior
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/MathGame.git
cd MathGame

# 2. Crie e ative um ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 3. Instale as dependências
pip install flask

# 4. Inicie o servidor
python app.py
```

### Acesso

Abra o navegador e acesse: **http://localhost:5000**

O banco de dados `mathgame.db` será criado automaticamente na primeira execução.

---

## 🎮 Como Jogar

1. **Crie uma conta** ou faça login na tela inicial
2. **Escolha a dificuldade** (1 a 5) antes de começar
3. **Responda a operação** exibida dentro do tempo limite
4. **Acompanhe sua pontuação** em tempo real — resposta rápida = mais pontos
5. **Encerre a sessão** para salvar seus resultados e ver o resumo
6. Consulte o **Ranking** para ver sua posição entre todos os jogadores

---

## ⚙️ Sistema de Pontuação

A pontuação é calculada pela fórmula:

```
pontos = pontos_base × multiplicador_tempo
```

Onde o `multiplicador_tempo` varia de **2.0** (resposta instantânea) a **0.5** (tempo esgotado).

| Dificuldade | Operações disponíveis | Tempo limite | Pontos base |
|:-----------:|----------------------|:------------:|:-----------:|
| 1 | Soma, Subtração | 30s | 10 |
| 2 | + Multiplicação | 25s | 20 |
| 3 | + Divisão | 20s | 40 |
| 4 | + Potência | 15s | 70 |
| 5 | + Raiz Quadrada | 12s | 100 |

---

## 🗄️ Banco de Dados

O projeto utiliza **SQLite** com três tabelas principais:

- **`usuarios`** — dados de cadastro, pontuação máxima e estatísticas gerais
- **`sessoes`** — cada sessão de jogo (agrupamento de rodadas)
- **`partidas`** — registro individual de cada questão respondida

---

## 🔌 Endpoints da API

Todas as rotas de API retornam JSON e são consumidas via `fetch` pelo frontend.

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/registrar` | Cria um novo usuário |
| `POST` | `/api/login` | Autentica o usuário |
| `POST` | `/api/logout` | Encerra a sessão |
| `POST` | `/api/nova-questao` | Gera uma nova questão |
| `POST` | `/api/responder` | Envia e valida a resposta |
| `POST` | `/api/encerrar-sessao` | Encerra a sessão de jogo |
| `GET`  | `/api/ranking` | Retorna o ranking global |
| `GET`  | `/api/historico` | Retorna o histórico do usuário |

---

## 🔐 Segurança

- Senhas armazenadas como hash **SHA-256** — nunca em texto puro
- Respostas das questões mantidas no **servidor** (sessão Flask), não expostas ao browser
- Verificação de autenticação em todas as rotas protegidas

> ⚠️ **Nota:** Este projeto é voltado para fins educacionais. Para uso em produção, recomenda-se substituir SHA-256 por **bcrypt** ou **Argon2**, utilizar HTTPS e configurar uma `SECRET_KEY` via variável de ambiente.

---

## 🧪 Versão Terminal (legado)

O arquivo `game.py` contém a versão original do jogo para terminal:

```bash
python game.py
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma _issue_ ou enviar um _pull request_.

1. Faça um fork do projeto
2. Crie sua branch: `git checkout -b feature/minha-feature`
3. Commit suas mudanças: `git commit -m 'feat: adiciona minha feature'`
4. Push para a branch: `git push origin feature/minha-feature`
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">Feito com 🐍 Python e ☕ muito café</p>
