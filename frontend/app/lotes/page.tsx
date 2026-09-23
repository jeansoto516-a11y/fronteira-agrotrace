"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import RotaProtegida from "@/components/RotaProtegida";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import MapaOrigensWrapper from "@/components/Mapa/MapaOrigensWrapper";
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
import { listarColheitas } from "@/lib/api/colheitas";
import { listarLotes, criarLote, consultarRastreabilidade } from "@/lib/api/lotes";
import { Colheita, Lote, RastreabilidadeLote } from "@/lib/api/types";

export default function LotesPage() {
    const [colheitas, setColheitas] = useState<Colheita[]>([]);
    const [lotes, setLotes] = useState<Lote[]>([]);
    const [carregando, setCarregando] = useState(true);
    const [salvando, setSalvando] = useState(false);

    const [codigoLote, setCodigoLote] = useState("");
    const [colheitaSelecionada, setColheitaSelecionada] = useState("");
    const [quantidadeKg, setQuantidadeKg] = useState("");
    const [itensLote, setItensLote] = useState<{ colheitaId: string; quantidade: number }[]>([]);

    const [loteConsultaId, setLoteConsultaId] = useState("");
    const [rastreabilidade, setRastreabilidade] = useState<RastreabilidadeLote | null>(null);
    const [consultando, setConsultando] = useState(false);

    async function carregarDados() {
    try {
        const [dadosColheitas, dadosLotes] = await Promise.all([
        listarColheitas(),
        listarLotes(),
        ]);
        setColheitas(dadosColheitas);
        setLotes(dadosLotes);
    } catch {
        toast.error("Erro ao carregar dados");
    } finally {
        setCarregando(false);
    }
    }

    useEffect(() => {
    carregarDados();
    }, []);

    function adicionarItem() {
    if (!colheitaSelecionada || !quantidadeKg) {
        toast.error("Selecione a colheita e informe a quantidade");
        return;
    }
    setItensLote([...itensLote, { colheitaId: colheitaSelecionada, quantidade: parseFloat(quantidadeKg) }]);
    setColheitaSelecionada("");
    setQuantidadeKg("");
    }

    function removerItem(index: number) {
    setItensLote(itensLote.filter((_, i) => i !== index));
    }

    async function handleFormarLote() {
    if (!codigoLote) {
        toast.error("Informe o código do lote");
        return;
    }
    if (itensLote.length === 0) {
        toast.error("Adicione pelo menos uma colheita ao lote");
        return;
    }

    setSalvando(true);
    try {
        await criarLote({
        codigo_lote: codigoLote,
        colheitas: itensLote.map((item) => ({
            colheita_id: item.colheitaId,
            quantidade_kg: item.quantidade,
        })),
        });
        toast.success("Lote formado com sucesso!");
        setCodigoLote("");
        setItensLote([]);
        carregarDados();
    } catch {
        toast.error("Erro ao formar lote. Verifique se o código já existe.");
    } finally {
        setSalvando(false);
    }
    }

    async function handleConsultarRastreabilidade() {
    if (!loteConsultaId) {
        toast.error("Selecione um lote para consultar");
        return;
    }
    setConsultando(true);
    try {
        const dados = await consultarRastreabilidade(loteConsultaId);
        setRastreabilidade(dados);
    } catch {
        toast.error("Erro ao consultar rastreabilidade");
    } finally {
        setConsultando(false);
    }
    }

    return (
    <RotaProtegida>
        <main className="p-8 space-y-10">
        {/* Seção 1: Formar um novo lote */}
        <div>
            <h1 className="text-2xl font-bold mb-6">Formar Lote</h1>

            <div className="space-y-4 max-w-2xl">
            <div className="space-y-2">
                <Label htmlFor="codigoLote">Código do lote</Label>
                <Input
                id="codigoLote"
                placeholder="Ex: LOTE-2026-002"
                value={codigoLote}
                onChange={(e) => setCodigoLote(e.target.value)}
                />
            </div>

            <div className="flex gap-4 items-end">
                <div className="space-y-2 flex-1">
                <Label>Colheita</Label>
                <Select value={colheitaSelecionada} onValueChange={setColheitaSelecionada}>
                    <SelectTrigger>
                    <SelectValue placeholder="Selecione a colheita" />
                    </SelectTrigger>
                    <SelectContent>
                    {colheitas.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                        {new Date(c.data_colheita).toLocaleDateString("pt-BR")} — {c.quantidade_kg}kg
                        </SelectItem>
                    ))}
                    </SelectContent>
                </Select>
                </div>
                <div className="space-y-2 w-40">
                <Label htmlFor="quantidadeKg">Quantidade (kg)</Label>
                <Input
                    id="quantidadeKg"
                    type="number"
                    step="0.01"
                    value={quantidadeKg}
                    onChange={(e) => setQuantidadeKg(e.target.value)}
                />
                </div>
                <Button variant="outline" onClick={adicionarItem}>
                Adicionar
                </Button>
            </div>

            {itensLote.length > 0 && (
                <Table>
                <TableHeader>
                    <TableRow>
                    <TableHead>Colheita</TableHead>
                    <TableHead>Quantidade (kg)</TableHead>
                    <TableHead></TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {itensLote.map((item, index) => (
                    <TableRow key={index}>
                        <TableCell>{item.colheitaId.slice(0, 8)}...</TableCell>
                        <TableCell>{item.quantidade}</TableCell>
                        <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => removerItem(index)}>
                            Remover
                        </Button>
                        </TableCell>
                    </TableRow>
                    ))}
                </TableBody>
                </Table>
            )}

            <Button onClick={handleFormarLote} disabled={salvando}>
                {salvando ? "Formando lote..." : "Formar Lote"}
            </Button>
            </div>
        </div>

        {/* Seção 2: Lotes existentes */}
        <div>
            <h2 className="text-xl font-bold mb-4">Lotes formados</h2>
            {carregando ? (
            <p>Carregando...</p>
            ) : (
            <Table>
                <TableHeader>
                <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Peso total (kg)</TableHead>
                    <TableHead>Criado em</TableHead>
                </TableRow>
                </TableHeader>
                <TableBody>
                {lotes.map((lote) => (
                    <TableRow key={lote.id}>
                    <TableCell>{lote.codigo_lote}</TableCell>
                    <TableCell>{lote.peso_total_kg ?? "-"}</TableCell>
                    <TableCell>{new Date(lote.criado_em).toLocaleDateString("pt-BR")}</TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
            )}
        </div>

        {/* Seção 3: Consultar rastreabilidade */}
        <div>
            <h2 className="text-xl font-bold mb-4">Consultar Rastreabilidade</h2>

            <div className="flex gap-4 items-end max-w-xl mb-6">
            <div className="space-y-2 flex-1">
                <Label>Lote</Label>
                <Select value={loteConsultaId} onValueChange={setLoteConsultaId}>
                <SelectTrigger>
                    <SelectValue placeholder="Selecione o lote" />
                </SelectTrigger>
                <SelectContent>
                    {lotes.map((lote) => (
                    <SelectItem key={lote.id} value={lote.id}>
                        {lote.codigo_lote}
                    </SelectItem>
                    ))}
                </SelectContent>
                </Select>
            </div>
            <Button onClick={handleConsultarRastreabilidade} disabled={consultando}>
                {consultando ? "Consultando..." : "Consultar Origem"}
            </Button>
            </div>

            {rastreabilidade && (
            <div className="space-y-4">
                <p className="font-medium">
                Lote {rastreabilidade.codigo_lote} — {rastreabilidade.peso_total_kg}kg total
                </p>
            <div className="border rounded-lg overflow-hidden">
                <MapaOrigensWrapper origens={rastreabilidade.origens} />
            </div>
                {rastreabilidade.origens.map((origem, index) => (
                <div key={index} className="border rounded-lg p-4 space-y-1">
                    <p><strong>Produtor:</strong> {origem.produtor.nome} (CPF/CNPJ: {origem.produtor.cpf_cnpj})</p>
                    <p><strong>Fazenda:</strong> {origem.fazenda.nome} — {origem.fazenda.municipio}/{origem.fazenda.estado}</p>
                    <p><strong>Talhão:</strong> {origem.talhao.nome_identificador} ({origem.talhao.area_hectares ?? "-"} ha)</p>
                    <p><strong>Safra/Cultura:</strong> {origem.safra} — {origem.cultura}</p>
                    <p><strong>Colheita:</strong> {new Date(origem.data_colheita).toLocaleDateString("pt-BR")} — {origem.quantidade_kg_no_lote}kg neste lote</p>
                </div>
                ))}
            </div>
            )}
        </div>
        </main>
    </RotaProtegida>
    );
}