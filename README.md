# TrainFlow — Gestão de treinos de powerlifting (v2)

Sistema Django para treinadores de powerlifting (IPF / CBLB) gerenciarem
atletas, planejamento, execução e tonelagem. Escopo enxuto: só SBD.

## O que mudou na v2

- **Classificação em tiers**: Principal (SBD), Primeira ordem (variações que
  contam na tonelagem, ex.: supino fechado), Acessório (não conta).
- **Tonelagem executada** por semana e por movimento-pai no dashboard.
- **Feedback estruturado**: dor sim/não, cansaço sim/não, RPE geral, sono, peso.
- **Visão do plano em calendário por data real** (sem "bloco 1.1").
- **Gerenciamento de semanas inline** (+ / ×), sem formulário intermediário.
- **Criação de exercício inline** dentro da tela da sessão.
- **Apenas treinadores se registram publicamente**; treinadores criam as
  contas dos atletas com senha inicial.
- **Atleta só edita carga feita** (e afins). Não mexe no plano, nem apaga nada.
- **Acessórios simplificados** — sem 1RM/%; só séries, reps, carga, RPE (opcional),
  descanso, notas.

## Papéis

| Pode | Treinador | Atleta |
|------|:---------:|:------:|
| Ver os próprios planos | ✓ (dos seus atletas) | ✓ (os seus) |
| Criar/editar/apagar plano, semana, sessão, exercício | ✓ | ✗ |
| Editar `carga feita / reps / séries / RPE real` | ✓ | ✓ (só isso) |
| Enviar feedback de sessão | ✗ | ✓ |
| Responder feedback | ✓ | ✗ |
| Criar atletas | ✓ | ✗ |
| Biblioteca de exercícios, templates, anamnese | ✓ | ✗ |

## Instalar

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_exercises
python manage.py runserver
```

## Fluxo de uso

1. **Treinador se registra** em `/accounts/register/`.
2. **Meus atletas → + Novo atleta**: cria login do atleta com senha inicial
   (anote a senha e passe pro aluno).
3. **+ Novo plano** escolhendo o atleta.
4. **Dentro do plano**, botão **"+ Semana"** adiciona semana com sessões
   distribuídas pela frequência. Botão **"× Remover semana"** ao lado.
5. **Abrir uma sessão** → adicionar exercício (existente ou criar novo inline).
   Para principais/variações: use `% do 1RM + 1RM de referência` (carga calculada).
   Para acessórios: `Carga prevista (kg)` direto.
6. **Atleta loga**, abre a sessão do dia e, em cada exercício, registra
   `carga feita / reps / séries / RPE real`. Ao final, envia feedback.
7. **Tonelagem**: `/tonelagem/` mostra volume executado por semana, separado
   em Agacho / Supino / Terra (variações primárias somam ao movimento-pai).

## Classificação dos exercícios

Usada pelo dashboard de tonelagem:

- **Principal (SBD)** → conta.
- **Primeira ordem** (supino fechado, deficit, pausa…) → conta no movimento-pai.
- **Acessório** → não conta.

Ajuste `tier` e `main_lift` em cada exercício no admin ou em `/treinos/exercicios/`.

## Calculadoras

- **IPF GL Points** (fórmula oficial Goodlift 2020) — 8 combinações
  sexo × equipamento × prova.
- **1RM** por Epley, Brzycki e tabela RPE/RIR.
- **Warm-ups escalonados** arredondados para múltiplos de 2,5 kg.
- **Tabela RPE/RIR** completa em `/rpe/`.

## Testes

```bash
pytest tests/test_scoring.py   # 29 testes da matemática IPF GL / 1RM / RPE
```

## Deploy no Render

Ver `render.md` ou o histórico da conversa — mudanças principais:
- Adicionar `gunicorn`, `whitenoise`, `dj-database-url`, `psycopg2-binary` ao `requirements.txt`
- WhiteNoiseMiddleware após SecurityMiddleware
- `DATABASES` via `dj_database_url.config()`
- `STORAGES` com `CompressedManifestStaticFilesStorage`
- Build: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`
- Start: `gunicorn trainflow.wsgi:application`
- Env vars: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`
