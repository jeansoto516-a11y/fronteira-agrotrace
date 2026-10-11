"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import {
    contarNaoLidos,
    listarAlertas,
    marcarComoLido,
    marcarTodosComoLidos,
} from "@/lib/api/alertas";
import { AlertaDocumento, TipoAlerta } from "@/lib/api/types";

const INTERVALO_MS = 60_000;

const TEXTO_ALERTA: Record<TipoAlerta, string> = {
    vence_30_dias: "30 dias",
    vence_15_dias: "15 dias",
    vence_7_dias: "7 dias",
    vencido: "Vencido",
};

const COR_ALERTA: Record<TipoAlerta, string> = {
    vence_30_dias: "bg-yellow-100 text-yellow-800",
    vence_15_dias: "bg-orange-100 text-orange-800",
    vence_7_dias: "bg-orange-200 text-orange-900",
    vencido: "bg-red-100 text-red-800",
};

export default function SinoAlertas() {
    const { usuario } = useAuth();
    const [aberto, setAberto] = useState(false);
    const [naoLidos, setNaoLidos] = useState(0);
    const [alertas, setAlertas] = useState<AlertaDocumento[]>([]);
    const [carregando, setCarregando] = useState(false);
    const raizRef = useRef<HTMLDivElement>(null);

  // A API só libera os alertas para estes dois perfis.
    const podeVer =
    usuario?.perfil === "cooperativa_admin" ||
    usuario?.perfil === "auditor_compliance";

    const atualizarContagem = useCallback(async () => {
    try {
        setNaoLidos(await contarNaoLidos());
    } catch {
      // silencioso: o sino não deve incomodar se a API cair
    }
    }, []);

    const carregarLista = useCallback(async () => {
    setCarregando(true);
    try {
        setAlertas(await listarAlertas());
    } catch {
        toast.error("Erro ao carregar alertas");
    } finally {
        setCarregando(false);
    }
    }, []);

  // Contador: busca ao abrir a tela e atualiza a cada 60 segundos.
    useEffect(() => {
    if (!podeVer) return;
    atualizarContagem();
    const id = setInterval(atualizarContagem, INTERVALO_MS);
    return () => clearInterval(id);
    }, [podeVer, atualizarContagem]);

  // Lista: carrega ao abrir o painel e fecha ao clicar fora.
    useEffect(() => {
    if (!aberto) return;
    carregarLista();
    function aoClicarFora(e: MouseEvent) {
        if (raizRef.current && !raizRef.current.contains(e.target as Node)) {
        setAberto(false);
        }
    }
    document.addEventListener("mousedown", aoClicarFora);
    return () => document.removeEventListener("mousedown", aoClicarFora);
    }, [aberto, carregarLista]);

    async function handleMarcarLido(alerta: AlertaDocumento) {
    if (alerta.lido) return;
    try {
        await marcarComoLido(alerta.id);
        setAlertas((prev) =>
        prev.map((a) => (a.id === alerta.id ? { ...a, lido: true } : a)),
        );
        setNaoLidos((n) => Math.max(0, n - 1));
    } catch {
        toast.error("Erro ao marcar como lido");
    }
    }

    async function handleMarcarTodos() {
    try {
        await marcarTodosComoLidos();
        setAlertas((prev) => prev.map((a) => ({ ...a, lido: true })));
        setNaoLidos(0);
    } catch {
        toast.error("Erro ao marcar todos como lidos");
    }
    }

    if (!podeVer) return null;

    return (
    <div className="relative" ref={raizRef}>
        <Button
        variant="outline"
        size="sm"
        onClick={() => setAberto((v) => !v)}
        aria-label="Alertas de documentos"
        >
        <Bell className="h-4 w-4" />
        </Button>

        {naoLidos > 0 && (
        <span className="pointer-events-none absolute -right-2 -top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-xs font-medium text-white">
            {naoLidos > 99 ? "99+" : naoLidos}
        </span>
        )}

        {aberto && (
        <div className="absolute right-0 z-50 mt-2 w-96 rounded-md border bg-popover text-popover-foreground shadow-lg">
            <div className="flex items-center justify-between border-b px-4 py-3">
            <span className="text-sm font-semibold">
                Alertas de documentos
            </span>
            {naoLidos > 0 && (
                <button
                type="button"
                onClick={handleMarcarTodos}
                className="text-xs underline"
                >
                Marcar todos como lidos
                </button>
            )}
            </div>

            <div className="max-h-96 overflow-y-auto">
            {carregando && alertas.length === 0 ? (
                <p className="p-4 text-sm text-muted-foreground">
                Carregando...
                </p>
            ) : alertas.length === 0 ? (
                <p className="p-4 text-sm text-muted-foreground">
                Nenhum alerta no momento.
                </p>
            ) : (
                alertas.map((a) => (
                <button
                    key={a.id}
                    type="button"
                    onClick={() => handleMarcarLido(a)}
                    className={`block w-full border-b px-4 py-3 text-left text-sm last:border-b-0 ${
                    a.lido ? "opacity-60" : "bg-muted/50"
                    }`}
                >
                    <span
                    className={`mb-1 inline-block rounded px-2 py-0.5 text-xs ${COR_ALERTA[a.tipo_alerta]}`}
                    >
                    {TEXTO_ALERTA[a.tipo_alerta]}
                    </span>
                    <span className="block">{a.mensagem}</span>
                </button>
                ))
            )}
            </div>

            <div className="border-t px-4 py-3">
            <Link
                href="/documentos"
                className="text-xs underline"
                onClick={() => setAberto(false)}
            >
                Ir para Gestão Documental
            </Link>
            </div>
        </div>
        )}
    </div>
    );
}