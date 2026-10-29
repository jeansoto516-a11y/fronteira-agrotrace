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
import { obterResumoConformidade } from "@/lib/api/conformidade";
import { obterIndicadores } from "@/lib/api/indicadores";
import { Indicadores, ResumoConformidade, ResumoSinalizacoes } from "@/lib/api/types";

export default function DashboardPage() {
    const { usuario } = useAuth();
    const [resumo, setResumo] = useState<ResumoSinalizacoes | null>(null);
    const [conformidade, setConformidade] = useState<ResumoConformidade | null>(
    null,
    );

        const [indicadores, setIndicadores] = useState<Indicadores | null>(null);

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

    useEffect(() => {
    if (!usuario) return;
    obterResumoConformidade()
        .then(setConformidade)
        .catch(() => {
        // silencioso: o dashboard não deve quebrar se o resumo falhar
        });
    }, [usuario]);

        useEffect(() => {
    if (!usuario) return;
    obterIndicadores()
        .then(setIndicadores)
        .catch(() => {
        // silencioso: o dashboard não deve quebrar se os indicadores falharem
        });
    }, [usuario]);

    const lotesEmAtencao = conformidade
    ? conformidade.pendentes + conformidade.vencidos
    : null;

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

        <section className="grid max-w-3xl grid-cols-1 gap-4 md:grid-cols-2">
            <Link href="/conformidade" className="block">
            <Card>
                <CardHeader>
                <CardDescription>Lotes que precisam de atenção</CardDescription>
                <CardTitle
                    className={`text-3xl ${
                    lotesEmAtencao ? "text-red-700" : ""
                    }`}
                >
                    {lotesEmAtencao ?? "-"}
                </CardTitle>
                <CardDescription>
                    {conformidade
                    ? `${conformidade.vencidos} vencido(s), ${conformidade.pendentes} pendente(s) e ${conformidade.completos} completo(s). Clique para abrir o painel.`
                    : "Carregando..."}
                </CardDescription>
                </CardHeader>
            </Card>
            </Link>

            {podeVerAuditoria && (
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
            )}
        </section>

                    <section className="grid max-w-5xl grid-cols-1 gap-4 md:grid-cols-3">
            <Card>
            <CardHeader>
                <CardDescription>Volume rastreado</CardDescription>
                <CardTitle className="text-3xl">
                {indicadores
                    ? `${indicadores.volume_rastreado.total_kg.toLocaleString("pt-BR")} kg`
                    : "-"}
                </CardTitle>
                <CardDescription>
                {indicadores
                    ? `${indicadores.volume_rastreado.por_status.completo_kg.toLocaleString("pt-BR")} kg completos, ${indicadores.volume_rastreado.por_status.pendente_kg.toLocaleString("pt-BR")} kg pendentes e ${indicadores.volume_rastreado.por_status.vencido_kg.toLocaleString("pt-BR")} kg vencidos.`
                    : "Carregando..."}
                </CardDescription>
            </CardHeader>
            </Card>

            <Card>
            <CardHeader>
                <CardDescription>Lotes certificados</CardDescription>
                <CardTitle className="text-3xl">
                {indicadores
                    ? `${indicadores.lotes_certificados.percentual.toLocaleString("pt-BR")}%`
                    : "-"}
                </CardTitle>
                <CardDescription>
                {indicadores
                    ? `${indicadores.lotes_certificados.certificados} de ${indicadores.lotes_certificados.total_lotes} lote(s) com origem estão completos.`
                    : "Carregando..."}
                </CardDescription>
            </CardHeader>
            </Card>

            <Card>
            <CardHeader>
                <CardDescription>Documentos em alerta</CardDescription>
                <CardTitle
                className={`text-3xl ${
                    indicadores && indicadores.alertas.documentos_em_alerta > 0
                    ? "text-red-700"
                    : ""
                }`}
                >
                {indicadores ? indicadores.alertas.documentos_em_alerta : "-"}
                </CardTitle>
                <CardDescription>
                {indicadores
                    ? `${indicadores.alertas.vencidos} vencido(s), ${
                        indicadores.alertas.vencem_7_dias +
                        indicadores.alertas.vencem_15_dias +
                        indicadores.alertas.vencem_30_dias
                    } a vencer em até 30 dias e ${indicadores.alertas.nao_lidos} não lido(s).`
                    : "Carregando..."}
                </CardDescription>
            </CardHeader>
            </Card>
        </section>

        </main>

        

    </RotaProtegida>
    );
}