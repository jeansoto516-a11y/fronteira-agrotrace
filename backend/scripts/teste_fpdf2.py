import os

import fpdf
from fpdf import FPDF
from fpdf.fonts import FontFace

from app.core.config import settings

# As fontes padrão do PDF só aceitam o conjunto Latin-1 (cobre todo o
# português). Pontuação "bonita" e emojis precisam ser trocados.
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


class PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.set_text_color(110, 110, 110)
        self.cell(
            0, 6, f"Página {self.page_no()} de {{nb}}", align="R"
        )


def main():
    print(f"fpdf2 versão: {fpdf.__version__}")

    pdf = PDF(format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, t("Relatório de rastreabilidade (teste)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, t("Fronteira AgroTrace: ação, conformidade, são, nº 1.234,56 kg"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Texto com pontuação fora do Latin-1 e emoji, para provar a troca
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(
        0, 5,
        t("Teste de troca de caracteres: travessão \u2014 aspas \u201cdemo\u201d e emoji \U0001F600 viram texto seguro."),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    # Desenho de polígono (como será o mapa das origens)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, t("Desenho de polígono"), new_x="LMARGIN", new_y="NEXT")
    x0, y0 = pdf.get_x(), pdf.get_y() + 2
    pdf.set_fill_color(187, 247, 208)
    pdf.set_draw_color(22, 101, 52)
    pdf.set_line_width(0.5)
    pdf.polygon(
        [(x0 + 5, y0 + 40), (x0 + 30, y0 + 5), (x0 + 65, y0 + 14), (x0 + 80, y0 + 42)],
        style="DF",
    )
    pdf.set_y(y0 + 48)

    # Tabela com texto longo (quebra de linha) e várias linhas (2ª página)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, t("Tabela"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=9)
    pdf.set_draw_color(180, 180, 180)
    estilo_cabecalho = FontFace(emphasis="BOLD", fill_color=(238, 242, 239))
    with pdf.table(
        col_widths=(30, 45, 25),
        headings_style=estilo_cabecalho,
        line_height=5,
        text_align=("LEFT", "LEFT", "RIGHT"),
    ) as tabela:
        cab = tabela.row()
        for titulo in ("Item", "Situação", "Quantidade"):
            cab.cell(t(titulo))
        for i in range(1, 46):
            linha = tabela.row()
            linha.cell(t(f"Linha {i}"))
            linha.cell(t(
                "Completo, com texto longo para testar a quebra de linha dentro da célula da tabela"
                if i % 7 == 0 else "Completo"
            ))
            linha.cell(t(f"{i * 12.5:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", ".")))

    os.makedirs(settings.PASTA_UPLOADS, exist_ok=True)
    caminho = os.path.join(settings.PASTA_UPLOADS, "teste_fpdf2.pdf")
    pdf.output(caminho)
    print(f"PDF gerado ({os.path.getsize(caminho)} bytes): {caminho}")


if __name__ == "__main__":
    main()