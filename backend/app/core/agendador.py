from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import SessionLocal
from app.core.alertas import gerar_alertas

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")


def job_gerar_alertas():
    """Abre uma sessão própria, gera os alertas e fecha a sessão."""
    db = SessionLocal()
    try:
        criados = gerar_alertas(db)
        print(f"[alertas] rotina executada: {criados} alerta(s) novo(s)")
    except Exception as e:
        db.rollback()
        print(f"[alertas] ERRO na rotina: {e}")
    finally:
        db.close()


def iniciar_agendador():
    if scheduler.running:
        return
    scheduler.add_job(
        job_gerar_alertas,
        trigger="cron",
        hour=6,
        minute=0,
        id="alertas_diarios",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    # Roda uma vez ao subir a API, para cobrir o caso de o servidor
    # ter ficado desligado no horário das 06:00.
    job_gerar_alertas()


def parar_agendador():
    if scheduler.running:
        scheduler.shutdown(wait=False)