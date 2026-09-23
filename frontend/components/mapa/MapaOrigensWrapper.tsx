"use client";

import dynamic from "next/dynamic";
import { ColheitaRastreada } from "@/lib/api/types";

const MapaOrigens = dynamic(() => import("./MapaOrigens"), { 
    ssr: false,
    loading: () => <p>Carregando mapa...</p>,
});

interface Props {
    origens: ColheitaRastreada[];
}

export default function MapaOrigensWrapper({ origens }: Props) {
    return <MapaOrigens origens={origens} />;
}