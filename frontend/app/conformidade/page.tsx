"use client";

import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import RotaProtegida from "@/components/RotaProtegida";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    listarConformidade,
    obterResumoConformidade,
} from "@/lib/api/conformidade";
import {
    ConformidadeLote,
    ResumoConformidade,
    SeveridadeMotivo,
    StatusConformidade,
    TipoMotivoConformidade,
} from "@/lib/api/types";

const ROTULO_STATUS: Record<StatusConformidade, string> = {
    completo: "Completo",
    pendente: "Pendente",
    vencido: "Vencido",
};

const COR_STATUS: Record<StatusConformidade, string> = {
    completo: "bg-green-100 text-green-800",
    pendente: "bg-yellow-100 text-yellow-800",
    vencido: "bg-red-100 text-red-800",
};

const ROTULO_MOTIVO: Record<TipoMotivoConformidade, string> = {
    documento_ausente: "Documento ausente",
    documento_vencido: "Documento vencido",
    documento_a_vencer: "Documento a vencer",
    restricao_pendente_revisao: "Restrição aguardando revisão",
    restricao_confirmada: "Restrição confirmada",
};

const COR_SEVERIDADE: Record<SeveridadeMotivo, string> = {
    impeditivo: "bg-red-100 text-red-800",
    atencao: "bg-amber-100 text-amber-800",
};

const ROTULO_SEVERIDADE: Record<SeveridadeMotivo, string> = {
    impeditivo: "Impeditivo",
    atencao: "Atenção",
};

const ROTULO_ENTIDADE: Record<string, string> = {
    fazenda: "Fazenda",
    talhao: "Talhão",
};

const CLASSE_SELECT =
    "h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

function formatarData(data: string) {
    return data.split("-").reverse().join("/");
}

function formatarKg(n: number | null) {
    if (n === null || n === undefined) return "-";
    return `${n.toLocaleString("pt-BR", { maximumFractionDigits: 3 })} kg`;
}

function CartaoFiltro({
    rotulo,
    valor,
    ativo,
    destaque,
    onClick,
}: {
    rotulo: string;
    valor: number | undefined;
    ativo: boolean;
    destaque?: string;
    onClick: () => void;
}) {
    return (
    <button type="button" onClick={onClick} className="text-left">
        <Card size="sm" className={ativo ? "ring-2 ring-foreground/40" : ""}>
        <CardHeader>
            <CardDescription>{rotulo}</CardDescription>
            <CardTitle className={`text-2xl ${destaque ?? ""}`}>
            {valor ?? "-"}
            </CardTitle>
        </CardHeader>
        </Card>
    </button>
    );
}

