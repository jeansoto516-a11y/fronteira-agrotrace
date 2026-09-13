"use client";

import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw";
import { GeoJSONPolygonType } from "@/lib/api/types";

// Corrige o mesmo bug de ícones que já resolvemos no MapaBase.
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface FerramentasDesenhoProps {
    onPoligonoDesenhado: (poligono: GeoJSONPolygonType | null) => void;
}

/**
 * Componente interno que acessa a instância do mapa (via useMap) e
 * adiciona os controles de desenho do leaflet-draw. Permite desenhar
 * apenas 1 polígono por vez — desenhar um novo substitui o anterior.
 */
function FerramentasDesenho({ onPoligonoDesenhado }: FerramentasDesenhoProps) {
    const map = useMap();
    const camadaDesenhoRef = useRef<L.FeatureGroup | null>(null);

    useEffect(() => {
    const camadaDesenho = new L.FeatureGroup();
    map.addLayer(camadaDesenho);
    camadaDesenhoRef.current = camadaDesenho;

    const controleDesenho = new (L as any).Control.Draw({
        draw: {
        polygon: {
          allowIntersection: false, // não permite o polígono se auto-cruzar
            showArea: true,
          shapeOptions: { color: "#16a34a" }, // verde, combina com o tema agro
        },
        // Desabilita outras formas de desenho — só queremos polígono
        polyline: false,
        rectangle: false,
        circle: false,
        marker: false,
        circlemarker: false,
        },
        edit: {
        featureGroup: camadaDesenho,
        remove: true,
        },
    });
    map.addControl(controleDesenho);

    function converterParaGeoJSON(layer: L.Layer): GeoJSONPolygonType {
        const geojson = (layer as any).toGeoJSON();
        return geojson.geometry as GeoJSONPolygonType;
    }

    // Evento disparado ao terminar de desenhar um novo polígono
    map.on((L as any).Draw.Event.CREATED, (evento: any) => {
      camadaDesenho.clearLayers(); // só permite 1 polígono por vez
        camadaDesenho.addLayer(evento.layer);
        onPoligonoDesenhado(converterParaGeoJSON(evento.layer));
    });

    // Evento disparado ao editar um polígono existente
    map.on((L as any).Draw.Event.EDITED, (evento: any) => {
        evento.layers.eachLayer((layer: L.Layer) => {
        onPoligonoDesenhado(converterParaGeoJSON(layer));
        });
    });

    // Evento disparado ao apagar o polígono
    map.on((L as any).Draw.Event.DELETED, () => {
        onPoligonoDesenhado(null);
    });

    return () => {
        map.removeControl(controleDesenho);
        map.removeLayer(camadaDesenho);
    };
    }, [map, onPoligonoDesenhado]);

    return null;
}

interface MapaDesenhoProps {
    centroInicial?: [number, number];
    onPoligonoDesenhado: (poligono: GeoJSONPolygonType | null) => void;
}

export default function MapaDesenho({
  centroInicial = [-12.6819, -55.7967], // MT, mesma região usada no MapaBase
    onPoligonoDesenhado,
}: MapaDesenhoProps) {
    return (
    <MapContainer center={centroInicial} zoom={13} style={{ height: "500px", width: "100%" }}>
        <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FerramentasDesenho onPoligonoDesenhado={onPoligonoDesenhado} />
    </MapContainer>
    );
}