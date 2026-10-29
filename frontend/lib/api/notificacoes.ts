import { api } from "./client";
import { Notificacao, ResumoNotificacoes } from "./types";

export async function listarNotificacoes(): Promise<Notificacao[]> {
    const resposta = await api.get<Notificacao[]>("/notificacoes/");
    return resposta.data;
}

export async function obterResumoNotificacoes(): Promise<ResumoNotificacoes> {
    const resposta = await api.get<ResumoNotificacoes>("/notificacoes/resumo");
    return resposta.data;
}

export async function marcarNotificacaoComoLida(id: string): Promise<Notificacao> {
    const resposta = await api.patch<Notificacao>(`/notificacoes/${id}/lido`);
    return resposta.data;
}

export async function marcarTodasNotificacoesComoLidas(): Promise<void> {
    await api.post("/notificacoes/marcar-todas-lidas");
}