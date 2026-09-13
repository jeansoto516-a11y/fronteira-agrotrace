import { api } from "./client";
import { Fazenda, FazendaCreateInput } from "./types";

export async function listarFazendas(produtorId?: string): Promise<Fazenda[]> {
    const params = produtorId ? { produtor_id: produtorId } : {};
    const resposta = await api.get<Fazenda[]>("/fazendas/", { params });
    return resposta.data;
}

export async function criarFazenda(dados: FazendaCreateInput): Promise<Fazenda> {
    const resposta = await api.post<Fazenda>("/fazendas/", dados);
    return resposta.data;
}