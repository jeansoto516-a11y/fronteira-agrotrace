import { api } from "./client";
import { LinhaDoTempoLote, Lote, MovimentacaoEtapa } from "./types";

export async function listarLotesParaCadeia(): Promise<Lote[]> {
    const r = await api.get<Lote[]>("/lotes/");
    return r.data;
}

export async function obterCadeia(loteId: string): Promise<LinhaDoTempoLote> {
    const r = await api.get<LinhaDoTempoLote>(`/lotes/${loteId}/cadeia`);
    return r.data;
}

export async function listarMovimentacoes(
    etapaId: string,
): Promise<MovimentacaoEtapa[]> {
    const r = await api.get<MovimentacaoEtapa[]>(
    `/etapas/${etapaId}/movimentacoes`,
    );
    return r.data;
}