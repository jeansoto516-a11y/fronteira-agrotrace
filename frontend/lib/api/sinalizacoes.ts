import { api } from "./client";
import {
    ResumoSinalizacoes,
    RevisaoInput,
    Sinalizacao,
    StatusRevisao,
    TipoAreaRestrita,
} from "./types";

export async function listarSinalizacoes(
    filtros: {
    apenasAtivas?: boolean;
    tipo?: TipoAreaRestrita;
    statusRevisao?: StatusRevisao;
    } = {},
): Promise<Sinalizacao[]> {
    const r = await api.get<Sinalizacao[]>("/sinalizacoes/", {
    params: {
        apenas_ativas: filtros.apenasAtivas ?? true,
        tipo: filtros.tipo,
        status_revisao: filtros.statusRevisao,
        limit: 200,
    },
    });
    return r.data;
}

export async function obterResumoSinalizacoes(): Promise<ResumoSinalizacoes> {
    const r = await api.get<ResumoSinalizacoes>("/sinalizacoes/resumo");
    return r.data;
}

export async function revisarSinalizacao(
    id: string,
    dados: RevisaoInput,
): Promise<Sinalizacao> {
    const r = await api.patch<Sinalizacao>(`/sinalizacoes/${id}/revisao`, dados);
    return r.data;
}