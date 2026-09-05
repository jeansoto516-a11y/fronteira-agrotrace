"use client";

import RotaProtegida from "@/components/RotaProtegida";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
    const { usuario, logout } = useAuth();

    return (
    <RotaProtegida>
        <main className="p-8">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="mt-2">
            Bem-vindo, <strong>{usuario?.nome}</strong> ({usuario?.perfil})
        </p>
        <Button className="mt-4" onClick={logout}>
            Sair
        </Button>
        </main>
    </RotaProtegida>
    );
}