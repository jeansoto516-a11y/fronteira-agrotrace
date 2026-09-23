"use client";

import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface CapturaCliqueProps {
    onPontoSelecionado: (lat: number, lon: number) => void;
}

/**
 * Componente interno que escuta cliques no mapa e informa a
 * coordenada clicada para o componente pai.
 */
function CapturaClique({ onPontoSelecionado }: CapturaCliqueProps) {
    useMapEvents({
    click(evento) {
        onPontoSelecionado(evento.latlng.lat, evento.latlng.lng);
    },
    });
    return null;
}

interface MapaSelecionarPontoProps {
    centroInicial?: [number, number];
    pontoSelecionado: [number, number] | null;
    onPontoSelecionado: (lat: number, lon: number) => void;
}

export default function MapaSelecionarPonto({
    centroInicial = [-12.6819, -55.7967],
    pontoSelecionado,
    onPontoSelecionado,
}: MapaSelecionarPontoProps) {
    return (
    <MapContainer center={centroInicial} zoom={14} style={{ height: "400px", width: "100%" }}>
        <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <CapturaClique onPontoSelecionado={onPontoSelecionado} />
        {pontoSelecionado && <Marker position={pontoSelecionado} />}
    </MapContainer>
    );
}