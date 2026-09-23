import { api } from "./client";
import { Colheita, ColheitaCreateInput } from "./types";

export async function listarColheitas(talhaoSafraId?: string): Promise<Colheita[]> {
    const params = talhaoSafraId ? { talhao_safra_id: talhaoSafraId } : {};
    const resposta = await api.get<Colheita[]>("/colheitas/", { params });
    return resposta.data;
}

export async function criarColheita(dados: ColheitaCreateInput): Promise<Colheita> {
    const resposta = await api.post<Colheita>("/colheitas/", dados);
    return resposta.data;
}