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

export async function baixarRelatorioLote(loteId: string, codigoLote: string): Promise<void> {
    const resposta = await api.get<Blob>(`/lotes/${loteId}/relatorio.pdf`, {
        responseType: "blob",
    });

    const url = window.URL.createObjectURL(resposta.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = `relatorio-rastreabilidade-${codigoLote}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
}