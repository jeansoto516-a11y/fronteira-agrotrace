import os

import weasyprint
from weasyprint import HTML

from app.core.config import settings

HTML_TESTE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4;
    margin: 2cm 1.8cm;
    @bottom-right {
      content: "Página " counter(page) " de " counter(pages);
      font-size: 9pt;
      color: #555;
    }
  }
  body { font-family: sans-serif; font-size: 11pt; color: #1a1a1a; }
  h1 { font-size: 18pt; margin: 0 0 4pt 0; }
  .sub { color: #555; margin-bottom: 14pt; }
  table { width: 100%; border-collapse: collapse; margin-top: 10pt; }
  th, td { border: 1px solid #bbb; padding: 5pt 7pt; text-align: left; }
  th { background: #eef2ef; }
  .ok { color: #166534; font-weight: bold; }
</style>
</head>
<body>
  <h1>Relatório de rastreabilidade (teste)</h1>
  <p class="sub">Fronteira AgroTrace: ação, conformidade, geolocalização, são, nº 1.234,56 kg</p>

  <table>
    <tr><th>Item</th><th>Situação</th><th>Quantidade</th></tr>
    <tr><td>Acentuação (áéíóú ãõ ç)</td><td class="ok">Completo</td><td>1.234,56 kg</td></tr>
    <tr><td>Tabela com borda</td><td class="ok">Completo</td><td>480 kg</td></tr>
  </table>

  <p style="margin-top: 16pt">Desenho vetorial (SVG embutido):</p>
  <svg width="160" height="90" viewBox="0 0 160 90" xmlns="http://www.w3.org/2000/svg">
    <polygon points="10,70 60,10 120,25 150,75" fill="#bbf7d0" stroke="#166534" stroke-width="2"/>
  </svg>
</body>
</html>
"""


def main():
    print(f"WeasyPrint versão: {weasyprint.__version__}")
    os.makedirs(settings.PASTA_UPLOADS, exist_ok=True)
    caminho = os.path.join(settings.PASTA_UPLOADS, "teste_weasyprint.pdf")
    pdf = HTML(string=HTML_TESTE).write_pdf()
    with open(caminho, "wb") as arquivo:
        arquivo.write(pdf)
    print(f"PDF gerado ({len(pdf)} bytes): {caminho}")


if __name__ == "__main__":
    main()