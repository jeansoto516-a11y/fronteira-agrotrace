import { api } from "./client";
import { Produtor, ProdutorCreateInput } from "./types";

export async function listarProdutores(): Promise<Produtor[]> {
    const resposta = await api.get<Produtor[]>("/produtores/");
    return resposta.data;
}

export async function criarProdutor(dados: ProdutorCreateInput): Promise<Produtor> {
    const resposta = await api.post<Produtor>("/produtores/", dados);
    return resposta.data;
}