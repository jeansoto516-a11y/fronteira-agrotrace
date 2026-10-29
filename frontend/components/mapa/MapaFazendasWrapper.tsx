"use client";

import dynamic from "next/dynamic";
import { Fazenda, Talhao } from "@/lib/api/types";

const MapaFazendas = dynamic(() => import("./MapaFazendas"), {
    ssr: false,
    loading: () => <p>Carregando mapa...</p>,
});

interface Props {
    fazendas: Fazenda[];
    talhoes: Talhao[];
}

export default function MapaFazendasWrapper({ fazendas, talhoes }: Props) {
    return <MapaFazendas fazendas={fazendas} talhoes={talhoes} />;
}