import { api } from "./client";
import { Talhao, TalhaoCreateInput } from "./types";

export async function listarTalhoes(fazendaId?: string): Promise<Talhao[]> {
    const params = fazendaId ? { fazenda_id: fazendaId } : {};
    const resposta = await api.get<Talhao[]>("/talhoes/", { params });
    return resposta.data;
}

export async function criarTalhao(dados: TalhaoCreateInput): Promise<Talhao> {
    const resposta = await api.post<Talhao>("/talhoes/", dados);
    return resposta.data;
}