import sys
sys.path.insert(1, './pesquisabr')
import configs 

from util_memsql import MemSQL_Conexao
from pesquisabr_memsql import PesquisaBRMemSQL, PesquisaBRMemSQLTeste
from pesquisabr import PesquisaBR
## Instância da Conexão que deve ser utilizada pelos Modelos
def Db_Instance():
    return MemSQL_Conexao(**configs.DB_CONFIG_PROD)

def teste_pb():
    pb = PesquisaBR()
    pb.testes()

def teste_pb_criterio():
    _criterios = '((purgação adj2 mora) com ((integr$ ou tota$) com dívida ou débito ou pagamento) ou débito) e ((busca adj2 apreensao) ou 911/??69)'
    _texto = {'texto':'texto aqui responsabilidade civil do estado','numero':123}
    pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
    pb.print_resumo()

def teste_pbmem():
    pbmem = PesquisaBRMemSQLTeste(db_instance=Db_Instance())
    pbmem.testes_processamento()

def teste_pesquisar():
    pbmem = PesquisaBRMemSQL(db_instance=Db_Instance(), print_debug=True)
    consulta = "'dano moral' adj10 estetico nao presumido"
    retorno = pbmem.pre_pesquisar(sessao = 'teste',criterios_and_or_not = consulta, tipo_documento = 'diversos')
    print('Retorno: ', retorno)

def teste_mapa():
    pbmem = PesquisaBRMemSQL(db_instance=Db_Instance())
    consulta = "'dano moral' adj10 estetico nao presumido"
    pb = PesquisaBR(criterios=consulta)
    mapa = pbmem.carregar_mapa(tipo_documento='diversos', id_documento=2982175)
    pb.novo_mapa_texto(mapa_texto=mapa)
    pb.print_resumo()

#teste_pbmem()
teste_pesquisar()
#teste_pb()
#teste_pb_criterio()
#teste_mapa()

