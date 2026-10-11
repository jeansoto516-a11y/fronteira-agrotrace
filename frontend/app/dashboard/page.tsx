"use client";

import RotaProtegida from "@/components/RotaProtegida";
import SinoAlertas from "@/components/SinoAlertas";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
    const { usuario, logout } = useAuth();

    return (
    <RotaProtegida>
        <main className="p-8">
                <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <SinoAlertas />
        </div>
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