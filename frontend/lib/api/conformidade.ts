import { api } from "./client";
import {
    ConformidadeLote,
    ResumoConformidade,
    StatusConformidade,
} from "./types";

export async function listarConformidade(
    filtros: {
    statusConformidade?: StatusConformidade;
    incluirMotivos?: boolean;
    } = {},
): Promise<ConformidadeLote[]> {
    const r = await api.get<ConformidadeLote[]>("/conformidade/lotes", {
    params: {
        status_conformidade: filtros.statusConformidade,
        incluir_motivos: filtros.incluirMotivos ?? false,
    },
    });
    return r.data;
}

export async function obterResumoConformidade(): Promise<ResumoConformidade> {
    const r = await api.get<ResumoConformidade>("/conformidade/resumo");
    return r.data;
}