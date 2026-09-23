"use client";

import { useEffect, useState } from "react";
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
import MapaSelecionarPontoWrapper from "@/components/mapa/MapaSelecionarPontoWrapper";
import { listarVinculos } from "@/lib/api/talhaoSafra";
import { listarColheitas, criarColheita } from "@/lib/api/colheitas";
import { TalhaoSafra, Colheita } from "@/lib/api/types";

export default function ColheitasPage() {
    const [vinculos, setVinculos] = useState<TalhaoSafra[]>([]);
    const [colheitas, setColheitas] = useState<Colheita[]>([]);
    const [vinculoSelecionado, setVinculoSelecionado] = useState("");
    const [carregando, setCarregando] = useState(true);
    const [salvando, setSalvando] = useState(false);

    const [dataColheita, setDataColheita] = useState("");
    const [quantidadeKg, setQuantidadeKg] = useState("");
    const [ponto, setPonto] = useState<[number, number] | null>(null);

    async function carregarVinculos() {
    try {
        const dados = await listarVinculos();
        setVinculos(dados);
    } catch {
        toast.error("Erro ao carregar vínculos talhão-safra");
    } finally {
        setCarregando(false);
    }
    }

    async function carregarColheitas(vinculoId: string) {
    try {
        const dados = await listarColheitas(vinculoId);
        setColheitas(dados);
    } catch {
        toast.error("Erro ao carregar colheitas");
    }
    }

    useEffect(() => {
    carregarVinculos();
    }, []);

    useEffect(() => {
    if (vinculoSelecionado) {
        carregarColheitas(vinculoSelecionado);
    } else {
        setColheitas([]);
    }
    }, [vinculoSelecionado]);

    function nomeDoVinculo(v: TalhaoSafra) {
    return `${v.talhao.nome_identificador} — ${v.safra.identificacao} (${v.cultura.nome})`;
    }

    async function handleSalvarColheita() {
    if (!vinculoSelecionado) {
        toast.error("Selecione o talhão/safra/cultura");
        return;
    }
    if (!ponto) {
        toast.error("Clique no mapa para marcar o ponto de coleta");
        return;
    }
    if (!dataColheita || !quantidadeKg) {
        toast.error("Preencha a data e a quantidade colhida");
        return;
    }

    setSalvando(true);
    try {
        await criarColheita({
        data_colheita: new Date(dataColheita).toISOString(),
        quantidade_kg: parseFloat(quantidadeKg),
        latitude: ponto[0],
        longitude: ponto[1],
        talhao_safra_id: vinculoSelecionado,
        });
        toast.success("Colheita registrada com sucesso!");
        setDataColheita("");
        setQuantidadeKg("");
        setPonto(null);
        carregarColheitas(vinculoSelecionado);
    } catch {
        toast.error("Erro ao registrar colheita. Verifique se a data não é futura.");
    } finally {
        setSalvando(false);
    }
    }

    return (
    <RotaProtegida>
        <main className="p-8 space-y-6">
        <h1 className="text-2xl font-bold">Registro de Colheita</h1>

        <div className="space-y-2 max-w-md">
            <Label>Talhão / Safra / Cultura</Label>
            <Select value={vinculoSelecionado} onValueChange={setVinculoSelecionado}>
            <SelectTrigger>
                <SelectValue placeholder="Selecione o vínculo" />
            </SelectTrigger>
            <SelectContent>
                {vinculos.map((v) => (
                <SelectItem key={v.id} value={v.id}>
                    {nomeDoVinculo(v)}
                </SelectItem>
                ))}
            </SelectContent>
            </Select>
        </div>

        {vinculoSelecionado && (
            <>
            <div>
                <Label className="mb-2 block">
                Clique no mapa para marcar o ponto exato da colheita
                </Label>
                <div className="border rounded-lg overflow-hidden">
                <MapaSelecionarPontoWrapper
                    pontoSelecionado={ponto}
                    onPontoSelecionado={(lat, lon) => setPonto([lat, lon])}
                />
                </div>
                {ponto && (
                <p className="text-sm text-muted-foreground mt-1">
                    Ponto selecionado: {ponto[0].toFixed(5)}, {ponto[1].toFixed(5)}
                </p>
                )}
            </div>

            <div className="flex gap-4 items-end max-w-2xl">
                <div className="space-y-2 flex-1">
                <Label htmlFor="dataColheita">Data/hora da colheita</Label>
                <Input
                    id="dataColheita"
                    type="datetime-local"
                    value={dataColheita}
                    onChange={(e) => setDataColheita(e.target.value)}
                />
                </div>
                <div className="space-y-2 flex-1">
                <Label htmlFor="quantidadeKg">Quantidade (kg)</Label>
                <Input
                    id="quantidadeKg"
                    type="number"
                    step="0.01"
                    value={quantidadeKg}
                    onChange={(e) => setQuantidadeKg(e.target.value)}
                />
                </div>
                <Button onClick={handleSalvarColheita} disabled={salvando}>
                {salvando ? "Salvando..." : "Registrar Colheita"}
                </Button>
            </div>

            <div>
                <h2 className="text-lg font-semibold mb-2">Colheitas registradas</h2>
                {carregando ? (
                <p>Carregando...</p>
                ) : (
                <Table>
                    <TableHeader>
                    <TableRow>
                        <TableHead>Data</TableHead>
                        <TableHead>Quantidade (kg)</TableHead>
                        <TableHead>Localização</TableHead>
                    </TableRow>
                    </TableHeader>
                    <TableBody>
                    {colheitas.map((colheita) => (
                        <TableRow key={colheita.id}>
                        <TableCell>{new Date(colheita.data_colheita).toLocaleString("pt-BR")}</TableCell>
                        <TableCell>{colheita.quantidade_kg}</TableCell>
                        <TableCell>
                            {colheita.latitude.toFixed(5)}, {colheita.longitude.toFixed(5)}
                        </TableCell>
                        </TableRow>
                    ))}
                    </TableBody>
                </Table>
                )}
            </div>
            </>
        )}
        </main>
    </RotaProtegida>
    );
}