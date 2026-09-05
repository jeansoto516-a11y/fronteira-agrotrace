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