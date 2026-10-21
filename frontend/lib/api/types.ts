export type PerfilUsuario =
    | "produtor"
    | "cooperativa_admin"
    | "auditor_compliance"
    | "exportador";

export interface Usuario {
    id: string;
    nome: string;
    email: string;
    perfil: PerfilUsuario;
    ativo: boolean;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface Produtor {
    id: string;
    nome: string;
    cpf_cnpj: string;
    telefone: string | null;
    email: string | null;
    criado_em: string;
}

export interface ProdutorCreateInput {
    nome: string;
    cpf_cnpj: string;
    telefone?: string;
    email?: string;
}

export interface Fazenda {
    id: string;
    nome: string;
    municipio: string;
    estado: string;
    area_total_hectares: number | null;
    latitude: number | null;
    longitude: number | null;
    produtor_id: string;
    criado_em: string;
}

export interface FazendaCreateInput {
    nome: string;
    municipio: string;
    estado: string;
    area_total_hectares?: number;
    latitude?: number;
    longitude?: number;
    produtor_id: string;
}

export interface GeoJSONPolygonType {
    type: "Polygon";
    coordinates: number[][][];
}

export interface Talhao {
    id: string;
    nome_identificador: string;
    area_hectares: number | null;
    fazenda_id: string;
    criado_em: string;
    poligono: GeoJSONPolygonType;
}

export interface TalhaoCreateInput {
    nome_identificador: string;
    area_hectares?: number;
    fazenda_id: string;
    poligono: GeoJSONPolygonType;
}

export interface Cultura {
    id: string;
    nome: string;
}

export interface CulturaCreateInput {
    nome: string;
}

export interface Safra {
    id: string;
    identificacao: string;
    ano_inicio: number;
    ano_fim: number;
}

export interface SafraCreateInput {
    identificacao: string;
    ano_inicio: number;
    ano_fim: number;
}

export interface TalhaoSafraCreateInput {
    talhao_id: string;
    safra_id: string;
    cultura_id: string;
}

export interface TalhaoSafra {
    id: string;
    talhao: Talhao;
    safra: Safra;
    cultura: Cultura;
}

export interface Colheita {
    id: string;
    data_colheita: string;
    quantidade_kg: number;
    latitude: number;
    longitude: number;
    talhao_safra_id: string;
    criado_em: string;
}

export interface ColheitaCreateInput {
    data_colheita: string;
    quantidade_kg: number;
    latitude: number;
    longitude: number;
    talhao_safra_id: string;
}

export interface Lote {
    id: string;
    codigo_lote: string;
    peso_total_kg: number | null;
    criado_em: string;
}

export interface ColheitaVinculadaInput {
    colheita_id: string;
    quantidade_kg: number;
}

export interface LoteCreateInput {
    codigo_lote: string;
    colheitas: ColheitaVinculadaInput[];
}

export interface OrigemTalhao {
    talhao_id: string;
    nome_identificador: string;
    area_hectares: number | null;
    poligono: GeoJSONPolygonType;
}

export interface OrigemFazenda {
    fazenda_id: string;
    nome: string;
    municipio: string;
    estado: string;
}

export interface OrigemProdutor {
    produtor_id: string;
    nome: string;
    cpf_cnpj: string;
}

export interface ColheitaRastreada {
    colheita_id: string;
    data_colheita: string;
    quantidade_kg_no_lote: number;
    safra: string;
    cultura: string;
    talhao: OrigemTalhao;
    fazenda: OrigemFazenda;
    produtor: OrigemProdutor;
}

export interface RastreabilidadeLote {
    lote_id: string;
    codigo_lote: string;
    peso_total_kg: number | null;
    origens: ColheitaRastreada[];
}

export type TipoDocumento = 
| "car"
| "licenca_ambiental"
| "laudo_tecnico"
| "outro"; 

export type EntidadeDocumento = "fazenda" | "talhao"; 

export type SituacaoValidade = 
| "sem_validade"
| "valido"
| "a_vencer"
| "vencido";

export interface Documento {
    id: string;
    grupo_id: string;
    versao: number;
    vigente: boolean;
    tipo: TipoDocumento;
    entidade_tipo: EntidadeDocumento;
    entidade_id: string;
    nome_arquivo_original: string;
    data_validade: string | null;
    enviado_por_id: string;
    criado_em: string;
    dias_para_vencer: number | null;
    situacao_validade: SituacaoValidade;
}

export type TipoAlerta =
    | "vence_30_dias"
    | "vence_15_dias"
    | "vence_7_dias"
    | "vencido";

export interface AlertaDocumento {
    id: string;
    documento_id: string;
    tipo_alerta: TipoAlerta;
    mensagem: string;
    lido: boolean;
    criado_em: string | null;
    documento_tipo: "car" | "licenca_ambiental" | "laudo_tecnico" | "outro";
    entidade_tipo: EntidadeDocumento;
    entidade_id: string;
    data_validade: string | null;
}

export type TipoAreaRestrita = "embargo" | "desmatamento";

export type StatusRevisao = "pendente" | "confirmada" | "descartada";

export interface Sinalizacao {
    id: string;
    talhao_id: string;
    talhao_nome: string;
    fazenda_id: string;
    area_restrita_id: string;
    tipo: TipoAreaRestrita;
    identificador: string;
    descricao: string | null;
    fonte: string;
    data_referencia: string;
    area_sobreposta_hectares: number;
    percentual_do_talhao: number;
    ativa: boolean;
    detectada_em: string | null;
    atualizada_em: string | null;
    resolvida_em: string | null;
    status_revisao: StatusRevisao;
    parecer: string | null;
    revisado_por_id: string | null;
    revisado_por_nome: string | null;
    revisado_em: string | null;
}

export interface ResumoSinalizacoes {
    talhoes_sinalizados: number;
    sinalizacoes_ativas: number;
    embargos: number;
    desmatamentos: number;
    pendentes_revisao: number;
}

export interface RevisaoInput {
    decisao: "confirmada" | "descartada";
    parecer?: string;
}

export type TipoEtapa =
    | "fazenda"
    | "armazem"
    | "transporte"
    | "porto"
    | "exportacao";

export type StatusEtapa = "planejada" | "em_andamento" | "concluida";

export type ModalTransporte = "rodoviario" | "ferroviario" | "hidroviario";

export type TipoMovimentacao =
    | "entrada"
    | "saida"
    | "transferencia_responsavel"
    | "ocorrencia";

export interface OrigemFazendaCadeia {
    fazenda_id: string;
    fazenda_nome: string;
    municipio: string;
    estado: string;
    produtor_nome: string;
    quantidade_kg: number;
}

export interface UltimaMovimentacaoCadeia {
    tipo: TipoMovimentacao;
    ocorrida_em: string;
    quantidade_kg: number | null;
    responsavel: string | null;
    registrado_por_nome: string | null;
}

export interface EtapaCadeia {
    id: string | null;
    tipo: TipoEtapa;
    ordem: number;
    status: StatusEtapa;
    automatica: boolean;
    local_nome: string | null;
    municipio: string | null;
    estado: string | null;
    latitude: number | null;
    longitude: number | null;
    data_entrada: string | null;
    data_saida: string | null;
    responsavel: string | null;
    documento_referencia: string | null;
    observacoes: string | null;
    modal: ModalTransporte | null;
    placa_veiculo: string | null;
    transportadora: string | null;
    origem: string | null;
    destino: string | null;
    pais_destino: string | null;
    importador: string | null;
    navio: string | null;
    quantidade_entrada_kg: number | null;
    quantidade_saida_kg: number | null;
    diferenca_kg: number | null;
    total_movimentacoes: number;
    ultima_movimentacao: UltimaMovimentacaoCadeia | null;
    origens: OrigemFazendaCadeia[] | null;
}

export interface LinhaDoTempoLote {
    lote_id: string;
    codigo_lote: string;
    peso_total_kg: number | null;
    etapas: EtapaCadeia[];
    etapas_pendentes: TipoEtapa[];
}

export interface MovimentacaoEtapa {
    id: string;
    etapa_id: string;
    tipo: TipoMovimentacao;
    ocorrida_em: string;
    quantidade_kg: number | null;
    responsavel: string | null;
    documento_referencia: string | null;
    observacao: string | null;
    registrado_por_id: string | null;
    registrado_por_nome: string | null;
    criado_em: string | null;
}