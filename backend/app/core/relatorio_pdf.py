import math
from datetime import datetime
from enum import Enum
from io import BytesIO
from zoneinfo import ZoneInfo

from fpdf import FPDF
from fpdf.fonts import FontFace

from app.core.mapa_estatico import obter_mapa_base

FUSO = ZoneInfo("America/Sao_Paulo")

COR_TITULO = (22, 83, 52)
COR_CABECALHO_TABELA = (232, 240, 235)
ESTILO_CABECALHO = FontFace(emphasis="BOLD", fill_color=COR_CABECALHO_TABELA)

# (fundo, texto) de cada situação de conformidade
COR_STATUS = {
    "completo": ((220, 252, 231), (22, 101, 52)),
    "pendente": ((254, 249, 195), (133, 77, 14)),
    "vencido": ((254, 226, 226), (153, 27, 27)),
}

ROTULO_STATUS = {
    "completo": "Completo",
    "pendente": "Pendente",
    "vencido": "Vencido",
}
ROTULO_SEVERIDADE = {"impeditivo": "Impeditivo", "atencao": "Atenção"}
ROTULO_MOTIVO = {
    "documento_ausente": "Documento ausente",
    "documento_vencido": "Documento vencido",
    "documento_a_vencer": "Documento a vencer",
    "restricao_pendente_revisao": "Restrição aguardando revisão",
    "restricao_confirmada": "Restrição confirmada",
}
ROTULO_TIPO_DOC = {
    "car": "CAR",
    "licenca_ambiental": "Licença ambiental",
    "laudo_tecnico": "Laudo técnico",
    "outro": "Outro",
}
ROTULO_ENTIDADE = {"fazenda": "Fazenda", "talhao": "Talhão"}
ROTULO_SITUACAO_DOC = {
    "valido": "Válido",
    "a_vencer": "A vencer",
    "vencido": "Vencido",
    "sem_validade": "Sem validade",
}
ROTULO_AREA = {"embargo": "Embargo", "desmatamento": "Desmatamento"}
ROTULO_REVISAO = {
    "pendente": "Pendente de revisão",
    "confirmada": "Confirmada",
    "descartada": "Descartada",
}
ROTULO_ETAPA = {
    "fazenda": "Origem (fazenda)",
    "armazem": "Armazém",
    "transporte": "Transporte",
    "porto": "Porto",
    "exportacao": "Exportação",
}
ROTULO_STATUS_ETAPA = {
    "planejada": "Planejada",
    "em_andamento": "Em andamento",
    "concluida": "Concluída",
}
ROTULO_MODAL = {
    "rodoviario": "Rodoviário",
    "ferroviario": "Ferroviário",
    "hidroviario": "Hidroviário",
}
ROTULO_MOV = {
    "entrada": "Entrada",
    "saida": "Saída",
    "transferencia_responsavel": "Transferência de responsável",
    "ocorrencia": "Ocorrência",
}
ROTULO_PERFIL = {
    "produtor": "Produtor",
    "cooperativa_admin": "Administrador da cooperativa",
    "auditor_compliance": "Auditor de compliance",
    "exportador": "Exportador",
}

# As fontes padrão do PDF só aceitam Latin-1 (cobre todo o português).
# Pontuação "bonita" e emojis precisam ser trocados.
SUBSTITUICOES = {
    "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "-",
    "\u2192": "->", "\u00a0": " ",
}


def t(texto) -> str:
    """Deixa qualquer texto seguro para as fontes padrão do PDF."""
    texto = "" if texto is None else str(texto)
    for original, troca in SUBSTITUICOES.items():
        texto = texto.replace(original, troca)
    return texto.encode("latin-1", "replace").decode("latin-1")


def val(x):
    """Valor de um Enum (ou o próprio valor, se não for Enum)."""
    return x.value if isinstance(x, Enum) else x


def fmt_num(n, casas: int = 2) -> str:
    if n is None:
        return "-"
    s = f"{n:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_kg(n) -> str:
    return "-" if n is None else f"{fmt_num(n, 2)} kg"


