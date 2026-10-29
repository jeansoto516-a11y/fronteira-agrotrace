"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import RotaProtegida from "@/components/RotaProtegida";
import SinoAlertas from "@/components/SinoAlertas";
import MapaFazendasWrapper from "@/components/Mapa/MapaFazendasWrapper";
import { useAuth } from "@/contexts/AuthContext";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { listarFazendas } from "@/lib/api/fazendas";
import { listarTalhoes } from "@/lib/api/talhoes";
import { obterIndicadores } from "@/lib/api/indicadores";
import { Fazenda, Indicadores, Talhao } from "@/lib/api/types";

export default function DashboardExecutivoPage() {
    const { usuario } = useAuth();
    const [fazendas, setFazendas] = useState<Fazenda[]>([]);
    const [talhoes, setTalhoes] = useState<Talhao[]>([]);
    const [indicadores, setIndicadores] = useState<Indicadores | null>(null);
    const [carregandoMapa, setCarregandoMapa] = useState(true);

    useEffect(() => {
    if (!usuario) return;
    Promise.all([listarFazendas(), listarTalhoes()])
        .then(([dadosFazendas, dadosTalhoes]) => {
        setFazendas(dadosFazendas);
        setTalhoes(dadosTalhoes);
        })
        .catch(() => toast.error("Erro ao carregar o mapa de fazendas"))
        .finally(() => setCarregandoMapa(false));
    }, [usuario]);

    useEffect(() => {
    if (!usuario) return;
    obterIndicadores()
        .then(setIndicadores)
        .catch(() => {
        // silencioso: a página não deve quebrar se os indicadores falharem
        });
    }, [usuario]);

    return (
    <RotaProtegida>
        <main className="p-8 space-y-6">
        <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Dashboard executivo</h1>
            <SinoAlertas />
        </div>

        <section className="grid max-w-5xl grid-cols-1 gap-4 md:grid-cols-3">
            <Card>
            <CardHeader>
                <CardDescription>Volume rastreado</CardDescription>
                <CardTitle className="text-3xl">
                {indicadores
                    ? `${indicadores.volume_rastreado.total_kg.toLocaleString("pt-BR")} kg`
                    : "-"}
                </CardTitle>
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
            </CardHeader>
            </Card>
        </section>

        <section className="space-y-3">
            <h2 className="text-xl font-bold">Mapa geral de fazendas</h2>
            {carregandoMapa ? (
            <p>Carregando...</p>
            ) : (
            <>
                <p className="text-sm text-muted-foreground">
                {fazendas.length} fazenda(s) e {talhoes.length} talhão(ões) cadastrados.
                </p>
                <div className="border rounded-lg overflow-hidden">
                <MapaFazendasWrapper fazendas={fazendas} talhoes={talhoes} />
                </div>
            </>
            )}
        </section>
        </main>
    </RotaProtegida>
    );
}