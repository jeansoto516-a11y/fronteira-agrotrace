import { api } from "./client";
import { Documento, EntidadeDocumento, TipoDocumento } from "./types";

const MULTIPART = { "Content-Type": "multipart/form-data" };

export async function listarDocumentos(
    entidadeTipo: EntidadeDocumento,
    entidadeId: string,
    incluirHistorico = false,
): Promise<Documento[]> {
    const r = await api.get<Documento[]>("/documentos/", {
    params: {
        entidade_tipo: entidadeTipo,
        entidade_id: entidadeId,
        incluir_historico: incluirHistorico,
    },
    });
    return r.data;
}

export async function listarVencendo(dias = 30): Promise<Documento[]> {
    const r = await api.get<Documento[]>("/documentos/vencendo", {
    params: { dias },
    });
    return r.data;
}

export async function enviarDocumento(dados: {
    tipo: TipoDocumento;
    entidadeTipo: EntidadeDocumento;
    entidadeId: string;
    dataValidade?: string;
    arquivo: File;
}): Promise<Documento> {
    const form = new FormData();
    form.append("tipo", dados.tipo);
    form.append("entidade_tipo", dados.entidadeTipo);
    form.append("entidade_id", dados.entidadeId);
    if (dados.dataValidade) form.append("data_validade", dados.dataValidade);
    form.append("arquivo", dados.arquivo);
    const r = await api.post<Documento>("/documentos/", form, {
    headers: MULTIPART,
    });
    return r.data;
}

export async function enviarNovaVersao(
    documentoId: string,
    arquivo: File,
    dataValidade?: string,
): Promise<Documento> {
    const form = new FormData();
    if (dataValidade) form.append("data_validade", dataValidade);
    form.append("arquivo", arquivo);
    const r = await api.post<Documento>(
    `/documentos/${documentoId}/nova-versao`,
    form,
    { headers: MULTIPART },
    );
    return r.data;
}

// O download exige o token, então baixamos como blob e salvamos.
export async function baixarDocumento(doc: Documento): Promise<void> {
    const r = await api.get(`/documentos/${doc.id}/download`, {
    responseType: "blob",
    });
    const url = URL.createObjectURL(r.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = doc.nome_arquivo_original;
    link.click();
    URL.revokeObjectURL(url);
}

export async function excluirDocumento(id: string): Promise<void> {
    await api.delete(`/documentos/${id}`);
}