def _para_fuso(v):
    if isinstance(v, datetime) and v.tzinfo is not None:
        return v.astimezone(FUSO)
    return v


def fmt_data(v) -> str:
    if v is None:
        return "-"
    return _para_fuso(v).strftime("%d/%m/%Y")


def fmt_datahora(v) -> str:
    if v is None:
        return "-"
    v = _para_fuso(v)
    if isinstance(v, datetime):
        return v.strftime("%d/%m/%Y %H:%M")
    return v.strftime("%d/%m/%Y")


class RelatorioPDF(FPDF):
    def __init__(self, codigo_lote: str):
        super().__init__(format="A4")
        self.codigo_lote = codigo_lote

    def footer(self):
        self.set_y(-13)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_y(-11)
        self.set_font("Helvetica", size=7.5)
        self.set_text_color(110, 110, 110)
        esquerda = t(
            "Fronteira AgroTrace | Relatório de rastreabilidade | "
            f"Lote {self.codigo_lote}"
        )
        self.cell(self.epw * 0.75, 5, esquerda)
        self.cell(0, 5, f"Página {self.page_no()} de {{nb}}", align="R")


# ---------------------------------------------------------------------------
# Blocos reutilizáveis
# ---------------------------------------------------------------------------

def _secao(pdf: FPDF, titulo: str, altura_minima: float = 35) -> None:
    if pdf.get_y() + altura_minima > pdf.page_break_trigger:
        pdf.add_page()
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COR_TITULO)
    pdf.cell(0, 7, t(titulo), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*COR_TITULO)
    pdf.set_line_width(0.4)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.set_line_width(0.2)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2.5)


def _subtitulo(pdf: FPDF, texto: str) -> None:
    if pdf.get_y() + 25 > pdf.page_break_trigger:
        pdf.add_page()
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 6, t(texto), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)


def _texto(pdf: FPDF, texto: str, tamanho: float = 9, cor=(0, 0, 0)) -> None:
    pdf.set_font("Helvetica", size=tamanho)
    pdf.set_text_color(*cor)
    pdf.multi_cell(0, 4.8, t(texto), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)


def _tabela(
    pdf: FPDF,
    cabecalho: list,
    linhas: list,
    larguras: tuple,
    alinhar=None,
    estilos: list | None = None,
    vazio: str = "Nenhum registro.",
) -> None:
    """Tabela com cabeçalho repetido a cada página e quebra de linha."""
    if not linhas:
        _texto(pdf, vazio, 9, (100, 100, 100))
        pdf.ln(2)
        return
    if pdf.get_y() + 25 > pdf.page_break_trigger:
        pdf.add_page()
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    with pdf.table(
        col_widths=larguras,
        headings_style=ESTILO_CABECALHO,
        line_height=4.6,
        text_align=alinhar or "LEFT",
    ) as tabela:
        linha_cab = tabela.row()
        for titulo in cabecalho:
            linha_cab.cell(t(titulo))
        for i, linha in enumerate(linhas):
            estilo = estilos[i] if estilos else None
            nova = tabela.row()
            for valor in linha:
                nova.cell(t(valor), style=estilo)
    pdf.set_x(pdf.l_margin)
    pdf.ln(3)


# ---------------------------------------------------------------------------
# Seções do relatório
# ---------------------------------------------------------------------------

