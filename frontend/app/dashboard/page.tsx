"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import RotaProtegida from "@/components/RotaProtegida";
import SinoAlertas from "@/components/SinoAlertas";
import { useAuth } from "@/contexts/AuthContext";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { obterResumoSinalizacoes } from "@/lib/api/sinalizacoes";
import { ResumoSinalizacoes } from "@/lib/api/types";

export default function DashboardPage() {
    const { usuario } = useAuth();
    const [resumo, setResumo] = useState<ResumoSinalizacoes | null>(null);

    const podeVerAuditoria =
    usuario?.perfil === "auditor_compliance" ||
    usuario?.perfil === "cooperativa_admin";

    useEffect(() => {
    if (!podeVerAuditoria) return;
    obterResumoSinalizacoes()
        .then(setResumo)
        .catch(() => {
        // silencioso: o dashboard não deve quebrar se o resumo falhar
        });
    }, [podeVerAuditoria]);

    return (
    <RotaProtegida>
        <main className="p-8 space-y-6">
        <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <SinoAlertas />
        </div>
        <p>
            Bem-vindo, <strong>{usuario?.nome}</strong> ({usuario?.perfil})
        </p>

        {podeVerAuditoria && (
            <section className="grid max-w-3xl grid-cols-1 gap-4 md:grid-cols-2">
            <Link href="/auditoria" className="block">
                <Card>
                <CardHeader>
                    <CardDescription>
                    Sinalizações pendentes de revisão
                    </CardDescription>
                    <CardTitle
                    className={`text-3xl ${
                        resumo && resumo.pendentes_revisao > 0
                        ? "text-red-700"
                        : ""
                    }`}
                    >
                    {resumo ? resumo.pendentes_revisao : "-"}
                    </CardTitle>
                    <CardDescription>
                    {resumo
                        ? `${resumo.talhoes_sinalizados} talhão(ões) com sobreposição de área restrita. Clique para abrir a auditoria.`
                        : "Carregando..."}
                    </CardDescription>
                </CardHeader>
                </Card>
            </Link>
            </section>
        )}
        </main>
    </RotaProtegida>
    );
}