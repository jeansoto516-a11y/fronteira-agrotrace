import math
import os
import time
import urllib.request
from io import BytesIO

from PIL import Image

from app.core.config import settings

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

# Coloque False para desligar o mapa de fundo: o PDF usa só o desenho
# esquemático dos talhões (útil sem internet).
MAPA_ONLINE = True

# Servidor de tiles. Para volume alto de relatórios, troque por um
# provedor com chave de API ou próprio (a política do OpenStreetMap pede
# isso para uso intenso).
URL_TILE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

# A política do OpenStreetMap exige um User-Agent próprio e identificável.
# Se quiser, acrescente um e-mail de contato entre os parênteses.
USER_AGENT = (
    "FronteiraAgroTrace/1.0 (relatorio PDF; "
    "https://github.com/jeansoto516-a11y/fronteira-agrotrace)"
)

ATRIBUICAO = "© OpenStreetMap contributors"

TAMANHO_TILE = 256
ZOOM_MAXIMO = 16          # nunca baixa tiles mais detalhados que isso
ZOOM_MINIMO = 3
LARGURA_PX = 960          # tamanho da imagem final (proporção do quadro do PDF)
ALTURA_PX = 470
PREENCHIMENTO = 0.80      # a área dos talhões ocupa até 80% do quadro
VALIDADE_CACHE_S = 14 * 24 * 3600
TEMPO_LIMITE_TOTAL_S = 15
TEMPO_LIMITE_TILE_S = 5


# ---------------------------------------------------------------------------
# Projeção Web Mercator (a mesma dos tiles)
# ---------------------------------------------------------------------------

def _pixel_global(lon: float, lat: float, zoom: int) -> tuple[float, float]:
    """Coordenada em pixels no mapa-múndi inteiro, no zoom informado."""
    n = TAMANHO_TILE * (2 ** zoom)
    lat = max(min(lat, 85.05112878), -85.05112878)
    x = (lon + 180.0) / 360.0 * n
    rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(rad) + 1.0 / math.cos(rad)) / math.pi) / 2.0 * n
    return x, y


def _escolher_zoom(pontos: list) -> int:
    """Maior zoom em que todos os pontos cabem no quadro, com folga."""
    for zoom in range(ZOOM_MAXIMO, ZOOM_MINIMO - 1, -1):
        xs, ys = zip(*(_pixel_global(lon, lat, zoom) for lon, lat in pontos))
        if (
            max(xs) - min(xs) <= LARGURA_PX * PREENCHIMENTO
            and max(ys) - min(ys) <= ALTURA_PX * PREENCHIMENTO
        ):
            return zoom
    return ZOOM_MINIMO


# ---------------------------------------------------------------------------
# Tiles (com cache em disco)
# ---------------------------------------------------------------------------

def _caminho_cache(zoom: int, x: int, y: int) -> str:
    return os.path.join(
        settings.PASTA_UPLOADS, "cache_tiles", str(zoom), str(x), f"{y}.png"
    )


def _ler_do_disco(caminho: str) -> Image.Image:
    with Image.open(caminho) as imagem:
        return imagem.convert("RGB")


def _carregar_tile(zoom: int, x: int, y: int, prazo: float) -> Image.Image:
    caminho = _caminho_cache(zoom, x, y)
    existe = os.path.exists(caminho)

    if existe and time.time() - os.path.getmtime(caminho) < VALIDADE_CACHE_S:
        return _ler_do_disco(caminho)

    try:
        if time.monotonic() > prazo:
            raise TimeoutError("tempo total para baixar o mapa esgotado")
        # x, y e zoom são inteiros: a URL nunca recebe texto de usuário.
        requisicao = urllib.request.Request(
            URL_TILE.format(z=zoom, x=x, y=y),
            headers={"User-Agent": USER_AGENT, "Accept": "image/png"},
        )
        with urllib.request.urlopen(
            requisicao, timeout=TEMPO_LIMITE_TILE_S
        ) as resposta:
            dados = resposta.read()
        imagem = Image.open(BytesIO(dados))
        imagem.load()  # garante que o arquivo é uma imagem válida
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)
        return imagem.convert("RGB")
    except Exception:
        if existe:  # cache vencido é melhor que nenhum mapa
            return _ler_do_disco(caminho)
        raise


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def obter_mapa_base(pontos: list) -> dict | None:
    """
    Monta a imagem do mapa de fundo que cobre os pontos (lon, lat).
    Devolve None se não for possível (sem internet, provedor fora do ar,
    mapa desligado...): quem chama deve usar o desenho esquemático.
    """
    if not MAPA_ONLINE or not pontos:
        return None
    try:
        zoom = _escolher_zoom(pontos)
        xs, ys = zip(*(_pixel_global(lon, lat, zoom) for lon, lat in pontos))
        centro_x = (min(xs) + max(xs)) / 2
        centro_y = (min(ys) + max(ys)) / 2
        esquerda = centro_x - LARGURA_PX / 2
        topo = centro_y - ALTURA_PX / 2

        n_tiles = 2 ** zoom
        x_ini = math.floor(esquerda / TAMANHO_TILE)
        x_fim = math.floor((esquerda + LARGURA_PX - 1) / TAMANHO_TILE)
        y_ini = max(0, math.floor(topo / TAMANHO_TILE))
        y_fim = min(n_tiles - 1, math.floor((topo + ALTURA_PX - 1) / TAMANHO_TILE))

        quadro = Image.new("RGB", (LARGURA_PX, ALTURA_PX), (235, 235, 235))
        prazo = time.monotonic() + TEMPO_LIMITE_TOTAL_S
        for tx in range(x_ini, x_fim + 1):
            for ty in range(y_ini, y_fim + 1):
                tile = _carregar_tile(zoom, tx % n_tiles, ty, prazo)
                quadro.paste(
                    tile,
                    (round(tx * TAMANHO_TILE - esquerda),
                     round(ty * TAMANHO_TILE - topo)),
                )

        buffer = BytesIO()
        quadro.save(buffer, format="JPEG", quality=88)

        latitudes = [lat for _, lat in pontos]
        lat_media = (min(latitudes) + max(latitudes)) / 2
        metros_por_pixel = (
            156543.03392 * math.cos(math.radians(lat_media)) / (2 ** zoom)
        )

        def projetar(lon: float, lat: float) -> tuple[float, float]:
            """lon/lat → pixel dentro da imagem devolvida."""
            px, py = _pixel_global(lon, lat, zoom)
            return px - esquerda, py - topo

        return {
            "imagem": buffer.getvalue(),
            "projetar": projetar,
            "largura_px": LARGURA_PX,
            "altura_px": ALTURA_PX,
            "zoom": zoom,
            "metros_por_pixel": metros_por_pixel,
            "atribuicao": ATRIBUICAO,
        }
    except Exception as erro:
        print(
            f"[mapa] mapa de fundo indisponível ({erro}); "
            "usando o desenho esquemático"
        )
        return None