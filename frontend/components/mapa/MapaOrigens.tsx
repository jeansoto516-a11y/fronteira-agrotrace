"use client";

import { MapContainer, TileLayer, Polygon, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { ColheitaRastreada } from "@/lib/api/types";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface MapaOrigensProps {
    origens: ColheitaRastreada[];
}

export default function MapaOrigens({ origens }: MapaOrigensProps) {
  // GeoJSON usa [longitude, latitude]; o Leaflet espera [latitude, longitude].
  // Por isso invertemos cada par de coordenadas ao desenhar.
    function coordenadasParaLeaflet(coordinates: number[][][]): [number, number][] {
    return coordinates[0].map(([lon, lat]) => [lat, lon]);
    }

  // Centraliza o mapa no primeiro ponto do primeiro talhão disponível.
    const primeiroPonto = origens[0]?.talhao.poligono.coordinates[0]?.[0];
    const centro: [number, number] = primeiroPonto
    ? [primeiroPonto[1], primeiroPonto[0]]
    : [-12.6819, -55.7967];

    return (
    <MapContainer center={centro} zoom={12} style={{ height: "450px", width: "100%" }}>
        <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {origens.map((origem) => (
        <Polygon
            key={origem.talhao.talhao_id}
            positions={coordenadasParaLeaflet(origem.talhao.poligono.coordinates)}
            pathOptions={{ color: "#16a34a", fillOpacity: 0.3 }}
        >
            <Popup>
            <strong>{origem.talhao.nome_identificador}</strong>
            <br />
            Fazenda: {origem.fazenda.nome}
            <br />
            Produtor: {origem.produtor.nome}
            <br />
            {origem.talhao.area_hectares ?? "-"} ha
            </Popup>
        </Polygon>
        ))}
    </MapContainer>
    );
}