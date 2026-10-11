import { api } from "./client";
import { AlertaDocumento } from "./types";

export async function listarAlertas(
    apenasNaoLidos = false,
): Promise<AlertaDocumento[]> {
    const r = await api.get<AlertaDocumento[]>("/alertas/", {
    params: { apenas_nao_lidos: apenasNaoLidos },
    });
    return r.data;
}

export async function contarNaoLidos(): Promise<number> {
    const r = await api.get<{ nao_lidos: number }>("/alertas/contagem");
    return r.data.nao_lidos;
}

export async function marcarComoLido(id: string): Promise<AlertaDocumento> {
    const r = await api.patch<AlertaDocumento>(`/alertas/${id}/lido`);
    return r.data;
}

export async function marcarTodosComoLidos(): Promise<number> {
    const r = await api.post<{ marcados: number }>(
    "/alertas/marcar-todos-lidos",
    );
    return r.data.marcados;
}