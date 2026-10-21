"use client";

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { toast } from "sonner";
import RotaProtegida from "@/components/RotaProtegida";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    listarLotesParaCadeia,
    listarMovimentacoes,
    obterCadeia,
} from "@/lib/api/cadeia";
import {
    EtapaCadeia,
    LinhaDoTempoLote,
    Lote,
    ModalTransporte,
    MovimentacaoEtapa,
    StatusEtapa,
    TipoEtapa,
    TipoMovimentacao,
} from "@/lib/api/types";

const ROTULO_TIPO: Record<TipoEtapa, string> = {
    fazenda: "Fazenda (origem)",
    armazem: "Armazém",
    transporte: "Transporte",
    porto: "Porto",
    exportacao: "Exportação",
};

const ROTULO_STATUS: Record<StatusEtapa, string> = {
    planejada: "Planejada",
    em_andamento: "Em andamento",
    concluida: "Concluída",
};

const COR_STATUS: Record<StatusEtapa, string> = {
    planejada: "bg-gray-100 text-gray-700",
    em_andamento: "bg-blue-100 text-blue-800",
    concluida: "bg-green-100 text-green-800",
};

const COR_PONTO: Record<StatusEtapa, string> = {
    planejada: "bg-gray-400",
    em_andamento: "bg-blue-600",
    concluida: "bg-green-600",
};

const ROTULO_MODAL: Record<ModalTransporte, string> = {
    rodoviario: "Rodoviário",
    ferroviario: "Ferroviário",
    hidroviario: "Hidroviário",
};

const ROTULO_MOVIMENTACAO: Record<TipoMovimentacao, string> = {
    entrada: "Entrada",
    saida: "Saída",
    transferencia_responsavel: "Transferência de responsável",
    ocorrencia: "Ocorrência",
};

const CLASSE_SELECT =
    "h-9 min-w-64 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

function formatarDataHora(iso: string | null) {
    if (!iso) return null;
    return new Date(iso).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    });
}

function formatarKg(n: number | null) {
    if (n === null || n === undefined) return null;
    return `${n.toLocaleString("pt-BR", { maximumFractionDigits: 3 })} kg`;
}

function Campo({ rotulo, valor }: { rotulo: string; valor: ReactNode }) {
    if (valor === null || valor === undefined || valor === "") return null;
    return (
    <div>
        <dt className="text-xs text-muted-foreground">{rotulo}</dt>
        <dd className="text-sm">{valor}</dd>
    </div>
    );
}

interface EstadoHistorico {
    aberto: boolean;
    carregando: boolean;
    itens: MovimentacaoEtapa[] | null;
}

