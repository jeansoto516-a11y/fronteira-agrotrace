# Este arquivo garante que todas as models sejam registradas no
# SQLAlchemy assim que o pacote app.models é importado — evita erros
# de relacionamento ("failed to locate a name") entre models que se
# referenciam mutuamente (ex: Produtor -> Fazenda -> Talhao).
from app.models.usuario import Usuario
from app.models.produtor import Produtor
from app.models.fazenda import Fazenda
from app.models.talhao import Talhao
from app.models.cultura import Cultura
from app.models.safra import Safra
from app.models.talhao_safra import TalhaoSafra
from app.models.colheita import Colheita
from app.models.lote import Lote
from app.models.lote_colheita import LoteColheita
from app.models.log_atividade import LogAtividade