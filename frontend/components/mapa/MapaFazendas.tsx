"use client";

import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, Polygon, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Fazenda, Talhao } from "@/lib/api/types";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface MapaFazendasProps {
    fazendas: Fazenda[];
    talhoes: Talhao[];
}

// GeoJSON usa [longitude, latitude]; o Leaflet espera [latitude, longitude].
function coordenadasParaLeaflet(coordinates: number[][][]): [number, number][] {
    return coordinates[0].map(([lon, lat]) => [lat, lon]);
}

// Ajusta o zoom e o centro para enquadrar todos os pontos de uma vez.
function AjustarEnquadramento({ pontos }: { pontos: [number, number][] }) {
    const map = useMap();
    useEffect(() => {
        if (pontos.length === 0) return;
        map.fitBounds(L.latLngBounds(pontos), { padding: [40, 40], maxZoom: 14 });
    }, [map, pontos]);
    return null;
}

export default function MapaFazendas({ fazendas, talhoes }: MapaFazendasProps) {
    const fazendasComPonto = fazendas.filter(
        (f) => f.latitude !== null && f.longitude !== null,
    );

    const nomeDaFazenda = useMemo(() => {
        const nomes: Record<string, string> = {};
        fazendas.forEach((f) => {
            nomes[f.id] = f.nome;
        });
        return nomes;
    }, [fazendas]);

    const pontos = useMemo(() => {
        const lista: [number, number][] = [];
        fazendas.forEach((f) => {
            if (f.latitude !== null && f.longitude !== null) {
                lista.push([f.latitude, f.longitude]);
            }
        });
        talhoes.forEach((t) => {
            lista.push(...coordenadasParaLeaflet(t.poligono.coordinates));
        });
        return lista;
    }, [fazendas, talhoes]);

    return (
    <MapContainer center={[-12.6819, -55.7967]} zoom={5} style={{ height: "520px", width: "100%" }}>
        <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <AjustarEnquadramento pontos={pontos} />

        {talhoes.map((talhao) => (
        <Polygon
            key={talhao.id}
            positions={coordenadasParaLeaflet(talhao.poligono.coordinates)}
            pathOptions={{ color: "#16a34a", fillOpacity: 0.3 }}
        >
            <Popup>
            <strong>{talhao.nome_identificador}</strong>
            <br />
            Fazenda: {nomeDaFazenda[talhao.fazenda_id] ?? "-"}
            <br />
            {talhao.area_hectares ?? "-"} ha
            </Popup>
        </Polygon>
        ))}

        {fazendasComPonto.map((fazenda) => (
        <Marker key={fazenda.id} position={[fazenda.latitude as number, fazenda.longitude as number]}>
            <Popup>
            <strong>{fazenda.nome}</strong>
            <br />
            {fazenda.municipio}/{fazenda.estado}
            <br />
            {fazenda.area_total_hectares ?? "-"} ha
            </Popup>
        </Marker>
        ))}
    </MapContainer>
    );
}