function CartaoEtapa({
    etapa,
    historico,
    onAlternarHistorico,
}: {
    etapa: EtapaCadeia;
    historico: EstadoHistorico | undefined;
    onAlternarHistorico: (etapa: EtapaCadeia) => void;
}) {
    const local = [
    etapa.local_nome,
    [etapa.municipio, etapa.estado].filter(Boolean).join("/"),
    ]
    .filter(Boolean)
    .join(" - ");

    const rota =
    etapa.origem || etapa.destino
        ? `${etapa.origem ?? "?"} → ${etapa.destino ?? "?"}`
        : null;

    const temQuantidades =
    etapa.quantidade_entrada_kg !== null ||
    etapa.quantidade_saida_kg !== null;

    return (
    <div className="space-y-3 rounded-lg border bg-card p-4">
        <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-medium">
            {etapa.automatica ? "" : `${etapa.ordem}. `}
            {ROTULO_TIPO[etapa.tipo]}
        </h3>
        <span
            className={`rounded px-2 py-0.5 text-xs ${COR_STATUS[etapa.status]}`}
        >
            {ROTULO_STATUS[etapa.status]}
        </span>
        {etapa.automatica && (
            <span className="rounded bg-purple-100 px-2 py-0.5 text-xs text-purple-800">
            Automática (rastreabilidade)
            </span>
        )}
        </div>

        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-3">
        <Campo rotulo="Local" valor={local} />
        <Campo rotulo="Entrada" valor={formatarDataHora(etapa.data_entrada)} />
        <Campo rotulo="Saída" valor={formatarDataHora(etapa.data_saida)} />
        <Campo rotulo="Responsável atual" valor={etapa.responsavel} />
        <Campo rotulo="Documento" valor={etapa.documento_referencia} />
        <Campo
            rotulo="Modal"
            valor={etapa.modal ? ROTULO_MODAL[etapa.modal] : null}
        />
        <Campo rotulo="Trajeto" valor={rota} />
        <Campo rotulo="Placa" valor={etapa.placa_veiculo} />
        <Campo rotulo="Transportadora" valor={etapa.transportadora} />
        <Campo rotulo="País de destino" valor={etapa.pais_destino} />
        <Campo rotulo="Importador" valor={etapa.importador} />
        <Campo rotulo="Navio" valor={etapa.navio} />
        <Campo rotulo="Observações" valor={etapa.observacoes} />
        </dl>

        {etapa.origens && etapa.origens.length > 0 && (
        <div>
            <p className="mb-1 text-xs text-muted-foreground">
            Fazendas de origem
            </p>
            <ul className="space-y-1 text-sm">
            {etapa.origens.map((o) => (
                <li key={o.fazenda_id}>
                <strong>{o.fazenda_nome}</strong> ({o.municipio}/{o.estado}),
                produtor {o.produtor_nome}: {formatarKg(o.quantidade_kg)}
                </li>
            ))}
            </ul>
        </div>
        )}

        {temQuantidades && (
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span>
            Entrou: <strong>{formatarKg(etapa.quantidade_entrada_kg) ?? "-"}</strong>
            </span>
            <span>
            Saiu: <strong>{formatarKg(etapa.quantidade_saida_kg) ?? "-"}</strong>
            </span>
            {etapa.diferenca_kg !== null && (
            <span
                className={
                etapa.diferenca_kg !== 0 ? "font-medium text-amber-700" : ""
                }
            >
                Diferença: {formatarKg(etapa.diferenca_kg)}
            </span>
            )}
        </div>
        )}

        {etapa.ultima_movimentacao && (
        <p className="text-xs text-muted-foreground">
            Última movimentação:{" "}
            {ROTULO_MOVIMENTACAO[etapa.ultima_movimentacao.tipo]} em{" "}
            {formatarDataHora(etapa.ultima_movimentacao.ocorrida_em)}
            {etapa.ultima_movimentacao.registrado_por_nome &&
            `, registrada por ${etapa.ultima_movimentacao.registrado_por_nome}`}
        </p>
        )}

        {etapa.id && etapa.total_movimentacoes > 0 && (
        <div className="space-y-2">
            <Button
            variant="outline"
            size="sm"
            onClick={() => onAlternarHistorico(etapa)}
            >
            {historico?.aberto
                ? "Ocultar histórico"
                : `Ver histórico (${etapa.total_movimentacoes})`}
            </Button>

            {historico?.aberto && (
            <div className="rounded-md border bg-muted/30 p-3">
                {historico.carregando && (
                <p className="text-sm text-muted-foreground">Carregando...</p>
                )}
                {historico.itens && (
                <ul className="space-y-3">
                    {historico.itens.map((m) => (
                    <li key={m.id} className="text-sm">
                        <p>
                        <strong>{ROTULO_MOVIMENTACAO[m.tipo]}</strong> em{" "}
                        {formatarDataHora(m.ocorrida_em)}
                        {m.quantidade_kg !== null &&
                            `, ${formatarKg(m.quantidade_kg)}`}
                        </p>
                        <p className="text-xs text-muted-foreground">
                        {m.responsavel && `Responsável: ${m.responsavel}. `}
                        {m.documento_referencia &&
                            `Documento: ${m.documento_referencia}. `}
                        {`Registrada por ${m.registrado_por_nome ?? "usuário removido"}.`}
                        </p>
                        {m.observacao && (
                        <p className="text-xs">{m.observacao}</p>
                        )}
                    </li>
                    ))}
                </ul>
                )}
            </div>
            )}
        </div>
        )}
    </div>
    );
}

