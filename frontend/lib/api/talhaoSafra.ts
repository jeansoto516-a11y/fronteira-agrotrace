import { api } from "./client";
import { TalhaoSafra, TalhaoSafraCreateInput } from "./types";

export async function listarVinculos(): Promise<TalhaoSafra[]> {
    const resposta = await api.get<TalhaoSafra[]>("/talhao-safra/");
    return resposta.data;
}

export async function criarVinculo(dados: TalhaoSafraCreateInput): Promise<TalhaoSafra> {
    const resposta = await api.post<TalhaoSafra>("/talhao-safra/", dados);
    return resposta.data;
}