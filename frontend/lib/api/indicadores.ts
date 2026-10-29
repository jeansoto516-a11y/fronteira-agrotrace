import { api } from "./client";
import { Indicadores } from "./types";

export async function obterIndicadores(): Promise<Indicadores> {
    const resposta = await api.get<Indicadores>("/indicadores");
    return resposta.data;
}