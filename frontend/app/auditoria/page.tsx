"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import { toast } from "sonner";
import RotaProtegida from "@/components/RotaProtegida";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  listarSinalizacoes,
  obterResumoSinalizacoes,
  revisarSinalizacao,
} from "@/lib/api/sinalizacoes";
import {
  ResumoSinalizacoes,
  Sinalizacao,
  StatusRevisao,
  TipoAreaRestrita,
} from "@/lib/api/types";

const TEXTO_STATUS: Record<StatusRevisao, string> = {
  pendente: "Pendente",
  confirmada: "Confirmada",
  descartada: "Descartada",
};

const COR_STATUS: Record<StatusRevisao, string> = {
  pendente: "bg-yellow-100 text-yellow-800",
  confirmada: "bg-red-100 text-red-800",
  descartada: "bg-gray-100 text-gray-700",
};

const TEXTO_TIPO: Record<TipoAreaRestrita, string> = {
  embargo: "Embargo",
  desmatamento: "Desmatamento",
};

const COR_TIPO: Record<TipoAreaRestrita, string> = {
  embargo: "bg-orange-100 text-orange-800",
  desmatamento: "bg-green-100 text-green-800",
};

const CLASSE_SELECT =
  "h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

function formatarData(data: string) {
  return data.split("-").reverse().join("/");
}