def _cabecalho(pdf: FPDF, d: dict) -> None:
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*COR_TITULO)
    pdf.cell(0, 10, t("Relatório de rastreabilidade"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(
        0, 6,
        t("Fronteira AgroTrace | Rastreabilidade de commodities agrícolas"),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    lote = d["lote"]
    perfil = ROTULO_PERFIL.get(d["gerado_por"]["perfil"], d["gerado_por"]["perfil"])
    pares = [
        ("Lote", lote["codigo"]),
        ("Peso total", fmt_kg(lote["peso_total_kg"])),
        ("Lote formado em", fmt_data(lote["criado_em"])),
        ("Relatório gerado em", fmt_datahora(d["gerado_em"])),
        ("Gerado por", f"{d['gerado_por']['nome']} ({perfil})"),
    ]
    y = pdf.get_y()
    pdf.set_fill_color(240, 244, 241)
    pdf.rect(pdf.l_margin, y, pdf.epw, 31, style="F")
    pdf.set_y(y + 2)
    for rotulo, valor in pares:
        pdf.set_x(pdf.l_margin + 3)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(42, 5.4, t(rotulo))
        pdf.set_font("Helvetica", size=9.5)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5.4, t(valor), new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(y + 33)


def _secao_conformidade(pdf: FPDF, d: dict) -> None:
    _secao(pdf, "1. Situação de conformidade")
    c = d["conformidade"]
    status = val(c["status"])
    fundo, cor = COR_STATUS[status]

    pdf.set_fill_color(*fundo)
    pdf.set_text_color(*cor)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(42, 9, t(ROTULO_STATUS[status].upper()), fill=True, align="C", new_x="RIGHT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(
        0, 9,
        t(
            f"   {c['total_impeditivos']} impeditivo(s) | "
            f"{c['total_avisos']} aviso(s) | avaliado em {fmt_data(c['avaliado_em'])}"
        ),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(2)

    if not c["motivos"]:
        _texto(
            pdf,
            "Nenhuma pendência: todos os documentos obrigatórios estão vigentes "
            "e não há sinalização de área restrita em aberto.",
        )
        return

    linhas, estilos = [], []
    for m in c["motivos"]:
        severidade = val(m["severidade"])
        linhas.append([
            ROTULO_SEVERIDADE.get(severidade, severidade),
            ROTULO_MOTIVO.get(val(m["tipo"]), val(m["tipo"])),
            m["detalhe"],
        ])
        estilos.append(
            FontFace(fill_color=(254, 226, 226))
            if severidade == "impeditivo"
            else FontFace(fill_color=(254, 243, 199))
        )
    _tabela(pdf, ["Gravidade", "Motivo", "Detalhe"], linhas, (14, 24, 62), estilos=estilos)


def _secao_origem(pdf: FPDF, d: dict) -> None:
    _secao(pdf, "2. Origem do lote")

    _subtitulo(pdf, "Fazendas e produtores")
    _tabela(
        pdf,
        ["Fazenda", "Município/UF", "Produtor", "CPF/CNPJ", "Quantidade"],
        [
            [
                f["nome"], f"{f['municipio']}/{f['estado']}", f["produtor_nome"],
                f["produtor_documento"], fmt_kg(f["quantidade_kg"]),
            ]
            for f in d["fazendas"]
        ],
        (20, 17, 24, 17, 14),
        alinhar=("LEFT", "LEFT", "LEFT", "LEFT", "RIGHT"),
    )

    _subtitulo(pdf, "Colheitas que compõem o lote")
    total = sum(o["quantidade_kg"] for o in d["origens"])
    linhas = [
        [
            fmt_data(o["data_colheita"]), f"{o['safra']} / {o['cultura']}",
            o["talhao_nome"], f"{o['fazenda_nome']} ({o['estado']})",
            fmt_kg(o["quantidade_kg"]),
        ]
        for o in d["origens"]
    ]
    estilos = [None] * len(linhas)
    if linhas:
        linhas.append(["", "", "", "Total", fmt_kg(total)])
        estilos.append(FontFace(emphasis="BOLD", fill_color=COR_CABECALHO_TABELA))
    _tabela(
        pdf,
        ["Colheita", "Safra / cultura", "Talhão", "Fazenda", "Quantidade"],
        linhas,
        (13, 25, 20, 26, 16),
        alinhar=("LEFT", "LEFT", "LEFT", "LEFT", "RIGHT"),
        estilos=estilos,
    )

    _subtitulo(pdf, "Talhões de origem")
    _tabela(
        pdf,
        ["Talhão", "Fazenda", "Área", "Centro (lat, lon)", "No lote"],
        [
            [
                x["nome"], x["fazenda_nome"], f"{fmt_num(x['area_ha'], 2)} ha",
                f"{x['latitude']:.5f}, {x['longitude']:.5f}",
                fmt_kg(x["quantidade_kg"]),
            ]
            for x in d["talhoes"]
        ],
        (18, 24, 14, 24, 16),
        alinhar=("LEFT", "LEFT", "RIGHT", "LEFT", "RIGHT"),
    )


def _pontos_do_anel(proj, anel) -> list:
    pts = [proj(lon, lat) for lon, lat in anel]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return pts


def _rotulo_no_mapa(pdf: FPDF, nome: str, px: float, py: float) -> None:
    """Nome do talhão sobre um fundo branco translúcido, legível no mapa."""
    pdf.set_font("Helvetica", "B", 7)
    texto = t(nome)
    largura = pdf.get_string_width(texto) + 2
    with pdf.local_context(fill_opacity=0.75):
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(px - largura / 2, py - 3.1, largura, 4, style="F")
    pdf.set_text_color(*COR_TITULO)
    pdf.text(px - pdf.get_string_width(texto) / 2, py, texto)


def _secao_mapa(pdf: FPDF, d: dict) -> None:
    talhoes = [x for x in d["talhoes"] if x["coordenadas"]]
    areas = [
        (s["area_tipo"], anel)
        for s in d["sinalizacoes"]
        for anel in s["coordenadas"]
    ]
    pontos = [p for x in talhoes for p in x["coordenadas"]]
    pontos += [p for _, anel in areas for p in anel]

    # Mapa de fundo (OpenStreetMap). Se não der, usa o desenho esquemático.
    fundo = obter_mapa_base(pontos) if pontos else None

    largura = pdf.epw
    altura = 88.0
    if fundo:
        altura = largura * fundo["altura_px"] / fundo["largura_px"]

    _secao(pdf, "3. Mapa das origens", altura_minima=altura + 30)

    if not pontos:
        _texto(pdf, "Sem geometrias cadastradas para os talhões deste lote.", 9, (100, 100, 100))
        return

    x0 = pdf.l_margin
    y0 = pdf.get_y()

    if fundo:
        fator = largura / fundo["largura_px"]

        def proj(lon: float, lat: float):
            px, py = fundo["projetar"](lon, lat)
            return x0 + px * fator, y0 + py * fator

        pdf.image(BytesIO(fundo["imagem"]), x=x0, y=y0, w=largura, h=altura)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.2)
        pdf.rect(x0, y0, largura, altura)
        opacidade_talhao = 0.35
        km_largura = fundo["largura_px"] * fundo["metros_por_pixel"] / 1000
        km_altura = fundo["altura_px"] * fundo["metros_por_pixel"] / 1000
        nota_extensao = (
            f"Quadro de aproximadamente {fmt_num(km_largura, 1)} km x "
            f"{fmt_num(km_altura, 1)} km."
        )
    else:
        minx = min(p[0] for p in pontos)
        maxx = max(p[0] for p in pontos)
        miny = min(p[1] for p in pontos)
        maxy = max(p[1] for p in pontos)
        lat0 = (miny + maxy) / 2
        kx = math.cos(math.radians(lat0))
        gw = max((maxx - minx) * kx, 1e-9)
        gh = max(maxy - miny, 1e-9)

        margem = 8.0
        escala = min((largura - 2 * margem) / gw, (altura - 2 * margem) / gh)
        desloc_x = (largura - gw * escala) / 2
        desloc_y = (altura - gh * escala) / 2

        def proj(lon: float, lat: float):
            return (
                x0 + desloc_x + (lon - minx) * kx * escala,
                y0 + altura - desloc_y - (lat - miny) * escala,
            )

        pdf.set_fill_color(248, 250, 248)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.2)
        pdf.rect(x0, y0, largura, altura, style="DF")
        opacidade_talhao = 1.0
        nota_extensao = (
            "Extensão aproximada da área: "
            f"{fmt_num(gw * 111.32, 1)} km x {fmt_num(gh * 111.32, 1)} km."
        )

    # Talhões (verde)
    pdf.set_fill_color(187, 247, 208)
    pdf.set_draw_color(22, 101, 52)
    pdf.set_line_width(0.5)
    for x in talhoes:
        pts = _pontos_do_anel(proj, x["coordenadas"])
        if len(pts) >= 3:
            with pdf.local_context(fill_opacity=opacidade_talhao):
                pdf.polygon(pts, style="DF")

    # Áreas restritas por cima, translúcidas
    cores_area = {
        "embargo": ((220, 38, 38), (153, 27, 27)),
        "desmatamento": ((234, 88, 12), (154, 52, 18)),
    }
    for tipo_area, anel in areas:
        cor_fundo, cor_borda = cores_area.get(
            tipo_area, ((220, 38, 38), (153, 27, 27))
        )
        pts = _pontos_do_anel(proj, anel)
        if len(pts) < 3:
            continue
        with pdf.local_context(fill_opacity=0.45):
            pdf.set_fill_color(*cor_fundo)
            pdf.set_draw_color(*cor_borda)
            pdf.set_line_width(0.4)
            pdf.polygon(pts, style="DF")

    # Nomes dos talhões
    for x in talhoes:
        px, py = proj(x["longitude"], x["latitude"])
        _rotulo_no_mapa(pdf, x["nome"], px, py)

    # Atribuição do mapa de fundo (obrigatória)
    if fundo:
        pdf.set_font("Helvetica", size=6.5)
        texto_atribuicao = t(fundo["atribuicao"])
        largura_atribuicao = pdf.get_string_width(texto_atribuicao) + 2
        with pdf.local_context(fill_opacity=0.8):
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(
                x0 + largura - largura_atribuicao, y0 + altura - 4,
                largura_atribuicao, 4, style="F",
            )
        pdf.set_text_color(60, 60, 60)
        pdf.text(
            x0 + largura - largura_atribuicao + 1, y0 + altura - 1.2,
            texto_atribuicao,
        )

    # Legenda
    pdf.set_line_width(0.2)
    ly = y0 + altura + 3
    itens = [
        ("Talhão de origem", (187, 247, 208), (22, 101, 52)),
        ("Embargo", (252, 165, 165), (153, 27, 27)),
        ("Desmatamento", (253, 186, 116), (154, 52, 18)),
    ]
    lx = x0
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(60, 60, 60)
    for rotulo, cor_fundo, cor_borda in itens:
        pdf.set_fill_color(*cor_fundo)
        pdf.set_draw_color(*cor_borda)
        pdf.rect(lx, ly, 4, 3, style="DF")
        pdf.set_xy(lx + 5.5, ly - 0.8)
        pdf.cell(32, 4.6, t(rotulo))
        lx += 42
    pdf.set_text_color(0, 0, 0)

    pdf.set_y(ly + 6)
    if fundo:
        origem_mapa = (
            f"Mapa de fundo: {fundo['atribuicao']} (licença ODbL). "
        )
    else:
        origem_mapa = (
            "Representação esquemática, sem mapa de fundo (indisponível "
            "no momento da geração). "
        )
    _texto(
        pdf,
        origem_mapa + nota_extensao + " Coordenadas em WGS 84 (EPSG:4326).",
        7.5, (100, 100, 100),
    )


def _secao_documentos(pdf: FPDF, d: dict) -> None:
    _secao(pdf, "4. Documentos de certificação (versões vigentes)")
    estilos_situacao = {
        "valido": None,
        "sem_validade": FontFace(color=(100, 100, 100)),
        "a_vencer": FontFace(fill_color=(254, 243, 199)),
        "vencido": FontFace(fill_color=(254, 226, 226)),
    }
    linhas, estilos = [], []
    for doc in d["documentos"]:
        linhas.append([
            f"{ROTULO_ENTIDADE.get(doc['entidade_tipo'], doc['entidade_tipo'])}: {doc['entidade_nome']}",
            ROTULO_TIPO_DOC.get(doc["tipo"], doc["tipo"]),
            f"v{doc['versao']}",
            doc["nome_arquivo"],
            fmt_data(doc["data_validade"]),
            ROTULO_SITUACAO_DOC.get(doc["situacao"], doc["situacao"]),
        ])
        estilos.append(estilos_situacao.get(doc["situacao"]))
    _tabela(
        pdf,
        ["Entidade", "Documento", "Versão", "Arquivo", "Validade", "Situação"],
        linhas,
        (23, 15, 7, 27, 12, 12),
        estilos=estilos,
        vazio="Nenhum documento vigente cadastrado para as origens deste lote.",
    )


def _secao_sinalizacoes(pdf: FPDF, d: dict) -> None:
    _secao(pdf, "5. Áreas restritas (embargos e desmatamento)")
    linhas, estilos = [], []
    for s in d["sinalizacoes"]:
        revisao = s["status_revisao"]
        detalhe_revisao = ""
        if revisao != "pendente":
            detalhe_revisao = (
                f"{s['revisado_por'] or 'Revisor removido'} em "
                f"{fmt_datahora(s['revisado_em'])}"
            )
        parecer = s["parecer"] or ""
        linhas.append([
            s["talhao_nome"],
            f"{s['area_identificador']}\n{ROTULO_AREA.get(s['area_tipo'], s['area_tipo'])} | "
            f"{s['area_fonte']} | ref. {fmt_data(s['area_data_referencia'])}",
            f"{fmt_num(s['sobreposicao_ha'], 2)} ha\n({fmt_num(s['percentual_do_talhao'], 2)}% do talhão)",
            ROTULO_REVISAO.get(revisao, revisao),
            "\n".join(x for x in (parecer, detalhe_revisao) if x) or "-",
        ])
        if revisao == "confirmada":
            estilos.append(FontFace(fill_color=(254, 226, 226)))
        elif revisao == "pendente":
            estilos.append(FontFace(fill_color=(254, 243, 199)))
        else:
            estilos.append(None)
    _tabela(
        pdf,
        ["Talhão", "Área restrita", "Sobreposição", "Revisão", "Parecer / revisor"],
        linhas,
        (14, 29, 17, 15, 25),
        estilos=estilos,
        vazio="Nenhum talhão de origem se sobrepõe a áreas restritas cadastradas.",
    )


def _local_etapa(e: dict) -> str:
    tipo = e["tipo"]
    partes = []
    if tipo == "transporte":
        if e.get("modal"):
            partes.append(ROTULO_MODAL.get(e["modal"], e["modal"]))
        if e.get("origem") or e.get("destino"):
            partes.append(f"{e.get('origem') or '?'} -> {e.get('destino') or '?'}")
        if e.get("placa_veiculo"):
            partes.append(f"Placa {e['placa_veiculo']}")
        if e.get("transportadora"):
            partes.append(e["transportadora"])
    elif tipo == "exportacao":
        if e.get("pais_destino"):
            partes.append(f"Destino: {e['pais_destino']}")
        if e.get("importador"):
            partes.append(f"Importador: {e['importador']}")
        if e.get("navio"):
            partes.append(f"Navio: {e['navio']}")
    else:
        local = e.get("local_nome")
        uf = "/".join(x for x in (e.get("municipio"), e.get("estado")) if x)
        if local:
            partes.append(local)
        if uf:
            partes.append(uf)
    if e.get("documento_referencia"):
        partes.append(f"Doc.: {e['documento_referencia']}")
    return "\n".join(partes) or "-"


def _quantidades_etapa(e: dict, peso_lote) -> str:
    if e["automatica"]:
        return f"Lote: {fmt_kg(peso_lote)}"
    linhas = []
    if e.get("quantidade_entrada_kg") is not None:
        linhas.append(f"Entrou: {fmt_kg(e['quantidade_entrada_kg'])}")
    if e.get("quantidade_saida_kg") is not None:
        linhas.append(f"Saiu: {fmt_kg(e['quantidade_saida_kg'])}")
    if e.get("diferenca_kg") is not None:
        linhas.append(f"Dif.: {fmt_kg(e['diferenca_kg'])}")
    return "\n".join(linhas) or "-"


def _secao_cadeia(pdf: FPDF, d: dict) -> None:
    _secao(pdf, "6. Cadeia de custódia")
    cadeia = d["cadeia"]
    peso = d["lote"]["peso_total_kg"]

    linhas, estilos = [], []
    for e in cadeia["etapas"]:
        rotulo = ROTULO_ETAPA.get(e["tipo"], e["tipo"])
        nome = rotulo if e["automatica"] else f"{e['ordem']}. {rotulo}"
        linhas.append([
            nome,
            ROTULO_STATUS_ETAPA.get(e["status"], e["status"]),
            _local_etapa(e),
            fmt_datahora(e.get("data_entrada")),
            fmt_datahora(e.get("data_saida")),
            e.get("responsavel") or "-",
            _quantidades_etapa(e, peso),
        ])
        estilos.append(
            FontFace(fill_color=(235, 245, 255)) if e["automatica"] else None
        )
    _tabela(
        pdf,
        ["Etapa", "Situação", "Local / trajeto", "Entrada", "Saída", "Responsável", "Quantidades"],
        linhas,
        (14, 11, 24, 12, 12, 12, 15),
        estilos=estilos,
    )

    if cadeia["etapas_pendentes"]:
        nomes = ", ".join(
            ROTULO_ETAPA.get(p, p) for p in cadeia["etapas_pendentes"]
        )
        _texto(pdf, f"Etapas ainda não registradas: {nomes}.", 9, (133, 77, 14))
        pdf.ln(1)

    for e in cadeia["etapas"]:
        movimentos = e.get("movimentacoes") or []
        if not movimentos:
            continue
        _subtitulo(
            pdf,
            f"Histórico de movimentações: {e['ordem']}. {ROTULO_ETAPA.get(e['tipo'], e['tipo'])}",
        )
        _tabela(
            pdf,
            ["Data/hora", "Tipo", "Quantidade", "Responsável", "Documento", "Registrado por", "Observação"],
            [
                [
                    fmt_datahora(m["ocorrida_em"]),
                    ROTULO_MOV.get(m["tipo"], m["tipo"]),
                    fmt_kg(m["quantidade_kg"]) if m["quantidade_kg"] is not None else "-",
                    m["responsavel"] or "-",
                    m["documento_referencia"] or "-",
                    m["registrado_por"] or "Usuário removido",
                    m["observacao"] or "-",
                ]
                for m in movimentos
            ],
            (14, 14, 12, 15, 13, 14, 18),
            alinhar=("LEFT", "LEFT", "RIGHT", "LEFT", "LEFT", "LEFT", "LEFT"),
        )


def _nota_final(pdf: FPDF, d: dict) -> None:
    pdf.ln(2)
    _texto(
        pdf,
        "Este relatório foi gerado automaticamente pelo sistema Fronteira AgroTrace em "
        f"{fmt_datahora(d['gerado_em'])}. As informações de conformidade, documentos e "
        "áreas restritas refletem o estado dos cadastros no momento da geração; "
        "os dados de áreas restritas atualmente cadastrados podem ser simulados "
        "(ver campo de fonte).",
        7.5, (100, 100, 100),
    )


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def gerar_pdf_relatorio(dados: dict) -> bytes:
    """Monta o PDF do relatório de rastreabilidade a partir dos dados coletados."""
    codigo = dados["lote"]["codigo"]

    pdf = RelatorioPDF(codigo)
    pdf.alias_nb_pages()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_title(t(f"Relatório de rastreabilidade - Lote {codigo}"))
    pdf.set_author("Fronteira AgroTrace")
    pdf.set_creator("Fronteira AgroTrace")
    pdf.set_subject(t("Rastreabilidade de commodities agrícolas"))
    pdf.add_page()

    _cabecalho(pdf, dados)
    _secao_conformidade(pdf, dados)
    _secao_origem(pdf, dados)
    _secao_mapa(pdf, dados)
    _secao_documentos(pdf, dados)
    _secao_sinalizacoes(pdf, dados)
    _secao_cadeia(pdf, dados)
    _nota_final(pdf, dados)

    return bytes(pdf.output())