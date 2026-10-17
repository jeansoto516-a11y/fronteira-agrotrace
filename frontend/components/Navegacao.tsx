"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { PerfilUsuario } from "@/lib/api/types";

interface ItemMenu {
    rotulo: string;
    href: string;
    perfis?: PerfilUsuario[];
}

const ITENS: ItemMenu[] = [
    { rotulo: "Dashboard", href: "/dashboard" },
    { rotulo: "Produtores", href: "/produtores" },
    { rotulo: "Fazendas", href: "/fazendas" },
    { rotulo: "Talhões", href: "/talhoes" },
    { rotulo: "Safras e culturas", href: "/safras" },
    { rotulo: "Colheitas", href: "/colheitas" },
    { rotulo: "Lotes", href: "/lotes" },
    { rotulo: "Documentos", href: "/documentos" },
    {
    rotulo: "Auditoria",
    href: "/auditoria",
    perfis: ["auditor_compliance", "cooperativa_admin"],
    },
];

const NOME_PERFIL: Record<PerfilUsuario, string> = {
    produtor: "Produtor",
    cooperativa_admin: "Administrador da cooperativa",
    auditor_compliance: "Auditor de compliance",
    exportador: "Exportador",
};

export default function Navegacao() {
    const { usuario, logout } = useAuth();
    const pathname = usePathname();

    const itens = ITENS.filter(
    (i) => !i.perfis || (usuario && i.perfis.includes(usuario.perfil)),
    );

    return (
    <aside className="sticky top-0 flex h-screen w-56 shrink-0 flex-col self-start border-r bg-muted/30">
        <div className="border-b px-4 py-4">
        <p className="text-sm font-semibold">Fronteira AgroTrace</p>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-2">
        {itens.map((item) => {
            const ativo =
            pathname === item.href || pathname.startsWith(item.href + "/");
            return (
            <Link
                key={item.href}
                href={item.href}
                className={`block rounded-md px-3 py-2 text-sm ${
                ativo
                    ? "bg-muted font-medium"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                }`}
            >
                {item.rotulo}
            </Link>
            );
        })}
        </nav>

        <div className="space-y-2 border-t p-3">
        <div>
            <p className="truncate text-sm font-medium">{usuario?.nome}</p>
            <p className="text-xs text-muted-foreground">
            {usuario ? NOME_PERFIL[usuario.perfil] : ""}
            </p>
        </div>
        <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={logout}
        >
            Sair
        </Button>
        </div>
    </aside>
    );
}