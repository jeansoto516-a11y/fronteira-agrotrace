"use client";

import { useState, FormEvent } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
    const { login } = useAuth();
    const [email, setEmail] = useState("");
    const [senha, setSenha] = useState("");
    const [erro, setErro] = useState<string | null>(null);
    const [carregando, setCarregando] = useState(false);

    async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setCarregando(true);

    try {
        await login(email, senha);
    } catch {
        setErro("Email ou senha incorretos.");
    } finally {
        setCarregando(false);
    }
    }

    return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40">
        <Card className="w-full max-w-sm">
        <CardHeader>
            <CardTitle>Fronteira AgroTrace</CardTitle>
            <CardDescription>Entre com sua conta para continuar</CardDescription>
        </CardHeader>
        <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                />
            </div>
            <div className="space-y-2">
                <Label htmlFor="senha">Senha</Label>
                <Input
                id="senha"
                type="password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
                />
            </div>
            {erro && <p className="text-sm text-red-500">{erro}</p>}
            <Button type="submit" className="w-full" disabled={carregando}>
                {carregando ? "Entrando..." : "Entrar"}
            </Button>
            </form>
        </CardContent>
        </Card>
    </main>
    );
}