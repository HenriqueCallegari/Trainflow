<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1e3a8a,100:6d28d9&height=200&section=header&text=TrainFlow&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Powerlifting%20coaching%20made%20systematic&descAlignY=60&descSize=18" alt="TrainFlow banner" />

### Plataforma completa de gestão de treinos de powerlifting para treinadores **IPF / CBLB**

Planejamento, execução, tonelagem e calculadoras oficiais numa stack Django enxuta e pronta pra produção.

<br />

<a href="https://trainflow-r3qd.onrender.com">
  <img src="https://custom-icon-badges.demolab.com/badge/-Live%20Demo-2ea44f?style=for-the-badge&logo=rocket&logoColor=white" alt="Live demo" />
</a>
<a href="https://github.com/HenriqueCallegari/Trainflow/stargazers">
  <img src="https://custom-icon-badges.demolab.com/github/stars/HenriqueCallegari/Trainflow?style=for-the-badge&logo=star&color=f1c40f&logoColor=white&labelColor=2c2f33" alt="Stars" />
</a>
<a href="https://github.com/HenriqueCallegari/Trainflow/network/members">
  <img src="https://custom-icon-badges.demolab.com/github/forks/HenriqueCallegari/Trainflow?style=for-the-badge&logo=git-merge&color=7c3aed&logoColor=white&labelColor=2c2f33" alt="Forks" />
</a>
<a href="LICENSE">
  <img src="https://custom-icon-badges.demolab.com/badge/license-MIT-3b82f6?style=for-the-badge&logo=law&logoColor=white&labelColor=2c2f33" alt="License" />
</a>
<a href="https://github.com/HenriqueCallegari/Trainflow/commits/main">
  <img src="https://custom-icon-badges.demolab.com/github/last-commit/HenriqueCallegari/Trainflow?style=for-the-badge&logo=history&color=ef4444&logoColor=white&labelColor=2c2f33" alt="Last commit" />
</a>

<br /><br />

</div>

## Sobre

**TrainFlow** é um sistema completo onde **treinadores** planejam ciclos de powerlifting para seus atletas, e **atletas** registram a execução. O foco é o tripé **SBD** (Agacho, Supino, Terra), com classificação de exercícios por *tier* para que a tonelagem semanal reflita só o que importa.

### Diferenciais técnicos

- **Matemática oficial IPF GL Points** (fórmula Goodlift 2020), com 8 combinações de sexo × equipamento × prova, validada por **29 testes** automatizados.
- **Classificação em *tiers*** (Principal / Primeira ordem / Acessório) com agregação de tonelagem por movimento-pai.
- **Calendário por data real** — sem abstração de "bloco 1.1" que ninguém entende.
- **Papéis e permissões granulares** — atleta só edita o que executou; jamais o plano.
- **Pronto para produção**: WhiteNoise, Gunicorn, `dj-database-url`, deploy automático no Render via `build.sh`.

<br />

## Stack & Tecnologias

<div align="center">

<a href="https://skillicons.dev">
  <img src="https://skillicons.dev/icons?i=python,django,postgres,sqlite,html,css,js,git,github,vscode,linux&theme=dark" alt="Stack icons" />
</a>

<br /><br />

| Camada | Tech |
|---|---|
| **Backend** | Django 5.x · Python 3.12+ |
| **Banco** | PostgreSQL 16 em produção · SQLite em dev |
| **Frontend** | Django Templates · CSS puro (sem framework JS) |
| **Infra** | Gunicorn · WhiteNoise · Render (deploy contínuo) |
| **Testes** | pytest (29 testes da matemática IPF / 1RM / RPE) |
| **Outros** | `dj-database-url` · `python-dotenv` · `psycopg2-binary` |

</div>

<br />

## Funcionalidades

| Domínio | Recursos |
|---------|----------|
| **Planejamento** | Planos por atleta · Semanas inline (`+` / `×`) · Sessões distribuídas por frequência · Criação de exercícios direto na sessão |
| **Execução** | Atleta registra carga feita, reps, séries e RPE real · Feedback estruturado por sessão (dor, cansaço, RPE geral, sono, peso) |
| **Tonelagem** | Volume executado por semana, separado em Agacho / Supino / Terra · Variações primárias somam no movimento-pai |
| **Calculadoras** | IPF GL Points oficial · 1RM (Epley, Brzycki, RPE/RIR) · Warm-ups escalonados arredondados a 2,5 kg |
| **Biblioteca** | Exercícios com `tier` e `main_lift` · Templates de sessão · Anamnese · Log de PRs |
| **Auth** | Registro público só para treinadores · Treinador cria atletas com senha inicial · Reset de senha pelo treinador |

<br />

## Papéis e permissões

<div align="center">

|                                                       | Treinador | Atleta |
|:------------------------------------------------------|:---------:|:------:|
| Ver os próprios planos                                | ✓ (dos seus atletas) | ✓ (os seus) |
| Criar / editar / apagar plano, semana, sessão        | ✓ | ✗ |
| Editar carga feita, reps, séries, RPE real            | ✓ | ✓ (só isso) |
| Enviar feedback de sessão                             | ✗ | ✓ |
| Responder feedback                                    | ✓ | ✗ |
| Criar atletas                                         | ✓ | ✗ |
| Biblioteca de exercícios, templates, anamnese         | ✓ | ✗ |