export default function ConformidadePage() {
    const [lotes, setLotes] = useState<ConformidadeLote[]>([]);
    const [resumo, setResumo] = useState<ResumoConformidade | null>(null);
    const [carregando, setCarregando] = useState(false);

    const [filtroStatus, setFiltroStatus] = useState<
    StatusConformidade | "todos"
    >("todos");
    const [filtroMotivo, setFiltroMotivo] = useState<
    TipoMotivoConformidade | "todos"
    >("todos");
    const [busca, setBusca] = useState("");
    const [apenasComAvisos, setApenasComAvisos] = useState(false);
    const [expandidos, setExpandidos] = useState<Record<string, boolean>>({});

    const carregar = useCallback(async () => {
    setCarregando(true);
    try {
        const [lista, res] = await Promise.all([
        listarConformidade({ incluirMotivos: true }),
        obterResumoConformidade(),
        ]);
        setLotes(lista);
        setResumo(res);
    } catch {
        toast.error("Erro ao carregar a conformidade dos lotes");
    } finally {
        setCarregando(false);
    }
    }, []);

    useEffect(() => {
    carregar();
    }, [carregar]);

    const filtrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return lotes.filter((l) => {
        if (filtroStatus !== "todos" && l.status !== filtroStatus) return false;
        if (termo && !l.codigo_lote.toLowerCase().includes(termo)) return false;
        if (apenasComAvisos && l.total_avisos === 0) return false;
        if (
        filtroMotivo !== "todos" &&
        !l.motivos.some((m) => m.tipo === filtroMotivo)
        )
        return false;
        return true;
    });
    }, [lotes, filtroStatus, filtroMotivo, busca, apenasComAvisos]);

    const temFiltro =
    filtroStatus !== "todos" ||
    filtroMotivo !== "todos" ||
    busca.trim() !== "" ||
    apenasComAvisos;

    function limparFiltros() {
    setFiltroStatus("todos");
    setFiltroMotivo("todos");
    setBusca("");
    setApenasComAvisos(false);
    }

    function alternarExpandido(id: string) {
    setExpandidos((e) => ({ ...e, [id]: !e[id] }));
    }

    const avaliadoEm = lotes.length > 0 ? lotes[0].avaliado_em : null;

    return (
    <RotaProtegida>
        <main className="space-y-6 p-8">
        <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
            <h1 className="text-2xl font-bold">Painel de conformidade</h1>
            {avaliadoEm && (
                <p className="text-xs text-muted-foreground">
                Situação calculada em {formatarData(avaliadoEm)}
                </p>
            )}
            </div>
            <Button variant="outline" onClick={carregar} disabled={carregando}>
            {carregando ? "Atualizando..." : "Atualizar"}
            </Button>
        </div>

        <section className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <CartaoFiltro
            rotulo="Total de lotes"
            valor={resumo?.total_lotes}
            ativo={filtroStatus === "todos" && !apenasComAvisos}
            onClick={() => {
                setFiltroStatus("todos");
                setApenasComAvisos(false);
            }}
            />
            <CartaoFiltro
            rotulo="Completos"
            valor={resumo?.completos}
            ativo={filtroStatus === "completo"}
            destaque="text-green-700"
            onClick={() => setFiltroStatus("completo")}
            />
            <CartaoFiltro
            rotulo="Pendentes"
            valor={resumo?.pendentes}
            ativo={filtroStatus === "pendente"}
            destaque="text-yellow-700"
            onClick={() => setFiltroStatus("pendente")}
            />
            <CartaoFiltro
            rotulo="Vencidos"
            valor={resumo?.vencidos}
            ativo={filtroStatus === "vencido"}
            destaque="text-red-700"
            onClick={() => setFiltroStatus("vencido")}
            />
            <CartaoFiltro
            rotulo="Com avisos"
            valor={resumo?.com_avisos}
            ativo={apenasComAvisos}
            destaque="text-amber-700"
            onClick={() => setApenasComAvisos((a) => !a)}
            />
        </section>

        <section className="flex flex-wrap items-end gap-4">
            <div className="space-y-2">
            <Label htmlFor="busca">Buscar lote</Label>
            <Input
                id="busca"
                className="w-56"
                placeholder="Código do lote"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
            />
            </div>
            <div className="space-y-2">
            <Label htmlFor="filtro-status">Situação</Label>
            <select
                id="filtro-status"
                className={CLASSE_SELECT}
                value={filtroStatus}
                onChange={(e) =>
                setFiltroStatus(e.target.value as StatusConformidade | "todos")
                }
            >
                <option value="todos">Todas</option>
                <option value="vencido">Vencido</option>
                <option value="pendente">Pendente</option>
                <option value="completo">Completo</option>
            </select>
            </div>
            <div className="space-y-2">
            <Label htmlFor="filtro-motivo">Motivo</Label>
            <select
                id="filtro-motivo"
                className={CLASSE_SELECT}
                value={filtroMotivo}
                onChange={(e) =>
                setFiltroMotivo(
                    e.target.value as TipoMotivoConformidade | "todos",
                )
                }
            >
                <option value="todos">Todos</option>
                {(
                Object.entries(ROTULO_MOTIVO) as [
                    TipoMotivoConformidade,
                    string,
                ][]
                ).map(([valor, rotulo]) => (
                <option key={valor} value={valor}>
                    {rotulo}
                </option>
                ))}
            </select>
            </div>
            <label className="flex items-center gap-2 pb-2 text-sm">
            <input
                type="checkbox"
                checked={apenasComAvisos}
                onChange={(e) => setApenasComAvisos(e.target.checked)}
            />
            Somente com avisos
            </label>
            {temFiltro && (
            <Button variant="ghost" onClick={limparFiltros}>
                Limpar filtros
            </Button>
            )}
        </section>

        <p className="text-sm text-muted-foreground">
            Mostrando {filtrados.length} de {lotes.length} lote(s)
        </p>

        <section>
            <Table>
            <TableHeader>
                <TableRow>
                <TableHead>Lote</TableHead>
                <TableHead>Situação</TableHead>
                <TableHead>Peso</TableHead>
                <TableHead>Origem</TableHead>
                <TableHead>Impeditivos</TableHead>
                <TableHead>Avisos</TableHead>
                <TableHead>Detalhes</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {filtrados.length === 0 && (
                <TableRow>
                    <TableCell
                    colSpan={7}
                    className="text-sm text-muted-foreground"
                    >
                    {carregando
                        ? "Carregando..."
                        : lotes.length === 0
                        ? "Nenhum lote cadastrado ainda."
                        : "Nenhum lote para os filtros selecionados."}
                    </TableCell>
                </TableRow>
                )}
                {filtrados.map((l) => (
                <Fragment key={l.lote_id}>
                    <TableRow>
                    <TableCell className="font-medium">
                        {l.codigo_lote}
                    </TableCell>
                    <TableCell>
                        <span
                        className={`rounded px-2 py-1 text-xs ${COR_STATUS[l.status]}`}
                        >
                        {ROTULO_STATUS[l.status]}
                        </span>
                    </TableCell>
                    <TableCell>{formatarKg(l.peso_total_kg)}</TableCell>
                    <TableCell>
                        {l.total_fazendas} fazenda(s), {l.total_talhoes}{" "}
                        talhão(ões)
                    </TableCell>
                    <TableCell>{l.total_impeditivos}</TableCell>
                    <TableCell>{l.total_avisos}</TableCell>
                    <TableCell>
                        <Button
                        variant="outline"
                        size="sm"
                        onClick={() => alternarExpandido(l.lote_id)}
                        >
                        {expandidos[l.lote_id] ? "Ocultar" : "Ver motivos"}
                        </Button>
                    </TableCell>
                    </TableRow>

                    {expandidos[l.lote_id] && (
                    <TableRow>
                        <TableCell colSpan={7} className="bg-muted/30">
                        {l.motivos.length === 0 ? (
                            <p className="text-sm text-muted-foreground">
                            Nenhuma pendência: todos os documentos obrigatórios
                            estão vigentes e não há sinalização em aberto.
                            </p>
                        ) : (
                            <ul className="space-y-2 py-1">
                            {l.motivos.map((m, i) => (
                                <li
                                key={`${m.tipo}-${m.entidade_id}-${i}`}
                                className="flex flex-wrap items-start gap-2 text-sm"
                                >
                                <span
                                    className={`rounded px-2 py-0.5 text-xs ${COR_SEVERIDADE[m.severidade]}`}
                                >
                                    {ROTULO_SEVERIDADE[m.severidade]}
                                </span>
                                <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                                    {ROTULO_MOTIVO[m.tipo]}
                                </span>
                                <span>
                                    {m.detalhe}{" "}
                                    <span className="text-xs text-muted-foreground">
                                    (
                                    {ROTULO_ENTIDADE[m.entidade_tipo] ??
                                        m.entidade_tipo}
                                    )
                                    </span>
                                </span>
                                </li>
                            ))}
                            </ul>
                        )}
                        </TableCell>
                    </TableRow>
                    )}
                </Fragment>
                ))}
            </TableBody>
            </Table>
        </section>
        </main>
    </RotaProtegida>
    );
}