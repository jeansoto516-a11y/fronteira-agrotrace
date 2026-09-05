"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function RotaProtegida({ children }: { children: React.ReactNode }) {
    const { usuario, carregando } = useAuth();
    const router = useRouter();

    useEffect(() => {
    if (!carregando && !usuario) {
    router.push("/login");
    }
    }, [carregando, usuario, router]);

    if (carregando) {
    return <p className="p-8">Carregando...</p>;
    }

    if (!usuario) {
    return null;
    }

    return <>{children}</>;
}