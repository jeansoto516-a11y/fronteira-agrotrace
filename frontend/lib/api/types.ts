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

