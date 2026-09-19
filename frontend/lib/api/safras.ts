import { api } from "./client";
import { Safra, SafraCreateInput } from "./types";

export async function listarSafras(): Promise<Safra[]> {
    const resposta = await api.get<Safra[]>("/safras/");
    return resposta.data;
}

export async function criarSafra(dados: SafraCreateInput): Promise<Safra> {
    const resposta = await api.post<Safra>("/safras/", dados);
    return resposta.data;
}