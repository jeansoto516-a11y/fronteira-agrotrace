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