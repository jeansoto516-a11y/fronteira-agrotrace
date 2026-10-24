import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auditoria import registrar_log
from app.core.deps import exigir_perfil
from app.core.relatorio import coletar_dados_relatorio
from app.core.relatorio_pdf import gerar_pdf_relatorio
from app.db.database import get_db
from app.models.log_atividade import TipoAcao
from app.models.usuario import PerfilUsuario, Usuario

router = APIRouter(tags=["Relatórios"])

# O relatório traz dados de todos os produtores do lote (inclusive
# CPF/CNPJ), por isso o produtor não pode gerá-lo.
PERMITIDOS = (
    PerfilUsuario.COOPERATIVA_ADMIN,
    PerfilUsuario.AUDITOR_COMPLIANCE,
    PerfilUsuario.EXPORTADOR,
)


def _nome_arquivo(codigo_lote: str) -> str:
    seguro = re.sub(r"[^A-Za-z0-9._-]+", "-", codigo_lote).strip("-") or "lote"
    return f"relatorio-rastreabilidade-{seguro}.pdf"


@router.get(
    "/lotes/{lote_id}/relatorio.pdf",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Relatório de rastreabilidade do lote em PDF",
        }
    },
)
def baixar_relatorio(
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(*PERMITIDOS)),
):
    """
    Gera o relatório de rastreabilidade do lote em PDF: conformidade,
    origem, mapa, documentos, áreas restritas e cadeia de custódia.
    """
    dados = coletar_dados_relatorio(db, lote_id, usuario_atual)
    if dados is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote não encontrado",
        )

    pdf = gerar_pdf_relatorio(dados)

    registrar_log(
        db,
        acao=TipoAcao.CRIAR,
        entidade="RelatorioRastreabilidade",
        usuario_id=usuario_atual.id,
        entidade_id=lote_id,
        detalhes=(
            "Relatório de rastreabilidade em PDF gerado para o lote "
            f"{dados['lote']['codigo']}"
        ),
    )

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{_nome_arquivo(dados["lote"]["codigo"])}"'
            ),
            "Cache-Control": "no-store",
        },
    )