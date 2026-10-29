"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Bell } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import {
    listarNotificacoes,
    marcarNotificacaoComoLida,
    marcarTodasNotificacoesComoLidas,
    obterResumoNotificacoes,
} from "@/lib/api/notificacoes";
import { Notificacao, TipoNotificacao } from "@/lib/api/types";

const INTERVALO_MS = 60_000;

const TEXTO_TIPO: Record<TipoNotificacao, string> = {
    documento_vencendo: "Documento",
    sobreposicao_area: "Área restrita",
    etapa_pendente: "Etapa pendente",
};

const COR_TIPO: Record<TipoNotificacao, string> = {
    documento_vencendo: "bg-yellow-100 text-yellow-800",
    sobreposicao_area: "bg-red-100 text-red-800",
    etapa_pendente: "bg-blue-100 text-blue-800",
};

export default function SinoNotificacoes() {
    const { usuario } = useAuth();
    const router = useRouter();
    const [aberto, setAberto] = useState(false);
    const [naoLidos, setNaoLidos] = useState(0);
    const [notificacoes, setNotificacoes] = useState<Notificacao[]>([]);
    const [carregando, setCarregando] = useState(false);
    const raizRef = useRef<HTMLDivElement>(null);

  // A API só libera as notificações para estes dois perfis.
    const podeVer =
    usuario?.perfil === "cooperativa_admin" ||
    usuario?.perfil === "auditor_compliance";

    const atualizarContagem = useCallback(async () => {
    try {
        const resumo = await obterResumoNotificacoes();
        setNaoLidos(resumo.nao_lidos);
    } catch {
      // silencioso: o sino não deve incomodar se a API cair
    }
    }, []);

    const carregarLista = useCallback(async () => {
    setCarregando(true);
    try {
        setNotificacoes(await listarNotificacoes());
    } catch {
        toast.error("Erro ao carregar notificações");
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

  // Clicar em uma notificação marca como lida e leva para a página dela.
    async function handleAbrir(notificacao: Notificacao) {
    if (!notificacao.lido) {
        try {
        await marcarNotificacaoComoLida(notificacao.id);
        setNotificacoes((prev) =>
            prev.map((n) => (n.id === notificacao.id ? { ...n, lido: true } : n)),
        );
        setNaoLidos((n) => Math.max(0, n - 1));
        } catch {
        toast.error("Erro ao marcar como lida");
        return;
        }
    }
    setAberto(false);
    router.push(notificacao.link);
    }

    async function handleMarcarTodas() {
    try {
        await marcarTodasNotificacoesComoLidas();
        setNotificacoes((prev) => prev.map((n) => ({ ...n, lido: true })));
        setNaoLidos(0);
    } catch {
        toast.error("Erro ao marcar todas como lidas");
    }
    }

    if (!podeVer) return null;

    return (
    <div className="relative" ref={raizRef}>
        <Button
        variant="outline"
        size="sm"
        onClick={() => setAberto((v) => !v)}
        aria-label="Notificações"
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
            <span className="text-sm font-semibold">Notificações</span>
            {naoLidos > 0 && (
                <button
                type="button"
                onClick={handleMarcarTodas}
                className="text-xs underline"
                >
                Marcar todas como lidas
                </button>
            )}
            </div>

            <div className="max-h-96 overflow-y-auto">
            {carregando && notificacoes.length === 0 ? (
                <p className="p-4 text-sm text-muted-foreground">Carregando...</p>
            ) : notificacoes.length === 0 ? (
                <p className="p-4 text-sm text-muted-foreground">
                Nenhuma notificação no momento.
                </p>
            ) : (
                notificacoes.map((n) => (
                <button
                    key={n.id}
                    type="button"
                    onClick={() => handleAbrir(n)}
                    className={`block w-full border-b px-4 py-3 text-left text-sm last:border-b-0 ${
                    n.lido ? "opacity-60" : "bg-muted/50"
                    }`}
                >
                    <span
                    className={`mb-1 inline-block rounded px-2 py-0.5 text-xs ${COR_TIPO[n.tipo]}`}
                    >
                    {TEXTO_TIPO[n.tipo]}
                    </span>
                    <span className="block">{n.mensagem}</span>
                </button>
                ))
            )}
            </div>
        </div>
        )}
    </div>
    );
}