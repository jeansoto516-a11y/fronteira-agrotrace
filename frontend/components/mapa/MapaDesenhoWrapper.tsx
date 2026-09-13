"use client";

import dynamic from "next/dynamic";
import { GeoJSONPolygonType } from "@/lib/api/types";

const MapaDesenho = dynamic(() => import("./MapaDesenho"), {
    ssr: false,
    loading: () => <p>Carregando mapa...</p>,
});

interface Props {
    onPoligonoDesenhado: (poligono: GeoJSONPolygonType | null) => void;
}

export default function MapaDesenhoWrapper({ onPoligonoDesenhado }: Props) {
    return <MapaDesenho onPoligonoDesenhado={onPoligonoDesenhado} />;
}