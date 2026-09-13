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
import { listarProdutores, criarProdutor } from "@/lib/api/produtores";
import { Produtor } from "@/lib/api/types";

export default function ProdutoresPage() {
    const [produtores, setProdutores] = useState<Produtor[]>([]);
    const [carregando, setCarregando] = useState(true);
    const [dialogAberto, setDialogAberto] = useState(false);
    const [salvando, setSalvando] = useState(false);

    const [nome, setNome] = useState("");
    const [cpfCnpj, setCpfCnpj] = useState("");
    const [telefone, setTelefone] = useState("");
    const [email, setEmail] = useState("");

    async function carregarProdutores() {
    setCarregando(true);
    try {
        const dados = await listarProdutores();
        setProdutores(dados);
    } catch {
        toast.error("Erro ao carregar produtores");
    } finally {
        setCarregando(false);
    }
    }

    useEffect(() => {
    carregarProdutores();
    }, []);

    function limparFormulario() {
    setNome("");
    setCpfCnpj("");
    setTelefone("");
    setEmail("");
    }

    async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
        await criarProdutor({
        nome,
        cpf_cnpj: cpfCnpj,
        telefone: telefone || undefined,
        email: email || undefined,
        });
        toast.success("Produtor cadastrado com sucesso!");
        setDialogAberto(false);
        limparFormulario();
        carregarProdutores();
    } catch {
        toast.error("Erro ao cadastrar produtor. Verifique os dados.");
    } finally {
        setSalvando(false);
    }
    }

    return (
    <RotaProtegida>
        <main className="p-8">
        <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold">Produtores Rurais</h1>

            <Dialog open={dialogAberto} onOpenChange={setDialogAberto}>
            <DialogTrigger asChild>
                <Button>Novo Produtor</Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                <DialogTitle>Cadastrar Produtor</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="nome">Nome</Label>
                    <Input id="nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="cpfCnpj">CPF/CNPJ</Label>
                    <Input id="cpfCnpj" value={cpfCnpj} onChange={(e) => setCpfCnpj(e.target.value)} required />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="telefone">Telefone</Label>
                    <Input id="telefone" value={telefone} onChange={(e) => setTelefone(e.target.value)} />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
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
                <TableHead>CPF/CNPJ</TableHead>
                <TableHead>Telefone</TableHead>
                <TableHead>Email</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {produtores.map((produtor) => (
                <TableRow key={produtor.id}>
                    <TableCell>{produtor.nome}</TableCell>
                    <TableCell>{produtor.cpf_cnpj}</TableCell>
                    <TableCell>{produtor.telefone ?? "-"}</TableCell>
                    <TableCell>{produtor.email ?? "-"}</TableCell>
                </TableRow>
                ))}
            </TableBody>
            </Table>
        )}
        </main>
    </RotaProtegida>
    );
}