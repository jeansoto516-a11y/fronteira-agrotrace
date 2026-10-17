"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function HomePage() {
    const { usuario, carregando } = useAuth();
    const router = useRouter();

    useEffect(() => {
    if (carregando) return;
    router.replace(usuario ? "/dashboard" : "/login");
    }, [carregando, usuario, router]);

    return <p className="p-8">Carregando...</p>;
}