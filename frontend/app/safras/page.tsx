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
import { listarSafras, criarSafra } from "@/lib/api/safras";
import { listarCulturas, criarCultura } from "@/lib/api/culturas";
import { Safra, Cultura } from "@/lib/api/types";

export default function SafrasPage() {
    const [safras, setSafras] = useState<Safra[]>([]);
    const [culturas, setCulturas] = useState<Cultura[]>([]);
    const [carregando, setCarregando] = useState(true);

    const [dialogSafraAberto, setDialogSafraAberto] = useState(false);
    const [dialogCulturaAberto, setDialogCulturaAberto] = useState(false);
    const [salvando, setSalvando] = useState(false);

    const [identificacao, setIdentificacao] = useState("");
    const [anoInicio, setAnoInicio] = useState("");
    const [anoFim, setAnoFim] = useState("");
    const [nomeCultura, setNomeCultura] = useState("");

    async function carregarDados() {
    setCarregando(true);
    try {
        const [dadosSafras, dadosCulturas] = await Promise.all([
        listarSafras(),
        listarCulturas(),
        ]);
        setSafras(dadosSafras);
        setCulturas(dadosCulturas);
    } catch {
        toast.error("Erro ao carregar dados");
    } finally {
        setCarregando(false);
    }
    }

    useEffect(() => {
    carregarDados();
    }, []);

    async function handleSubmitSafra(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
        await criarSafra({
        identificacao,
        ano_inicio: parseInt(anoInicio, 10),
        ano_fim: parseInt(anoFim, 10),
        });
        toast.success("Safra cadastrada com sucesso!");
        setDialogSafraAberto(false);
        setIdentificacao("");
        setAnoInicio("");
        setAnoFim("");
        carregarDados();
    } catch {
        toast.error("Erro ao cadastrar safra. Verifique os dados.");
    } finally {
        setSalvando(false);
    }
    }

    async function handleSubmitCultura(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
        await criarCultura({ nome: nomeCultura });
        toast.success("Cultura cadastrada com sucesso!");
        setDialogCulturaAberto(false);
        setNomeCultura("");
        carregarDados();
    } catch {
        toast.error("Erro ao cadastrar cultura. Ela já pode existir.");
    } finally {
        setSalvando(false);
    }
    }

    return (
    <RotaProtegida>
        <main className="p-8 space-y-10">
        <div>
            <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold">Safras</h1>

            <Dialog open={dialogSafraAberto} onOpenChange={setDialogSafraAberto}>
                <DialogTrigger asChild>
                <Button>Nova Safra</Button>
                </DialogTrigger>
                <DialogContent>
                <DialogHeader>
                    <DialogTitle>Cadastrar Safra</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmitSafra} className="space-y-4">
                    <div className="space-y-2">
                    <Label htmlFor="identificacao">Identificação</Label>
                    <Input
                        id="identificacao"
                        placeholder="Ex: 2025/2026"
                        value={identificacao}
                        onChange={(e) => setIdentificacao(e.target.value)}
                        required
                    />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label htmlFor="anoInicio">Ano início</Label>
                        <Input
                        id="anoInicio"
                        type="number"
                        value={anoInicio}
                        onChange={(e) => setAnoInicio(e.target.value)}
                        required
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="anoFim">Ano fim</Label>
                        <Input
                        id="anoFim"
                        type="number"
                        value={anoFim}
                        onChange={(e) => setAnoFim(e.target.value)}
                        required
                        />
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
                    <TableHead>Identificação</TableHead>
                    <TableHead>Ano Início</TableHead>
                    <TableHead>Ano Fim</TableHead>
                </TableRow>
                </TableHeader>
                <TableBody>
                {safras.map((safra) => (
                    <TableRow key={safra.id}>
                    <TableCell>{safra.identificacao}</TableCell>
                    <TableCell>{safra.ano_inicio}</TableCell>
                    <TableCell>{safra.ano_fim}</TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
            )}
        </div>

        <div>
            <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">Culturas</h2>

            <Dialog open={dialogCulturaAberto} onOpenChange={setDialogCulturaAberto}>
                <DialogTrigger asChild>
                <Button variant="outline">Nova Cultura</Button>
                </DialogTrigger>
                <DialogContent>
                <DialogHeader>
                    <DialogTitle>Cadastrar Cultura</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmitCultura} className="space-y-4">
                    <div className="space-y-2">
                    <Label htmlFor="nomeCultura">Nome</Label>
                    <Input
                        id="nomeCultura"
                        placeholder="Ex: Soja, Café Arábica"
                        value={nomeCultura}
                        onChange={(e) => setNomeCultura(e.target.value)}
                        required
                    />
                    </div>
                    <Button type="submit" className="w-full" disabled={salvando}>
                    {salvando ? "Salvando..." : "Cadastrar"}
                    </Button>
                </form>
                </DialogContent>
            </Dialog>
            </div>

            {!carregando && (
            <Table>
                <TableHeader>
                <TableRow>
                    <TableHead>Nome</TableHead>
                </TableRow>
                </TableHeader>
                <TableBody>
                {culturas.map((cultura) => (
                    <TableRow key={cultura.id}>
                    <TableCell>{cultura.nome}</TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
            )}
        </div>
        </main>
    </RotaProtegida>
    );
}