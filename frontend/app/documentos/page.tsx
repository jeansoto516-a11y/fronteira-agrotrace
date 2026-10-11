"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import RotaProtegida from "@/components/RotaProtegida";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listarFazendas } from "@/lib/api/fazendas";
import { listarTalhoes } from "@/lib/api/talhoes";
import {
  listarDocumentos,
  listarVencendo,
  enviarDocumento,
  enviarNovaVersao,
  baixarDocumento,
  excluirDocumento,
} from "@/lib/api/documentos";
import {
  Documento,
  EntidadeDocumento,
  SituacaoValidade,
  TipoDocumento,
} from "@/lib/api/types";

const NOMES_TIPO: Record<TipoDocumento, string> = {
  car: "CAR",
  licenca_ambiental: "Licença ambiental",
  laudo_tecnico: "Laudo técnico",
  outro: "Outro",
};

const TEXTO_SITUACAO: Record<SituacaoValidade, string> = {
  sem_validade: "Sem validade",
  valido: "Válido",
  a_vencer: "A vencer",
  vencido: "Vencido",
};

const COR_SITUACAO: Record<SituacaoValidade, string> = {
  sem_validade: "bg-gray-100 text-gray-700",
  valido: "bg-green-100 text-green-800",
  a_vencer: "bg-yellow-100 text-yellow-800",
  vencido: "bg-red-100 text-red-800",
};

function formatarData(data: string | null) {
  if (!data) return "-";
  return data.split("-").reverse().join("/");
}

function Situacao({ doc }: { doc: Documento }) {
  const s = doc.situacao_validade;
  const extra =
    doc.dias_para_vencer !== null && s === "a_vencer"
      ? ` (${doc.dias_para_vencer}d)`
      : "";
  return (
    <span className={`rounded px-2 py-1 text-xs ${COR_SITUACAO[s]}`}>
      {TEXTO_SITUACAO[s]}
      {extra}
    </span>
  );
}