export default function CadeiaPage() {
    const [lotes, setLotes] = useState<Lote[]>([]);
    const [loteId, setLoteId] = useState("");
    const [cadeia, setCadeia] = useState<LinhaDoTempoLote | null>(null);
    const [carregando, setCarregando] = useState(false);
    const [historicos, setHistoricos] = useState<Record<string, EstadoHistorico>>(
    {},
    );

    useEffect(() => {
    listarLotesParaCadeia()
        .then((dados) => {
        setLotes(dados);
        if (dados.length > 0) setLoteId(dados[0].id);
        })
        .catch(() => toast.error("Erro ao carregar os lotes"));
    }, []);

    const carregarCadeia = useCallback(async () => {
    if (!loteId) return;
    setCarregando(true);
    setHistoricos({});
    try {
        setCadeia(await obterCadeia(loteId));
    } catch {
        setCadeia(null);
        toast.error("Erro ao carregar a cadeia do lote");
    } finally {
        setCarregando(false);
    }
    }, [loteId]);

    useEffect(() => {
    carregarCadeia();
    }, [carregarCadeia]);

    async function alternarHistorico(etapa: EtapaCadeia) {
    if (!etapa.id) return;
    const id = etapa.id;
    const atual = historicos[id];

    if (atual?.aberto) {
        setHistoricos((h) => ({ ...h, [id]: { ...atual, aberto: false } }));
        return;
    }
    if (atual?.itens) {
        setHistoricos((h) => ({ ...h, [id]: { ...atual, aberto: true } }));
        return;
    }

    setHistoricos((h) => ({
        ...h,
        [id]: { aberto: true, carregando: true, itens: null },
    }));
    try {
        const itens = await listarMovimentacoes(id);
        setHistoricos((h) => ({
        ...h,
        [id]: { aberto: true, carregando: false, itens },
        }));
    } catch {
        toast.error("Erro ao carregar o histórico da etapa");
        setHistoricos((h) => ({
        ...h,
        [id]: { aberto: false, carregando: false, itens: null },
        }));
    }
    }

    const registradas = cadeia?.etapas.filter((e) => !e.automatica) ?? [];
    const concluidas = registradas.filter((e) => e.status === "concluida");
    const exportada = registradas.some(
    (e) => e.tipo === "exportacao" && e.status === "concluida",
    );
    const emAndamento = registradas.find((e) => e.status === "em_andamento");

    let situacao = "Aguardando a próxima etapa";
    if (registradas.length === 0) situacao = "Nenhuma etapa registrada";
    else if (exportada) situacao = "Cadeia concluída (exportado)";
    else if (emAndamento)
    situacao = `Em andamento: ${ROTULO_TIPO[emAndamento.tipo]}`;

    return (
    <RotaProtegida>
        <main className="space-y-6 p-8">
        <h1 className="text-2xl font-bold">Cadeia de custódia por lote</h1>

        {lotes.length === 0 ? (
            <p className="text-sm text-muted-foreground">
            Nenhum lote cadastrado ainda.
            </p>
        ) : (
            <section className="flex flex-wrap items-end gap-4">
            <div className="space-y-2">
                <Label htmlFor="lote">Lote</Label>
                <select
                id="lote"
                className={CLASSE_SELECT}
                value={loteId}
                onChange={(e) => setLoteId(e.target.value)}
                >
                {lotes.map((l) => (
                    <option key={l.id} value={l.id}>
                    {l.codigo_lote}
                    </option>
                ))}
                </select>
            </div>
            <Button
                variant="outline"
                onClick={carregarCadeia}
                disabled={carregando}
            >
                {carregando ? "Atualizando..." : "Atualizar"}
            </Button>
            </section>
        )}

        {cadeia && (
            <>
            <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <Card size="sm">
                <CardHeader>
                    <CardDescription>Lote</CardDescription>
                    <CardTitle className="text-lg">{cadeia.codigo_lote}</CardTitle>
                </CardHeader>
                </Card>
                <Card size="sm">
                <CardHeader>
                    <CardDescription>Peso total</CardDescription>
                    <CardTitle className="text-lg">
                    {formatarKg(cadeia.peso_total_kg) ?? "-"}
                    </CardTitle>
                </CardHeader>
                </Card>
                <Card size="sm">
                <CardHeader>
                    <CardDescription>Etapas concluídas</CardDescription>
                    <CardTitle className="text-lg">
                    {concluidas.length} de {registradas.length}
                    </CardTitle>
                </CardHeader>
                </Card>
                <Card size="sm">
                <CardHeader>
                    <CardDescription>Situação</CardDescription>
                    <CardTitle className="text-base">{situacao}</CardTitle>
                </CardHeader>
                </Card>
            </section>

            <ol className="relative ml-3 space-y-6 border-l pl-6">
                {cadeia.etapas.map((etapa) => (
                <li key={etapa.id ?? "origem"} className="relative">
                    <span
                    className={`absolute -left-[31px] top-5 h-3 w-3 rounded-full ring-4 ring-background ${COR_PONTO[etapa.status]}`}
                    />
                    <CartaoEtapa
                    etapa={etapa}
                    historico={etapa.id ? historicos[etapa.id] : undefined}
                    onAlternarHistorico={alternarHistorico}
                    />
                </li>
                ))}

                {cadeia.etapas_pendentes.map((tipo) => (
                <li key={`pendente-${tipo}`} className="relative">
                    <span className="absolute -left-[31px] top-5 h-3 w-3 rounded-full bg-background ring-2 ring-gray-300" />
                    <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                    {ROTULO_TIPO[tipo]}: etapa ainda não registrada.
                    </div>
                </li>
                ))}
            </ol>
            </>
        )}
        </main>
    </RotaProtegida>
    );
}