function formatarDataHora(iso: string | null) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function formatarNumero(n: number) {
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

function mensagemErro(e: unknown) {
  if (axios.isAxiosError(e)) {
    const detail = e.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  }
  return "Erro ao salvar a revisão";
}

export default function AuditoriaPage() {
  const { usuario } = useAuth();
  const podeVer =
    usuario?.perfil === "auditor_compliance" ||
    usuario?.perfil === "cooperativa_admin";
  const podeRevisar = usuario?.perfil === "auditor_compliance";

  const [resumo, setResumo] = useState<ResumoSinalizacoes | null>(null);
  const [sinalizacoes, setSinalizacoes] = useState<Sinalizacao[]>([]);
  const [carregando, setCarregando] = useState(false);

  const [filtroStatus, setFiltroStatus] = useState<StatusRevisao | "todos">(
    "pendente",
  );
  const [filtroTipo, setFiltroTipo] = useState<TipoAreaRestrita | "todos">(
    "todos",
  );
  const [incluirHistorico, setIncluirHistorico] = useState(false);

  const [selecionada, setSelecionada] = useState<Sinalizacao | null>(null);
  const [decisao, setDecisao] = useState<"confirmada" | "descartada" | "">("");
  const [parecer, setParecer] = useState("");
  const [enviando, setEnviando] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const [lista, res] = await Promise.all([
        listarSinalizacoes({
          apenasAtivas: !incluirHistorico,
          tipo: filtroTipo === "todos" ? undefined : filtroTipo,
          statusRevisao: filtroStatus === "todos" ? undefined : filtroStatus,
        }),
        obterResumoSinalizacoes(),
      ]);
      setSinalizacoes(lista);
      setResumo(res);
    } catch {
      toast.error("Erro ao carregar as sinalizações");
    } finally {
      setCarregando(false);
    }
  }, [incluirHistorico, filtroTipo, filtroStatus]);

  useEffect(() => {
    if (podeVer) carregar();
  }, [podeVer, carregar]);

  function abrirRevisao(s: Sinalizacao) {
    setSelecionada(s);
    setDecisao("");
    setParecer(s.parecer ?? "");
  }

  function fecharRevisao() {
    if (enviando) return;
    setSelecionada(null);
  }

  async function handleSalvarRevisao() {
    if (!selecionada) return;
    if (!decisao) {
      toast.error("Escolha entre confirmar ou descartar");
      return;
    }
    const texto = parecer.trim();
    if (decisao === "descartada" && texto.length < 10) {
      toast.error("Para descartar, escreva um parecer com pelo menos 10 caracteres");
      return;
    }
    setEnviando(true);
    try {
      await revisarSinalizacao(selecionada.id, {
        decisao,
        parecer: texto || undefined,
      });
      toast.success(
        decisao === "confirmada"
          ? "Sinalização confirmada"
          : "Sinalização descartada",
      );
      setSelecionada(null);
      await carregar();
    } catch (e) {
      toast.error(mensagemErro(e));
    } finally {
      setEnviando(false);
    }
  }

  const cartoes: { rotulo: string; valor: number | undefined }[] = [
    { rotulo: "Talhões sinalizados", valor: resumo?.talhoes_sinalizados },
    { rotulo: "Sinalizações ativas", valor: resumo?.sinalizacoes_ativas },
    { rotulo: "Embargos", valor: resumo?.embargos },
    { rotulo: "Desmatamentos", valor: resumo?.desmatamentos },
    { rotulo: "Pendentes de revisão", valor: resumo?.pendentes_revisao },
  ];

  return (
    <RotaProtegida>
      <main className="p-8 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Auditoria de Compliance</h1>
          <Link href="/dashboard" className="text-sm underline">
            Voltar ao dashboard
          </Link>
        </div>

        {!podeVer ? (
          <p className="text-sm text-muted-foreground">
            Acesso restrito aos perfis auditor de compliance e administrador da
            cooperativa.
          </p>
        ) : (
          <>
            <section className="grid grid-cols-2 gap-4 md:grid-cols-5">
              {cartoes.map((c) => (
                <Card key={c.rotulo} size="sm">
                  <CardHeader>
                    <CardDescription>{c.rotulo}</CardDescription>
                    <CardTitle className="text-2xl">
                      {c.valor ?? "-"}
                    </CardTitle>
                  </CardHeader>
                </Card>
              ))}
            </section>

            {!podeRevisar && (
              <p className="text-xs text-muted-foreground">
                Você pode consultar as sinalizações, mas apenas o auditor de
                compliance registra a revisão.
              </p>
            )}

            <section className="flex flex-wrap items-end gap-4">
              <div className="space-y-2">
                <Label htmlFor="filtro-status">Revisão</Label>
                <select
                  id="filtro-status"
                  className={CLASSE_SELECT}
                  value={filtroStatus}
                  onChange={(e) =>
                    setFiltroStatus(e.target.value as StatusRevisao | "todos")
                  }
                >
                  <option value="todos">Todas</option>
                  <option value="pendente">Pendentes</option>
                  <option value="confirmada">Confirmadas</option>
                  <option value="descartada">Descartadas</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="filtro-tipo">Tipo de área</Label>
                <select
                  id="filtro-tipo"
                  className={CLASSE_SELECT}
                  value={filtroTipo}
                  onChange={(e) =>
                    setFiltroTipo(e.target.value as TipoAreaRestrita | "todos")
                  }
                >
                  <option value="todos">Todos</option>
                  <option value="embargo">Embargo</option>
                  <option value="desmatamento">Desmatamento</option>
                </select>
              </div>
              <label className="flex items-center gap-2 pb-2 text-sm">
                <input
                  type="checkbox"
                  checked={incluirHistorico}
                  onChange={(e) => setIncluirHistorico(e.target.checked)}
                />
                Incluir histórico (sobreposições já resolvidas)
              </label>
            </section>

            <section>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Talhão</TableHead>
                    <TableHead>Área restrita</TableHead>
                    <TableHead>Sobreposição</TableHead>
                    <TableHead>Detectada em</TableHead>
                    <TableHead>Revisão</TableHead>
                    <TableHead>Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sinalizacoes.length === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        className="text-sm text-muted-foreground"
                      >
                        {carregando
                          ? "Carregando..."
                          : "Nenhuma sinalização para os filtros selecionados."}
                      </TableCell>
                    </TableRow>
                  )}
                  {sinalizacoes.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell>{s.talhao_nome}</TableCell>
                      <TableCell>
                        <div>{s.identificador}</div>
                        <span
                          className={`rounded px-2 py-0.5 text-xs ${COR_TIPO[s.tipo]}`}
                        >
                          {TEXTO_TIPO[s.tipo]}
                        </span>
                        {!s.ativa && (
                          <span className="ml-1 rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                            Resolvida
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {formatarNumero(s.area_sobreposta_hectares)} ha (
                        {formatarNumero(s.percentual_do_talhao)}%)
                      </TableCell>
                      <TableCell>{formatarDataHora(s.detectada_em)}</TableCell>
                      <TableCell>
                        <span
                          className={`rounded px-2 py-1 text-xs ${COR_STATUS[s.status_revisao]}`}
                        >
                          {TEXTO_STATUS[s.status_revisao]}
                        </span>
                        {s.status_revisao !== "pendente" && (
                          <div className="mt-1 max-w-xs text-xs text-muted-foreground">
                            {s.revisado_por_nome ?? "Revisor removido"} em{" "}
                            {formatarDataHora(s.revisado_em)}
                            {s.parecer && <p>{s.parecer}</p>}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {podeRevisar && s.ativa && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => abrirRevisao(s)}
                          >
                            {s.status_revisao === "pendente"
                              ? "Revisar"
                              : "Rever"}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </section>
          </>
        )}

        <Dialog
          open={selecionada !== null}
          onOpenChange={(aberto) => {
            if (!aberto) fecharRevisao();
          }}
        >
          <DialogContent className="sm:max-w-lg">
            {selecionada && (
              <>
                <DialogHeader>
                  <DialogTitle>Revisar sinalização</DialogTitle>
                  <DialogDescription>
                    {selecionada.talhao_nome} × {selecionada.identificador} (
                    {TEXTO_TIPO[selecionada.tipo]}, referência{" "}
                    {formatarData(selecionada.data_referencia)})
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                  <p className="text-sm">
                    Sobreposição de{" "}
                    <strong>
                      {formatarNumero(selecionada.area_sobreposta_hectares)} ha
                    </strong>{" "}
                    ({formatarNumero(selecionada.percentual_do_talhao)}% do
                    talhão). Fonte: {selecionada.fonte}.
                  </p>
                  {selecionada.descricao && (
                    <p className="text-sm text-muted-foreground">
                      {selecionada.descricao}
                    </p>
                  )}

                  <fieldset className="space-y-2">
                    <legend className="mb-1 text-sm font-medium">
                      Decisão
                    </legend>
                    <label className="flex items-start gap-2 text-sm">
                      <input
                        type="radio"
                        name="decisao"
                        checked={decisao === "confirmada"}
                        onChange={() => setDecisao("confirmada")}
                        className="mt-1"
                      />
                      <span>
                        <strong>Confirmar</strong>: a sobreposição é real e o
                        talhão permanece com restrição.
                      </span>
                    </label>
                    <label className="flex items-start gap-2 text-sm">
                      <input
                        type="radio"
                        name="decisao"
                        checked={decisao === "descartada"}
                        onChange={() => setDecisao("descartada")}
                        className="mt-1"
                      />
                      <span>
                        <strong>Descartar</strong>: falso positivo ou situação
                        regularizada (exige parecer).
                      </span>
                    </label>
                  </fieldset>

                  <div className="space-y-2">
                    <Label htmlFor="parecer">
                      Parecer{" "}
                      {decisao === "descartada"
                        ? "(obrigatório, mínimo 10 caracteres)"
                        : "(opcional)"}
                    </Label>
                    <Textarea
                      id="parecer"
                      rows={4}
                      maxLength={1000}
                      value={parecer}
                      onChange={(e) => setParecer(e.target.value)}
                      placeholder="Registre o motivo da decisão"
                    />
                    <p className="text-right text-xs text-muted-foreground">
                      {parecer.length}/1000
                    </p>
                  </div>
                </div>

                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={fecharRevisao}
                    disabled={enviando}
                  >
                    Cancelar
                    </Button>
                    <Button onClick={handleSalvarRevisao} disabled={enviando}>
                    {enviando ? "Salvando..." : "Salvar revisão"}
                    </Button>
                </DialogFooter>
                </>
            )}
            </DialogContent>
        </Dialog>
        </main>
    </RotaProtegida>
    );
}