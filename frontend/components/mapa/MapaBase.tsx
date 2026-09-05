"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Corrige um bug conhecido: os ícones padrão do Leaflet não carregam
// certo com bundlers modernos (Webpack/Turbopack). Apontamos manualmente
// para os ícones servidos via CDN.
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

export default function MapaBase() {
  // Coordenadas de exemplo: região produtora em Mato Grosso
    const posicaoInicial: [number, number] = [-12.6819, -55.7967];

    return (
    <MapContainer
        center={posicaoInicial}
        zoom={7}
        style={{ height: "500px", width: "100%" }}
    >
        <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={posicaoInicial}>
        <Popup>Fazenda de teste — MT</Popup>
        </Marker>
    </MapContainer>
    );
}