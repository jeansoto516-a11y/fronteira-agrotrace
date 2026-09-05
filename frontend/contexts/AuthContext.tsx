"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api/client";
import { Usuario, TokenResponse } from "@/lib/api/types";

interface AuthContextType {
    usuario: Usuario | null;
    carregando: boolean;
    login: (email: string, senha: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [usuario, setUsuario] = useState<Usuario | null>(null);
    const [carregando, setCarregando] = useState(true);
    const router = useRouter();

  // Ao carregar a aplicação, verifica se já existe um token salvo
  // e tenta recuperar os dados do usuário logado.
    useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
        setCarregando(false);
        return;
    }

    api
        .get<Usuario>("/auth/me")
        .then((resposta) => setUsuario(resposta.data))
        .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        })
        .finally(() => setCarregando(false));
    }, []);

    async function login(email: string, senha: string) {
    const resposta = await api.post<TokenResponse>("/auth/login", { email, senha });
    const { access_token, refresh_token } = resposta.data;

    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);

    const dadosUsuario = await api.get<Usuario>("/auth/me");
    setUsuario(dadosUsuario.data);

    router.push("/dashboard");
    }

    function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUsuario(null);
    router.push("/login");
    }

    return (
    <AuthContext.Provider value={{ usuario, carregando, login, logout }}>
        {children}
    </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
    throw new Error("useAuth precisa ser usado dentro de um AuthProvider");
    }
    return context;
}