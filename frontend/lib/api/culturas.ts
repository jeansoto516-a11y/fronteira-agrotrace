import { api } from "./client";
import { Cultura, CulturaCreateInput } from "./types";

export async function listarCulturas(): Promise<Cultura[]> {
    const resposta = await api.get<Cultura[]>("/culturas/");
    return resposta.data;
}

export async function criarCultura(dados: CulturaCreateInput): Promise<Cultura> {
    const resposta = await api.post<Cultura>("/culturas/", dados);
    return resposta.data;
}