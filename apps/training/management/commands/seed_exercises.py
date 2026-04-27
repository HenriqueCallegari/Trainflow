"""Popula a biblioteca com exercícios padrão do powerlifting IPF.

Uso::

    python manage.py seed_exercises         # apenas adiciona faltantes
    python manage.py seed_exercises --reset # apaga e recria
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.training.models import ExerciseLibrary

T = ExerciseLibrary.Tier
ML = ExerciseLibrary.MainLift

# (nome, tier, main_lift, cues)
EXERCISES: list[tuple[str, str, str, str]] = [
    # Principais (SBD de competição)
    ("Agachamento Livre", T.PRINCIPAL, ML.SQUAT,
     "Bar path sobre o mediopé. Peito erguido na subida."),
    ("Supino Reto", T.PRINCIPAL, ML.BENCH,
     "Pegada legal IPF (≤ 81 cm). Cinco pontos de contato. Pausa no peito."),
    ("Terra Convencional", T.PRINCIPAL, ML.DEADLIFT,
     "Barra colada ao corpo. Empurrar o chão."),
    ("Terra Sumô", T.PRINCIPAL, ML.DEADLIFT,
     "Stance amplo; joelhos acompanhando os pés."),

    # Variações de primeira ordem (entram na tonelagem do movimento-pai)
    ("Agachamento Pausado", T.PRIMARY_VARIATION, ML.SQUAT, "Pausa 2–3 s no buraco."),
    ("Agachamento com Tempo de Descida", T.PRIMARY_VARIATION, ML.SQUAT,
     "3–5 s na excêntrica."),
    ("Front Squat", T.PRIMARY_VARIATION, ML.SQUAT, "Cotovelos altos, tronco ereto."),
    ("Agachamento High Bar", T.PRIMARY_VARIATION, ML.SQUAT, "Barra no trapézio superior."),
    ("Agachamento Box", T.PRIMARY_VARIATION, ML.SQUAT,
     "Descer controlado ao banco e explodir."),
    ("Supino Pausado Longo", T.PRIMARY_VARIATION, ML.BENCH, "Pausa 3–5 s no peito."),
    ("Supino com Pegada Fechada", T.PRIMARY_VARIATION, ML.BENCH,
     "Pegada na linha dos ombros; reforço de tríceps."),
    ("Supino com Board (2 tábuas)", T.PRIMARY_VARIATION, ML.BENCH,
     "Meio-range; foco no lockout."),
    ("Supino Spoto", T.PRIMARY_VARIATION, ML.BENCH,
     "Pausa a 2 cm do peito; mantém tensão."),
    ("Supino com Faixa", T.PRIMARY_VARIATION, ML.BENCH, "Resistência crescente."),
    ("Deficit Deadlift", T.PRIMARY_VARIATION, ML.DEADLIFT,
     "5–10 cm de elevação; reforça partida."),
    ("Block Pull / Rack Pull", T.PRIMARY_VARIATION, ML.DEADLIFT,
     "Barra em blocos; lockout."),
    ("Pause Deadlift", T.PRIMARY_VARIATION, ML.DEADLIFT, "Pausa 2 s na altura do joelho."),
    ("Romanian Deadlift", T.PRIMARY_VARIATION, ML.DEADLIFT, "Quadril para trás."),
    ("Deadlift com Faixas", T.PRIMARY_VARIATION, ML.DEADLIFT, "Resistência crescente."),

    # Acessórios (não contam na tonelagem)
    ("Remada Curvada (Barra)", T.ACCESSORY, ML.NONE, "Coluna neutra; cotovelos próximos."),
    ("Remada Cavalinho", T.ACCESSORY, ML.NONE, "Apoio no peito."),
    ("Puxada Alta", T.ACCESSORY, ML.NONE, "Pegada aberta; dorsal ativa."),
    ("Desenvolvimento Militar em Pé", T.ACCESSORY, ML.NONE, "Glúteo e abdômen ativos."),
    ("Desenvolvimento com Halteres", T.ACCESSORY, ML.NONE, "Amplitude livre."),
    ("Elevação Lateral", T.ACCESSORY, ML.NONE, "Deltóide médio."),
    ("Tríceps Testa", T.ACCESSORY, ML.NONE, "Cotovelos fixos."),
    ("Tríceps Corda", T.ACCESSORY, ML.NONE, "Abrir corda no final."),
    ("Rosca Direta", T.ACCESSORY, ML.NONE, "Cotovelo parado; sem balanço."),
    ("Face Pull", T.ACCESSORY, ML.NONE, "Cotovelos altos; saúde do ombro."),
    ("Leg Press", T.ACCESSORY, ML.NONE, "Sem hiperextensão lombar."),
    ("Afundo com Halteres", T.ACCESSORY, ML.NONE, "Unilateral."),
    ("Cadeira Extensora", T.ACCESSORY, ML.NONE, "Contração máxima no topo."),
    ("Mesa Flexora", T.ACCESSORY, ML.NONE, "Excêntrica controlada."),
    ("Panturrilha em Pé", T.ACCESSORY, ML.NONE, "Amplitude completa."),
    ("Hip Thrust", T.ACCESSORY, ML.NONE, "Contração de glúteo no topo."),
    ("Bom dia (Good Morning)", T.ACCESSORY, ML.NONE, "Coluna neutra; dobra do quadril."),
    ("Prancha", T.ACCESSORY, ML.NONE, "Alinhamento cabeça-quadril-calcanhar."),
    ("Ab Wheel", T.ACCESSORY, ML.NONE, "Sem arquear a lombar."),
    ("Hanging Leg Raise", T.ACCESSORY, ML.NONE, "Sem balanço."),
    ("Pallof Press", T.ACCESSORY, ML.NONE, "Anti-rotação."),
    ("Dead Bug", T.ACCESSORY, ML.NONE, "Lombar colada no chão."),
]


class Command(BaseCommand):
    help = "Popula a biblioteca com exercícios padrão de powerlifting."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Apaga todos os exercícios antes de recriar.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            n = ExerciseLibrary.objects.count()
            ExerciseLibrary.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Removidos {n} exercícios."))

        created = 0
        for name, tier, main_lift, cues in EXERCISES:
            _, was_created = ExerciseLibrary.objects.get_or_create(
                name=name,
                defaults={
                    "tier": tier, "main_lift": main_lift,
                    "cues": cues, "is_active": True,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed concluído. {created} novos, "
            f"{len(EXERCISES) - created} já existiam."
        ))
