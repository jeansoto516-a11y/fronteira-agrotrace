import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.log_atividade import LogAtividade, TipoAcao


def registrar_log(
    db: Session,
    acao: TipoAcao,
    entidade: str,
    usuario_id: Optional[uuid.UUID] = None,
    entidade_id: Optional[uuid.UUID] = None,
    detalhes: Optional[str] = None,
    ip_origem: Optional[str] = None,
) -> LogAtividade:
    """
    Registra uma ação de auditoria no banco. Deve ser chamada em toda
    rota que cria, edita, exclui uma entidade, ou processa um login.

    Exemplo de uso dentro de uma rota:
        registrar_log(
            db,
            acao=TipoAcao.CRIAR,
            entidade="Produtor",
            usuario_id=usuario_atual.id,
            entidade_id=novo_produtor.id,
            detalhes=f"Produtor {novo_produtor.nome} cadastrado",
        )
    """
    log = LogAtividade(
        usuario_id=usuario_id,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes,
        ip_origem=ip_origem,
    )
    db.add(log)
    db.commit()
    return log