import { api } from "./client";
import { Lote, LoteCreateInput, RastreabilidadeLote } from "./types";

export async function listarLotes(): Promise<Lote[]> {
    const resposta = await api.get<Lote[]>("/lotes/");
    return resposta.data;
}

export async function criarLote(dados: LoteCreateInput): Promise<Lote> {
    const resposta = await api.post<Lote>("/lotes/", dados);
    return resposta.data;
}

export async function consultarRastreabilidade(loteId: string): Promise<RastreabilidadeLote> {
    const resposta = await api.get<RastreabilidadeLote>(`/lotes/${loteId}/rastreabilidade`);
    return resposta.data;
}