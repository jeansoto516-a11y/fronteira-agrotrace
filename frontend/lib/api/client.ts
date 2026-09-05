import axios from "axios";

export const api = axios.create({
    baseURL: "http://127.0.0.1:8000",
    headers: {
    "Content-Type": "application/json",
    },
});

// Interceptor: anexa automaticamente o token de acesso em toda requisição,
// se ele existir guardado no navegador.
api.interceptors.request.use((config) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});