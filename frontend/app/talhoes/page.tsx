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
import MapaDesenhoWrapper from "@/components/mapa/MapaDesenhoWrapper";
import { listarFazendas } from "@/lib/api/fazendas";
import { listarTalhoes, criarTalhao } from "@/lib/api/talhoes";
import { Fazenda, Talhao, GeoJSONPolygonType } from "@/lib/api/types";

export default function TalhoesPage() {
    const [fazendas, setFazendas] = useState<Fazenda[]>([]);
    const [talhoes, setTalhoes] = useState<Talhao[]>([]);
    const [fazendaSelecionada, setFazendaSelecionada] = useState("");
    const [carregando, setCarregando] = useState(true);
    const [salvando, setSalvando] = useState(false);

    const [nomeIdentificador, setNomeIdentificador] = useState("");
    const [areaHectares, setAreaHectares] = useState("");
    const [poligono, setPoligono] = useState<GeoJSONPolygonType | null>(null);

    async function carregarFazendas() {
    try {
        const dados = await listarFazendas();
        setFazendas(dados);
    } catch {
        toast.error("Erro ao carregar fazendas");
    } finally {
        setCarregando(false);
    }
    }

    async function carregarTalhoes(fazendaId: string) {
    try {
        const dados = await listarTalhoes(fazendaId);
        setTalhoes(dados);
    } catch {
        toast.error("Erro ao carregar talhões");
    }
    }

    useEffect(() => {
    carregarFazendas();
    }, []);

    useEffect(() => {
    if (fazendaSelecionada) {
        carregarTalhoes(fazendaSelecionada);
    } else {
        setTalhoes([]);
    }
    }, [fazendaSelecionada]);

    async function handleSalvarTalhao() {
    if (!fazendaSelecionada) {
        toast.error("Selecione uma fazenda primeiro");
        return;
    }
    if (!poligono) {
        toast.error("Desenhe o polígono do talhão no mapa");
        return;
    }
    if (!nomeIdentificador) {
        toast.error("Informe o nome/identificador do talhão");
        return;
    }

    setSalvando(true);
    try {
        await criarTalhao({
        nome_identificador: nomeIdentificador,
        area_hectares: areaHectares ? parseFloat(areaHectares) : undefined,
        fazenda_id: fazendaSelecionada,
        poligono,
        });
        toast.success("Talhão cadastrado com sucesso!");
        setNomeIdentificador("");
        setAreaHectares("");
        setPoligono(null);
        carregarTalhoes(fazendaSelecionada);
    } catch {
        toast.error("Erro ao cadastrar talhão");
    } finally {
        setSalvando(false);
    }
    }

    return (
    <RotaProtegida>
        <main className="p-8 space-y-6">
        <h1 className="text-2xl font-bold">Talhões</h1>

        <div className="space-y-2 max-w-sm">
            <Label>Fazenda</Label>
            <Select value={fazendaSelecionada} onValueChange={setFazendaSelecionada}>
            <SelectTrigger>
                <SelectValue placeholder="Selecione a fazenda" />
            </SelectTrigger>
            <SelectContent>
                {fazendas.map((fazenda) => (
                <SelectItem key={fazenda.id} value={fazenda.id}>
                    {fazenda.nome}
                </SelectItem>
                ))}
            </SelectContent>
            </Select>
        </div>

        {fazendaSelecionada && (
            <>
            <div className="border rounded-lg overflow-hidden">
                <MapaDesenhoWrapper onPoligonoDesenhado={setPoligono} />
            </div>

            <div className="flex gap-4 items-end max-w-2xl">
                <div className="space-y-2 flex-1">
                <Label htmlFor="nomeIdentificador">Nome/Identificador</Label>
                <Input
                    id="nomeIdentificador"
                    placeholder="Ex: Talhão 01"
                    value={nomeIdentificador}
                    onChange={(e) => setNomeIdentificador(e.target.value)}
                />
                </div>
                <div className="space-y-2 flex-1">
                <Label htmlFor="areaHectares">Área (hectares)</Label>
                <Input
                    id="areaHectares"
                    type="number"
                    step="0.01"
                    value={areaHectares}
                    onChange={(e) => setAreaHectares(e.target.value)}
                />
                </div>
                <Button onClick={handleSalvarTalhao} disabled={salvando}>
                {salvando ? "Salvando..." : "Salvar Talhão"}
                </Button>
            </div>

            <div>
                <h2 className="text-lg font-semibold mb-2">Talhões desta fazenda</h2>
                {carregando ? (
                <p>Carregando...</p>
                ) : (
                <Table>
                    <TableHeader>
                    <TableRow>
                        <TableHead>Identificador</TableHead>
                        <TableHead>Área (ha)</TableHead>
                    </TableRow>
                    </TableHeader>
                    <TableBody>
                    {talhoes.map((talhao) => (
                        <TableRow key={talhao.id}>
                        <TableCell>{talhao.nome_identificador}</TableCell>
                        <TableCell>{talhao.area_hectares ?? "-"}</TableCell>
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