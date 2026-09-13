"use client";

import { useEffect, useState, FormEvent } from "react";
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
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { listarFazendas, criarFazenda } from "@/lib/api/fazendas";
import { listarProdutores } from "@/lib/api/produtores";
import { Fazenda, Produtor } from "@/lib/api/types";

export default function FazendasPage() {
    const [fazendas, setFazendas] = useState<Fazenda[]>([]);
    const [produtores, setProdutores] = useState<Produtor[]>([]);
    const [carregando, setCarregando] = useState(true);
    const [dialogAberto, setDialogAberto] = useState(false);
    const [salvando, setSalvando] = useState(false);

    const [nome, setNome] = useState("");
    const [municipio, setMunicipio] = useState("");
    const [estado, setEstado] = useState("");
    const [areaHectares, setAreaHectares] = useState("");
    const [latitude, setLatitude] = useState("");
    const [longitude, setLongitude] = useState("");
    const [produtorId, setProdutorId] = useState("");

    async function carregarDados() {
    setCarregando(true);
    try {
        const [dadosFazendas, dadosProdutores] = await Promise.all([
        listarFazendas(),
        listarProdutores(),
        ]);
        setFazendas(dadosFazendas);
        setProdutores(dadosProdutores);
    } catch {
        toast.error("Erro ao carregar dados");
    } finally {
        setCarregando(false);
    }
    }

    useEffect(() => {
    carregarDados();
    }, []);

    function nomeDoProdutor(produtorId: string) {
    return produtores.find((p) => p.id === produtorId)?.nome ?? "-";
    }

    function limparFormulario() {
    setNome("");
    setMunicipio("");
    setEstado("");
    setAreaHectares("");
    setLatitude("");
    setLongitude("");
    setProdutorId("");
    }

    async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!produtorId) {
        toast.error("Selecione o produtor dono da fazenda");
        return;
    }

    setSalvando(true);
    try {
        await criarFazenda({
        nome,
        municipio,
        estado,
        area_total_hectares: areaHectares ? parseFloat(areaHectares) : undefined,
        latitude: latitude ? parseFloat(latitude) : undefined,
        longitude: longitude ? parseFloat(longitude) : undefined,
        produtor_id: produtorId,
        });
        toast.success("Fazenda cadastrada com sucesso!");
        setDialogAberto(false);
        limparFormulario();
        carregarDados();
    } catch {
        toast.error("Erro ao cadastrar fazenda. Verifique os dados.");
    } finally {
        setSalvando(false);
    }
    }

    return (
    <RotaProtegida>
        <main className="p-8">
        <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold">Fazendas</h1>

            <Dialog open={dialogAberto} onOpenChange={setDialogAberto}>
            <DialogTrigger asChild>
                <Button>Nova Fazenda</Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                <DialogTitle>Cadastrar Fazenda</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                    <Label>Produtor</Label>
                    <Select value={produtorId} onValueChange={setProdutorId}>
                    <SelectTrigger>
                        <SelectValue placeholder="Selecione o produtor" />
                    </SelectTrigger>
                    <SelectContent>
                        {produtores.map((produtor) => (
                        <SelectItem key={produtor.id} value={produtor.id}>
                            {produtor.nome}
                        </SelectItem>
                        ))}
                    </SelectContent>
                    </Select>
                </div>
                <div className="space-y-2">
                    <Label htmlFor="nome">Nome da fazenda</Label>
                    <Input id="nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                    <Label htmlFor="municipio">Município</Label>
                    <Input id="municipio" value={municipio} onChange={(e) => setMunicipio(e.target.value)} required />
                    </div>
                    <div className="space-y-2">
                    <Label htmlFor="estado">Estado (UF)</Label>
                    <Input id="estado" maxLength={2} value={estado} onChange={(e) => setEstado(e.target.value)} required />
                    </div>
                </div>
                <div className="space-y-2">
                    <Label htmlFor="area">Área total (hectares)</Label>
                    <Input id="area" type="number" step="0.01" value={areaHectares} onChange={(e) => setAreaHectares(e.target.value)} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                    <Label htmlFor="latitude">Latitude</Label>
                    <Input id="latitude" type="number" step="any" value={latitude} onChange={(e) => setLatitude(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                    <Label htmlFor="longitude">Longitude</Label>
                    <Input id="longitude" type="number" step="any" value={longitude} onChange={(e) => setLongitude(e.target.value)} />
                    </div>
                </div>
                <Button type="submit" className="w-full" disabled={salvando}>
                    {salvando ? "Salvando..." : "Cadastrar"}
                </Button>
                </form>
            </DialogContent>
            </Dialog>
        </div>

        {carregando ? (
            <p>Carregando...</p>
        ) : (
            <Table>
            <TableHeader>
                <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Produtor</TableHead>
                <TableHead>Município/UF</TableHead>
                <TableHead>Área (ha)</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {fazendas.map((fazenda) => (
                <TableRow key={fazenda.id}>
                    <TableCell>{fazenda.nome}</TableCell>
                    <TableCell>{nomeDoProdutor(fazenda.produtor_id)}</TableCell>
                    <TableCell>{fazenda.municipio}/{fazenda.estado}</TableCell>
                    <TableCell>{fazenda.area_total_hectares ?? "-"}</TableCell>
                </TableRow>
                ))}
            </TableBody>
            </Table>
        )}
        </main>
    </RotaProtegida>
    );
}