export default function DocumentosPage() {
  const [entidadeTipo, setEntidadeTipo] = useState<EntidadeDocumento | "">("");
  const [opcoes, setOpcoes] = useState<{ id: string; nome: string }[]>([]);
  const [entidadeId, setEntidadeId] = useState("");
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [vencendo, setVencendo] = useState<Documento[]>([]);
  const [incluirHistorico, setIncluirHistorico] = useState(false);

  const [tipo, setTipo] = useState<TipoDocumento | "">("");
  const [dataValidade, setDataValidade] = useState("");
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [inputKey, setInputKey] = useState(0);
  const [enviando, setEnviando] = useState(false);

  const inputVersaoRef = useRef<HTMLInputElement>(null);
  const docVersaoRef = useRef<string | null>(null);

  async function carregarVencendo() {
    try {
      setVencendo(await listarVencendo(30));
    } catch {
      toast.error("Erro ao carregar documentos a vencer");
    }
  }

  async function carregarDocumentos() {
    if (!entidadeTipo || !entidadeId) return;
    try {
      setDocumentos(
        await listarDocumentos(entidadeTipo, entidadeId, incluirHistorico),
      );
    } catch {
      toast.error("Erro ao carregar documentos");
    }
  }

  async function recarregar() {
    await Promise.all([carregarDocumentos(), carregarVencendo()]);
  }

  useEffect(() => {
    carregarVencendo();
  }, []);

  useEffect(() => {
    setEntidadeId("");
    setDocumentos([]);
    setOpcoes([]);
    if (!entidadeTipo) return;
    async function carregarOpcoes() {
      try {
        if (entidadeTipo === "fazenda") {
          const dados = await listarFazendas();
          setOpcoes(dados.map((f) => ({ id: f.id, nome: f.nome })));
        } else {
          const dados = await listarTalhoes();
          setOpcoes(
            dados.map((t) => ({ id: t.id, nome: t.nome_identificador })),
          );
        }
      } catch {
        toast.error("Erro ao carregar opções");
      }
    }
    carregarOpcoes();
  }, [entidadeTipo]);

  useEffect(() => {
    carregarDocumentos();
  }, [entidadeTipo, entidadeId, incluirHistorico]);

  async function handleEnviar() {
    if (!entidadeTipo || !entidadeId) {
      toast.error("Selecione a fazenda/talhão");
      return;
    }
    if (!tipo || !arquivo) {
      toast.error("Selecione o tipo e o arquivo");
      return;
    }
    setEnviando(true);
    try {
      await enviarDocumento({
        tipo,
        entidadeTipo,
        entidadeId,
        dataValidade: dataValidade || undefined,
        arquivo,
      });
      toast.success("Documento enviado!");
      setArquivo(null);
      setDataValidade("");
      setInputKey((k) => k + 1);
      await recarregar();
    } catch {
        toast.error("Erro ao enviar (perfil admin, .pdf/.jpg/.png)");
    } finally {
        setEnviando(false);
    }
    }

    function pedirNovaVersao(doc: Documento) {
    docVersaoRef.current = doc.id;
    inputVersaoRef.current?.click();
    }

    async function handleNovaVersao(arq: File | undefined) {
    const docId = docVersaoRef.current;
    if (!arq || !docId) return;
    try {
        await enviarNovaVersao(docId, arq, dataValidade || undefined);
        toast.success("Nova versão enviada!");
        await recarregar();
    } catch {
        toast.error("Erro ao enviar nova versão");
    }
    }

    async function handleBaixar(doc: Documento) {
    try {
        await baixarDocumento(doc);
    } catch {
        toast.error("Erro ao baixar o arquivo");
    }
    }

    async function handleExcluir(doc: Documento) {
    if (!confirm(`Excluir ${doc.nome_arquivo_original} (v${doc.versao})?`)) {
        return;
    }
    try {
        await excluirDocumento(doc.id);
        toast.success("Documento excluído");
        await recarregar();
    } catch {
        toast.error("Erro ao excluir");
    }
    }

    return (
    <RotaProtegida>
        <main className="p-8 space-y-8">
        <h1 className="text-2xl font-bold">Gestão Documental</h1>

        <section>
            <h2 className="text-lg font-semibold mb-2">
            Vencidos ou a vencer em 30 dias ({vencendo.length})
            </h2>
            {vencendo.length === 0 ? (
            <p className="text-sm text-muted-foreground">
                Nenhum documento vencido ou a vencer.
            </p>
            ) : (
            <Table>
                <TableHeader>
                <TableRow>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Arquivo</TableHead>
                    <TableHead>Validade</TableHead>
                    <TableHead>Situação</TableHead>
                </TableRow>
                </TableHeader>
                <TableBody>
                {vencendo.map((d) => (
                    <TableRow key={d.id}>
                    <TableCell>{NOMES_TIPO[d.tipo]}</TableCell>
                    <TableCell>{d.nome_arquivo_original}</TableCell>
                    <TableCell>{formatarData(d.data_validade)}</TableCell>
                    <TableCell>
                        <Situacao doc={d} />
                    </TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
            )}
        </section>

        <section className="space-y-4 max-w-3xl">
            <h2 className="text-lg font-semibold">Documentos por entidade</h2>
            <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
                <Label>Vincular a</Label>
                <Select
                value={entidadeTipo}
                onValueChange={(v) => setEntidadeTipo(v as EntidadeDocumento)}
                >
                <SelectTrigger>
                    <SelectValue placeholder="Fazenda ou talhão" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="fazenda">Fazenda</SelectItem>
                    <SelectItem value="talhao">Talhão</SelectItem>
                </SelectContent>
                </Select>
            </div>
            <div className="space-y-2">
                <Label>Selecione</Label>
                <Select value={entidadeId} onValueChange={setEntidadeId}>
                <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                    {opcoes.map((o) => (
                    <SelectItem key={o.id} value={o.id}>
                        {o.nome}
                    </SelectItem>
                    ))}
                </SelectContent>
                </Select>
            </div>
            </div>

            {entidadeId && (
            <>
                <div className="grid grid-cols-3 gap-4 items-end">
                <div className="space-y-2">
                    <Label>Tipo</Label>
                    <Select
                    value={tipo}
                    onValueChange={(v) => setTipo(v as TipoDocumento)}
                    >
                    <SelectTrigger>
                        <SelectValue placeholder="Tipo" />
                    </SelectTrigger>
                    <SelectContent>
                        {Object.entries(NOMES_TIPO).map(([valor, nome]) => (
                        <SelectItem key={valor} value={valor}>
                            {nome}
                        </SelectItem>
                        ))}
                    </SelectContent>
                    </Select>
                </div>
                <div className="space-y-2">
                    <Label htmlFor="validade">Validade (opcional)</Label>
                    <Input
                    id="validade"
                    type="date"
                    value={dataValidade}
                    onChange={(e) => setDataValidade(e.target.value)}
                    />
                </div>
                    <div className="space-y-2">
                    <Label htmlFor="arquivo">Arquivo</Label>
                    <Input
                    key={inputKey}
                    id="arquivo"
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
                    />
                </div>
                </div>
                <Button onClick={handleEnviar} disabled={enviando}>
                {enviando ? "Enviando..." : "Enviar documento"}
                </Button>
                <p className="text-xs text-muted-foreground">
                Para nova versão, preencha a validade acima (se houver) e
                clique em &quot;Nova versão&quot; na linha do documento.
                </p>
            </>
            )}
        </section>

        {entidadeId && (
            <section>
            <label className="flex items-center gap-2 text-sm mb-2">
                <input
                type="checkbox"
                checked={incluirHistorico}
                onChange={(e) => setIncluirHistorico(e.target.checked)}
                />
                Mostrar histórico de versões
            </label>
            <Table>
                <TableHeader>
                <TableRow>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Arquivo</TableHead>
                    <TableHead>Versão</TableHead>
                    <TableHead>Validade</TableHead>
                    <TableHead>Situação</TableHead>
                    <TableHead>Ações</TableHead>
                </TableRow>
                </TableHeader>
                <TableBody>
                {documentos.map((d) => (
                    <TableRow key={d.id}>
                    <TableCell>{NOMES_TIPO[d.tipo]}</TableCell>
                    <TableCell>{d.nome_arquivo_original}</TableCell>
                    <TableCell>
                        v{d.versao}
                        {!d.vigente && " (antiga)"}
                    </TableCell>
                    <TableCell>{formatarData(d.data_validade)}</TableCell>
                    <TableCell>
                        <Situacao doc={d} />
                    </TableCell>
                    <TableCell className="space-x-1">
                        <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleBaixar(d)}
                        >
                        Baixar
                        </Button>
                        {d.vigente && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => pedirNovaVersao(d)}
                        >
                            Nova versão
                        </Button>
                        )}
                        <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleExcluir(d)}
                        >
                        Excluir
                        </Button>
                    </TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
            </section>
        )}

        <input
            ref={inputVersaoRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            className="hidden"
            onChange={(e) => {
            handleNovaVersao(e.target.files?.[0]);
            e.target.value = "";
            }}
        />
        </main>
    </RotaProtegida>
    );
}