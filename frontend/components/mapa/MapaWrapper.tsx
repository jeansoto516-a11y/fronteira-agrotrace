"use client";

import dynamic from "next/dynamic";

// ssr: false garante que o Leaflet só é carregado no navegador,
// nunca durante a renderização no servidor.
const MapaBase = dynamic(() => import("./MapaBase"), {
    ssr: false,
    loading: () => <p>Carregando mapa...</p>,
});

export default function MapaWrapper() {
    return <MapaBase />;
}