</div>

<br />

## Capturas de tela

<div align="center">

<!-- Substitua os placeholders por screenshots reais (sugestão: docs/screenshots/) -->

| Dashboard de tonelagem | Detalhe de plano |
|:---:|:---:|
| <img src="https://via.placeholder.com/450x260/0d1117/30363d?text=Tonelagem" alt="Tonelagem" /> | <img src="https://via.placeholder.com/450x260/0d1117/30363d?text=Plano" alt="Plano" /> |

| Sessão de treino | Calculadora IPF GL |
|:---:|:---:|
| <img src="https://via.placeholder.com/450x260/0d1117/30363d?text=Sessao" alt="Sessão" /> | <img src="https://via.placeholder.com/450x260/0d1117/30363d?text=IPF+GL" alt="IPF GL" /> |

</div>

<br />

## Instalação local

```bash
git clone https://github.com/HenriqueCallegari/Trainflow.git
cd Trainflow

python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env

python manage.py migrate
python manage.py seed_exercises
python manage.py createsuperuser
python manage.py runserver
```

App em **http://127.0.0.1:8000/** — registre um treinador em `/accounts/register/`.

<br />

## Estrutura do projeto

```
trainflow/
├── apps/
│   ├── accounts/         # Auth, perfis, gestão de atletas
│   ├── training/         # Planos, sessões, exercícios, PRs, anamnese
│   └── dashboard/        # Tonelagem, calculadoras, RPE chart, home
├── trainflow/            # Settings, urls, wsgi/asgi
├── templates/            # Templates base compartilhados
├── static/               # CSS, assets
├── tests/                # pytest — matemática IPF GL / 1RM / RPE
├── build.sh              # Build script do Render
├── manage.py
├── requirements.txt
└── .env.example
```

<br />

## Fluxo de uso

1. **Treinador se registra** em `/accounts/register/`.
2. **Meus atletas → + Novo atleta** — cria login do atleta com senha inicial.
3. **+ Novo plano** escolhendo o atleta.
4. Dentro do plano, **+ Semana** adiciona semana com sessões pela frequência configurada.
5. Abrir uma sessão → adicionar exercício (existente ou criar inline).
   - **Principais / variações**: usa `% do 1RM + 1RM de referência` (carga calculada).
   - **Acessórios**: `Carga prevista (kg)` direto.
6. Atleta abre a sessão do dia, registra `carga feita / reps / séries / RPE real`, envia feedback.
7. `/tonelagem/` mostra volume executado por semana, separado por movimento-pai.

<br />

## Testes

```bash
pytest tests/test_scoring.py
```

**29 testes** cobrindo IPF GL Points, fórmulas de 1RM (Epley, Brzycki) e a tabela RPE/RIR.

<br />

## Deploy no Render

O `build.sh` na raiz cuida de tudo:

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_exercises
```

**Start command:** `gunicorn trainflow.wsgi:application`

**Variáveis de ambiente** no Web Service:

| Variável | Obrigatória | Notas |
|----------|:-----------:|-------|
| `DJANGO_SECRET_KEY` | ✓ | Gere com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | ✓ | `0` em produção |
| `DJANGO_ALLOWED_HOSTS` | ✓ | Hostname público do Render |
| `DATABASE_URL` | ✓ | Use **"Add from Database"** no painel — Internal URL do Postgres |

O `settings.py` detecta `DATABASE_URL` via `dj-database-url`; SSL é exigido automaticamente quando `DEBUG=0`.

<br />

## Estatísticas do repositório

<div align="center">

<img height="160" src="https://github-readme-stats.vercel.app/api/pin/?username=HenriqueCallegari&repo=Trainflow&theme=tokyonight&hide_border=true&bg_color=0d1117" alt="Repo card" />
<img height="160" src="https://github-readme-stats.vercel.app/api/top-langs/?username=HenriqueCallegari&repo=Trainflow&layout=compact&theme=tokyonight&hide_border=true&bg_color=0d1117" alt="Top languages" />

</div>

<br />

## Roadmap

- [ ] Exportação de relatórios (PDF / CSV) por ciclo
- [ ] Notificações por e-mail quando atleta envia feedback
- [ ] Importação de planos a partir de templates compartilhados
- [ ] App mobile (PWA) para atletas registrarem sessão offline
- [ ] Internacionalização (EN / ES)

<br />

## Autor

<div align="center">

**Henrique Callegari**

<a href="https://github.com/HenriqueCallegari">
  <img src="https://custom-icon-badges.demolab.com/badge/-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" />
</a>
<a href="mailto:henriquecallegariprof@gmail.com">
  <img src="https://custom-icon-badges.demolab.com/badge/-Email-D14836?style=for-the-badge&logo=mail&logoColor=white" alt="Email" />
</a>

</div>

<br />

## Licença

Distribuído sob a licença **MIT**. Veja [`LICENSE`](LICENSE) para mais detalhes.

<br />

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:6d28d9,100:1e3a8a&height=100&section=footer" alt="footer" />

</div>
