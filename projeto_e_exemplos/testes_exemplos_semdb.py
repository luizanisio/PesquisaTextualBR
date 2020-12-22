import sys
sys.path.insert(1, './pesquisabr')
from pesquisabr import PesquisaBR, RegrasPesquisaBR

def teste_pb():
    pb = PesquisaBR()
    pb.testes()

def teste_pb_criterio():
    _criterios = '((purgação adj2 mora) com ((integr$ ou tota$) com dívida ou débito ou pagamento) ou débito) e ((busca adj2 apreensao) ou 911/??69)'
    _texto = {'texto':'texto aqui responsabilidade civil do estado','numero':123}
    pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
    pb.print_resumo()

def teste_pb_regras():
    regras = [{'grupo' : 'receitas_bolo', 'rotulo': 'Receita de Bolo', 'regra': 'receita ADJ10 bolo'},
              {'grupo' : 'receitas_bolo', 'rotulo': 'Receita de Bolo', 'regra': 'aprenda ADJ5 fazer ADJ10 bolo'},
              {'grupo' : 'receitas_pao', 'rotulo': 'Receita de Pão', 'regra': 'receita PROX15 pao'},
              {'grupo' : 'grupo teste', 'rotulo': 'teste', 'regra': 'teste'}]
    # receita de bolo
    texto = 'nessa receita você vai aprender a fazer bolos incríveis'
    pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
    rotulos = pbr.aplicar_regras(texto = texto)
    print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)
    # receita de pão
    texto = 'pão de ló, uma receita incrível'
    pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
    rotulos = pbr.aplicar_regras(texto = texto)
    print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)

#teste_pb()
#teste_pb_criterio()
teste_pb_regras()

