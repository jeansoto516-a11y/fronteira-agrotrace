from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import SessionLocal
from app.core.alertas import gerar_alertas
from app.core.sinalizacao import sincronizar_sinalizacoes

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


def job_sincronizar_sinalizacoes():
    """Reconfere todos os talhões contra a base de áreas restritas."""
    db = SessionLocal()
    try:
        resultado = sincronizar_sinalizacoes(db)
        print(f"[sinalizacao] rotina executada: {resultado}")
    except Exception as e:
        db.rollback()
        print(f"[sinalizacao] ERRO na rotina: {e}")
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
    scheduler.add_job(
        job_sincronizar_sinalizacoes,
        trigger="cron",
        hour=6,
        minute=5,
        id="sinalizacoes_diarias",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    # Roda uma vez ao subir a API, para cobrir o caso de o servidor
    # ter ficado desligado no horário agendado.
    job_gerar_alertas()
    job_sincronizar_sinalizacoes()


def parar_agendador():
    if scheduler.running:
        scheduler.shutdown(wait=False)