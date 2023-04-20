# Colocar um import em cada linha
name = "pesquisabr"
#import pesquisabr.pesquisabr as pesquisabr
#import pesquisabr.pesquisabr_testes as pesquisabr_testes
from pesquisabr.pesquisabr import PesquisaBR
from pesquisabr.pesquisabr_regras import RegrasPesquisaBR
from pesquisabr.pesquisabr_regras_util import UtilRegrasConfig
from pesquisabr.util import Util
from pesquisabr.pesquisabr_extracao import UtilExtracaoRe
#from pesquisabr.pesquisabr_relacao_testes import PesquisaBRTestes
from pesquisabr.pesquisabr_relacao_testes import TESTES_RETORNO_COMPLETO, TESTES_EXTRACAO, TESTES_EXTRACAO_REGRAS, \
                                                 TESTES_COMPLETOS, TESTES_TEXTOS, TESTES_CRITERIOS, \
                                                 TESTES_GRIFAR, TESTES_CABECALHO_RODAPE, TESTE_COM_REMOVER
#import pesquisabr.util_memsql
#import pesquisabr.pesquisabr_memsql
 