"""
Follow-up scheduler: runs inside the panel process via APScheduler.
Checks published complaints every 30 minutes and creates FollowUp records
when deadlines are crossed, alerting the moderator in the panel.
"""
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from db.models import db, Denuncia, FollowUp

logger = logging.getLogger(__name__)

DIAS_ALERTA = 3
DIAS_COBRANCA = 10  # business days approximated as calendar days * 1.4


def _dias_uteis_decorridos(desde: datetime) -> int:
    """Rough business-day count (excludes weekends only, no holidays)."""
    hoje = datetime.utcnow().date()
    inicio = desde.date()
    dias = 0
    atual = inicio
    while atual < hoje:
        if atual.weekday() < 5:  # Mon–Fri
            dias += 1
        atual += timedelta(days=1)
    return dias


def _ja_tem_followup(denuncia_id: int, tipo: str) -> bool:
    return FollowUp.query.filter_by(denuncia_id=denuncia_id, tipo=tipo).first() is not None


def verificar_followups(app):
    with app.app_context():
        publicadas = Denuncia.query.filter(
            Denuncia.status == "publicada",
            Denuncia.classificacao_scorecard.is_(None),
        ).all()

        novos = 0
        for d in publicadas:
            if not d.publicada_em:
                continue

            dias_corridos = (datetime.utcnow() - d.publicada_em).days
            dias_uteis = _dias_uteis_decorridos(d.publicada_em)

            # 3-day alert (calendar days)
            if dias_corridos >= DIAS_ALERTA and not _ja_tem_followup(d.id, "alerta_3d"):
                fu = FollowUp(
                    denuncia_id=d.id,
                    tipo="alerta_3d",
                    texto=(
                        f"3 dias sem resposta do vereador {d.vereador_nome or ''}. "
                        f"Protocolo {d.protocolo} — {d.bairro}."
                    ),
                )
                db.session.add(fu)
                novos += 1

            # 10-business-day escalation
            if dias_uteis >= DIAS_COBRANCA and not _ja_tem_followup(d.id, "cobranca_10d"):
                fu = FollowUp(
                    denuncia_id=d.id,
                    tipo="cobranca_10d",
                    texto=(
                        f"10 dias úteis sem resposta — {d.vereador_nome or 'vereador não identificado'}. "
                        f"Protocolo {d.protocolo} — {d.bairro}. "
                        f"Classificar como ❌ Ignorou no scorecard."
                    ),
                )
                db.session.add(fu)
                novos += 1

        if novos:
            db.session.commit()
            logger.info("Scheduler: %d follow-up(s) gerado(s).", novos)


def iniciar_scheduler(app):
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        func=verificar_followups,
        args=[app],
        trigger="interval",
        minutes=30,
        id="followup_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Follow-up scheduler iniciado (intervalo: 30 min).")
    return scheduler
