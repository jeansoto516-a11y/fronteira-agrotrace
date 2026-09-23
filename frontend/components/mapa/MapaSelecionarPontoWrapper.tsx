"use client";

import dynamic from "next/dynamic";

const MapaSelecionarPonto = dynamic(() => import("./MapaSelecionarPonto"), {
    ssr: false,
    loading: () => <p>Carregando mapa...</p>,
});

interface Props {
    pontoSelecionado: [number, number] | null;
    onPontoSelecionado: (lat: number, lon: number) => void;
}

export default function MapaSelecionarPontoWrapper(props: Props) {
    return <MapaSelecionarPonto {...props} />;
}