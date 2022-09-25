from copy import deepcopy
from random import random, shuffle
import unittest
import re 
from pesquisabr import PesquisaBR
from pesquisabr import TESTES_COMPLETOS, TESTES_EXTRACAO, TESTES_EXTRACAO_REGRAS, \
                       TESTES_TEXTOS, TESTES_CRITERIOS, TESTES_GRIFAR, \
                       TESTES_CABECALHO_RODAPE, TESTE_COM_REMOVER, TESTES_RETORNO_COMPLETO
from pesquisabr import RegrasPesquisaBR, UtilExtracaoRe

class TestPesquisaBR(unittest.TestCase):
    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        self.maxDiff = 5000

    def teste(self):
        self.assertTrue(len(TESTES_COMPLETOS)>0)
        self.assertTrue(len(TESTES_TEXTOS)>0)
        self.assertTrue(len(TESTES_CRITERIOS)>0)
        self.assertTrue(len(TESTES_GRIFAR)>0)
        self.assertTrue(len(TESTES_COMPLETOS)>0)
        self.assertTrue(len(TESTES_CABECALHO_RODAPE)>0)
        self.assertTrue(len(TESTES_EXTRACAO)>0)
        self.assertTrue(len(TESTES_EXTRACAO_REGRAS)>0)
        self.assertTrue(len(TESTES_RETORNO_COMPLETO)>0)
        self.assertTrue(len(TESTE_COM_REMOVER)>0)

    def limpar_chaves(self, dicionario, chaves):
        if type(dicionario) is list:
            return [self.limpar_chaves(_, chaves) for _ in dicionario]
        for c in list(dicionario.keys()):
            if c in chaves:
                dicionario.pop(c, None)

    def teste_tokenizacao(self):
        for i, t in enumerate(TESTES_TEXTOS):
            pb = PesquisaBR(texto=t['texto'])
            mapa = pb.mapa_texto
            with self.subTest(f'tokenização - mapa final {i}/{len(TESTES_TEXTOS)}'):
                print(f'Teste de Mapa: {i}/{len(TESTES_TEXTOS)}', mapa)
                self.assertDictEqual(t['mapa'],mapa)

    def teste_tokenizacao_criterios(self):
        for i, t in enumerate(TESTES_CRITERIOS):
            with self.subTest(f'tokenização - critério {i}/{len(TESTES_CRITERIOS)}'):
                pb = PesquisaBR(criterios = str(t['criterio']))
                print(f'-----------------------------------------------------------------')
                print(f'== Critérios: {i}/{len(TESTES_CRITERIOS)} =======================')
                print(f'Critério {i}/{len(TESTES_CRITERIOS)}: ', str(t['criterio']))
                print(f'Critério tokenizado: ', pb.tokens_criterios)
                print(f'           esperado: ', t['criterio_tokens'])
                print(f'Critério    : ', pb.criterios)
                print(f'Critério AON: ', pb.criterios_and_or_not)
                if t.get('criterio_final'):
                   self.assertEqual(t['criterio_final'],pb.criterios)    
                self.assertCountEqual(t['criterio_tokens'],pb.tokens_criterios)
                self.assertEqual(t['criterio_aon'],pb.criterios_and_or_not)

    def teste_grifar_texto(self):
        grifar_pbr = [_ for _ in TESTES_GRIFAR if _['criterio'][:2].lower() !="r:"]
        for i, t in enumerate(grifar_pbr):
            with self.subTest(f'grifar texto PesquisaBr - {i}/{len(grifar_pbr)}'):
                texto = t['texto'] # PesquisaBR.RE_QUEBRA.sub('\n', str(t['texto']) )
                pb = PesquisaBR(texto = texto, criterios = str(t['criterio']))
                texto_processado = pb.processar_texto_posicoes(texto)
                texto_grifado = pb.grifar_criterios(texto)
                texto_processado_esperado = t['texto_processado']
                texto_grifado_esperado = t['texto_grifado']
                texto_processado = str(PesquisaBR.corrige_quebras_para_br(texto_processado, True))
                texto_grifado = str(PesquisaBR.corrige_quebras_para_br(texto_grifado, True))
                texto_processado_esperado = str(PesquisaBR.corrige_quebras_para_br(texto_processado_esperado, True))
                texto_grifado_esperado = str(PesquisaBR.corrige_quebras_para_br(texto_grifado_esperado, True))
                if texto_grifado_esperado != texto_grifado or texto_processado_esperado != texto_processado:
                    print('Critério: ', pb.criterios)
                    print('Texto original : ', str(PesquisaBR.corrige_quebras_para_br(texto, True)))
                    print('Texto espaçado : ', texto_processado )
                    print('      esperado : ', texto_processado_esperado )
                    print('Texto  grifado : ', texto_grifado )
                    print('      esperado : ', texto_grifado_esperado )
                self.assertEqual(texto_processado,texto_processado_esperado)
                self.assertEqual(texto_grifado,texto_grifado_esperado)
        grifar_re = [_ for _ in TESTES_GRIFAR if _['criterio'][:2].lower() =="r:"]
        for i, t in enumerate(grifar_re):
            with self.subTest(f'grifar texto regex - {i}/{len(grifar_re)}'):
                texto = t['texto'] # PesquisaBR.RE_QUEBRA.sub('\n', str(t['texto']) )
                texto_processado = UtilExtracaoRe.processar_texto(texto)
                criterio = t['criterio'][2:]
                extracoes = UtilExtracaoRe.extrair_regex(texto = texto, criterio= criterio)
                texto_grifado = UtilExtracaoRe.grifar_texto(texto, extracoes)
                texto_processado_esperado = str(t['texto_processado'])
                texto_grifado_esperado = str(t['texto_grifado'])
                texto_processado = str(PesquisaBR.corrige_quebras_para_br(texto_processado, True))
                texto_grifado = str(PesquisaBR.corrige_quebras_para_br(texto_grifado, True))
                texto_processado_esperado = str(PesquisaBR.corrige_quebras_para_br(texto_processado_esperado, True))
                texto_grifado_esperado = str(PesquisaBR.corrige_quebras_para_br(texto_grifado_esperado, True))
                if texto_grifado_esperado != texto_grifado or texto_processado_esperado != texto_processado:
                    print('Critério: ', t['criterio'])
                    print('Texto original : ', str(PesquisaBR.corrige_quebras_para_br(texto, True)))
                    print('Texto espaçado : ', texto_processado )
                    print('      esperado : ', texto_processado_esperado )
                    print('Texto  grifado : ', texto_grifado )
                    print('      esperado : ', texto_grifado_esperado )
                self.assertEqual(texto_processado,texto_processado_esperado)
                self.assertEqual(texto_grifado,texto_grifado_esperado)

    def teste_cabecalho_rodape(self):
        for i, t in enumerate(TESTES_CABECALHO_RODAPE):
            with self.subTest(f'cabeçalho e rodapé - {i+1}/{len(TESTES_CABECALHO_RODAPE)}'):
                texto = PesquisaBR.corrige_quebras_para_n(t['texto'], True) 
                # para debug quando o teste der errado
                texto_aspas = RegrasPesquisaBR.remover_texto_aspas(texto)
                ###
                pbr = RegrasPesquisaBR(regras = t['regras_externas'])
                retorno = pbr.aplicar_regras(texto = texto, detalhar=True, primeiro_do_grupo=False, extrair=True)
                retorno = retorno.get('regras',[])
                retorno = sorted(retorno, key = lambda k: k.get('rotulo',''))
                esp_rotulos = sorted( t.get('esperado',[]) ) 
                esp_textos =  t.get('textos',[])
                ret_rotulos = sorted([r['rotulo'] for r in retorno])
                ret_textos = [r['texto'] for r in retorno]
                if esp_textos != ret_textos:
                    print('Teste: ', i)
                    print('TEXTO RAW   : ', texto)
                    print('TEXTO ASPAS : ', texto_aspas)
                    print('TEXTOS ESP  : ', esp_textos)
                    print('TEXTOS RET  : ', ret_textos)
                self.assertEqual(esp_rotulos, ret_rotulos)
                self.assertDictEqual({'d' : esp_textos}, {'d': ret_textos})

    ###########################################################
    ## básicos - tokens, critérios, etc
    def teste_criterios_tokens(self):
        _criterios = 'esse teste simples'
        _texto = 'esse é um teste simples repetindo teste simples'
        pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
        if not pb.retorno():
            self.print_erro('TEXTO EM DICIONÁRIO - esperado False')
            pb.print_resumo()
        self.assertEqual(pb.retorno(), True)
        # verifica os tokens
        tokens_esperados = ['esse','e','um','teste','simples','repetindo','teste','simples']
        self.assertCountEqual(pb.tokens_texto, tokens_esperados)
        # verifica os tokens únicos
        tokens_esperados = ['esse','e','um','teste','simples','repetindo']
        self.assertCountEqual(pb.tokens_texto_unicos, tokens_esperados)
        # verifica crit[erios]
        self.assertEqual(pb.criterios, 'esse E teste E simples')
        # verifica AON
        self.assertEqual(pb.criterios_and_or_not, 'esse AND teste AND simples')
        # verifica o mapa
        mapa_texto = {'e': {'c': [''], 'p': [0], 't': [1]},
                      'esse': {'c': [''], 'p': [0], 't': [0]},
                      'repetindo': {'c': [''], 'p': [0], 't': [5]},
                      'simples': {'c': ['', ''], 'p': [0, 0], 't': [4, 7]},
                      'teste': {'c': ['', ''], 'p': [0, 0], 't': [3, 6]},
                      'um': {'c': [''], 'p': [0], 't': [2]}}
        self.assertDictEqual(pb.mapa_texto, mapa_texto)
        # singulares
        _texto = 'casas tres simples abbtas thrs ghdls wcasas ycasas as es is os us '
        _texto += ' ' + ' '.join(PesquisaBR.LST_SINGULAR_IGNORAR)
        pb = PesquisaBR(texto=_texto, criterios='', print_debug=False)
        tokens_esperados = ['casa','simples','tres','abbtas','ghdls','thrs','wcasas','ycasas','a','e','il','o','u']
        tokens_esperados += PesquisaBR.LST_SINGULAR_IGNORAR
        self.assertCountEqual(pb.tokens_texto_unicos, list(set(tokens_esperados)))

    ###########################################################
    ## básicos - tokens, critérios, etc
    def teste_sinonimos(self):
        _criterios = 'ele adj3 alegre'
        _texto = 'ele está muito feliz'
        pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
        if not pb.retorno():
            self.print_erro('SINÔNIMOS - esperado True')
            pb.print_resumo()
        self.assertEqual(pb.retorno(), True)

        # desativa o dicionário e testa novamente
        pb = PesquisaBR(texto='', criterios=_criterios, print_debug=False)
        pb.SINONIMOS = {}
        pb.novo_texto(_texto,atualizar_pesquisa=True)
        if pb.retorno():
            self.print_erro('SINÔNIMOS - esperado False')
            pb.print_resumo()
        self.assertEqual(pb.retorno(), False)

        pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
        # verifica o mapa
        mapa_texto = {'ele': {'t': [0], 'p': [0], 'c': ['']}, 
                      'esta': {'t': [1], 'p': [0], 'c': ['']}, 
                      'muito': {'t': [2], 'p': [0], 'c': ['']}, 
                      'feliz': {'t': [3], 'p': [0], 'c': ['']}}
        print(pb.mapa_texto)              
        self.assertDictEqual(pb.mapa_texto, mapa_texto)

    def teste_texto_dicionario_1(self):
        _criterios = 'texto com civil não aqui'
        _texto = {'texto':'texto aqui responsabilidade civil do estado','numero':123}
        pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
        if pb.retorno():
            self.print_erro('TEXTO EM DICIONÁRIO - esperado False')
            pb.print_resumo()
        self.assertEqual(pb.retorno(), False)

    def teste_texto_dicionario_2(self):
        _criterios = '((purgação adj2 mora) com ((integr$ ou tota$) com dívida ou débito ou pagamento) ou débito) e ((busca adj2 apreensao) ou 911/??69)'
        _texto = {'texto':'texto aleatório para passar - purgação de mora por ocorrer na integração de uma dívida no débito para ocorrer busca e apreensao','numero':123}
        pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
        if not pb.retorno():
            self.print_erro('TEXTO EM DICIONÁRIO - esperado True')
            pb.print_resumo()
        self.assertEqual(pb.retorno(), True)

    # esse teste valida apenas o método de remover_texto_criterio, usando o texto bruto enviado
    # pois ele não pré-processa o texto, isso é responsabilidade do analisador de regras
    def testes_remocao_textos_regras(self):
        pbr=RegrasPesquisaBR()
        texto_original = 'Teste de texto removido e com trecho entre aspas "esse trecho tem que sair" e aqui outras \'aspas quaisquer\' ok'
        texto = UtilExtracaoRe.processar_texto(texto_original)
        with self.subTest(f'remover aspas'):
             criterios = 'casa adj2 papel remover(aspas) outra coisa qualquer'
             criterios_esperado = 'casa adj2 papel outra coisa qualquer'
             texto_esperado = 'Teste de texto removido e com trecho entre e aqui outras ok'
             _texto, _criterios, _texto_original = pbr.remover_texto_criterio(texto=texto, criterios=criterios, texto_original=texto_original)
             _texto = re.sub('\s+',' ',_texto)
             _texto_original = re.sub('\s+',' ',_texto_original)
             _criterios = re.sub('\s+',' ',_criterios)
             self.assertEqual(_texto_original,texto_esperado)
             self.assertEqual(_texto, UtilExtracaoRe.processar_texto(texto_esperado))
             self.assertEqual(_criterios, criterios_esperado)
        with self.subTest(f'remover trecho e aspas'):
             criterios = 'casa adj2 papel remover(aspas) outra coisa qualquer remover(texto removido)'
             criterios_esperado = 'casa adj2 papel outra coisa qualquer'
             texto_esperado = 'Teste de e com trecho entre e aqui outras ok'
             _texto, _criterios, _texto_original = pbr.remover_texto_criterio(texto=texto, criterios=criterios, texto_original=texto_original)
             _texto = re.sub('\s+',' ',_texto)
             _texto_original = re.sub('\s+',' ',_texto_original)
             _criterios = re.sub('\s+',' ',_criterios)
             self.assertEqual(_texto_original,texto_esperado)
             self.assertEqual(_texto, UtilExtracaoRe.processar_texto(texto_esperado))
             self.assertEqual(_criterios, criterios_esperado)
        with self.subTest(f'remover trecho'):
             criterios = 'casa adj2 papel outra coisa qualquer remover(texto removido)'
             criterios_esperado = 'casa adj2 papel outra coisa qualquer'
             texto_esperado = 'Teste de e com trecho entre aspas "esse trecho tem que sair" e aqui outras \'aspas quaisquer\' ok'
             _texto, _criterios, _texto_original = pbr.remover_texto_criterio(texto=texto, criterios=criterios, texto_original=texto_original)
             _texto = re.sub('\s+',' ',_texto)
             _texto_original = re.sub('\s+',' ',_texto_original)
             _criterios = re.sub('\s+',' ',_criterios)
             # as aspas são padronizadas na avaliação do texto
             texto_esperado = str(texto_esperado).replace('“','"').replace('”','"').replace("'",'"')
             texto_original = str(texto_original).replace('“','"').replace('”','"').replace("'",'"')
             self.assertEqual(_texto_original,texto_esperado)
             self.assertEqual(_texto, UtilExtracaoRe.processar_texto(texto_esperado))
             self.assertEqual(_criterios, criterios_esperado)
        

    ################################################################################
    # realiza testes internos e pode receber testes complementares
    # se um teste falhar, ativa o debug e realiza novamente o teste
    # para apresentar facilitar a análise - interrompe os testes ao falhar um deles
    ################################################################################
    def testes_completos(self):
        """
        Teste com as principais regras e combinações conhecidas
        """
        pb=PesquisaBR()
        pbr=RegrasPesquisaBR()
        pb.print_debug = False
        for i, teste in enumerate(TESTES_COMPLETOS):
            with self.subTest(f'testes completos básicos - {i+1}/{len(TESTES_COMPLETOS)}'):
                falha = ''
                texto = teste['texto']
                criterio = str(teste['criterio'])
                # avaliação de critérios de remoção
                print('==========================================================')
                print('==========================================================')
                print(f'TESTE: {i+1} - {criterio}  ==> esperado {teste["retorno"]}')

                pb.novo_texto(texto)
                print('Novo texto', pb.texto, criterio)
                r_texto, r_criterio, _ = pbr.remover_texto_criterio(texto = pb.texto, criterios = criterio)
                print('Novo texto', r_texto, r_criterio)
                if r_criterio is not None:
                    print('Critério: ', criterio)
                    print('    novo: ', r_criterio)
                    print(' remover: ', pbr.retornar_criterios_remocao(criterio))
                    print('Texto: ', texto)
                    print(' novo: ', r_texto)
                    texto = r_texto
                    criterio = r_criterio

                pb.novo_texto(texto)
                pb.novo_criterio(criterio)
                if teste["retorno"]:
                    print(f'   AON => {pb.criterios_and_or_not}')
                retorno = None
                if pb.erros =='':
                    retorno = pb.analisar_mapa_pesquisa()
                if pb.erros!= '' or retorno != teste['retorno']:
                    if pb.erros != '':
                        falha = f'ERRO NOS CRITÉRIOS: {pb.erros}'
                        self.print_erro(falha)
                    else:
                        falha = f'ERRO NO RETORNO ESPERADO: {retorno} != {teste["retorno"]}'
                        self.print_erro(falha)
                    pb.print_debug = True
                    pb.print()
                    pb.analisar_mapa_pesquisa()
                    self.fail('ERRO NO RETORNO')
                # verifica a reconstrução da pesquisa apenas pelo mapa 
                # o resultado tem que ser o mesmo ao criar o mapa em tempo de execução
                pbmapa = PesquisaBR(criterios=pb.criterios, mapa_texto = pb.mapa_texto)            
                retorno = pbmapa.analisar_mapa_pesquisa() if pbmapa.erros == '' else None
                if pbmapa.erros!= '' or retorno != teste['retorno']:
                    falha = 'ERRO AO REFAZAR A PESQUISA PELO MAPA'
                    self.print_erro(falha)
                    print(f' - Teste: {i} - {criterio}  ==> esperado {teste["retorno"]}')
                    if pbmapa.erros != '':
                        print(' -- ERRO NOS CRITÉRIOS: ', pbmapa.erros)
                    pbmapa.print_debug = True
                    pbmapa.print()
                    pbmapa.analisar_mapa_pesquisa()
                    self.fail('ERRO NO CRITÉRIO OU RETORNO')
                # verifica o clone dos critérios
                # o resultado tem que ser o mesmo
                pbclone = pb.clone_criterios()
                pbclone.novo_mapa_texto(mapa_texto=pb.mapa_texto)
                retorno = pbclone.retorno() if pbclone.erros == '' else None
                if pbclone.erros!= '' or retorno != teste['retorno']:
                    falha = 'ERRO AO REFAZER A PESQUISA PELO CLONE'
                    self.print_erro(falha)
                    print(f' - Teste: {i} - {criterio}  ==> esperado {teste["retorno"]}')
                    if pbclone.erros != '':
                        print(' -- ERRO NOS CRITÉRIOS DO CLONE: ', pbmapa.erros)
                    pbclone.print_debug = True
                    pbclone.print()
                    pbclone.analisar_mapa_pesquisa()
                    self.fail('ERRO NO CLONE')

                # verifica o AND OR NOT
                # convertendo a pesquisa em AND OR NOT, caso a pesquisa toda retorne TRUE, o 
                # critério AND OR NOT tem que retornar TRUE também
                # AND OR NOT é usado para acelerar a pesquisa em bancos textuais como o MemSQL/SingleStore
                criterio_aon = re.sub(' AND ',' E ', str(pb.criterios_and_or_not))
                criterio_aon = re.sub(' OR ',' OU ', criterio_aon)
                criterio_aon = re.sub(' NOT ',' NAO ', criterio_aon)
                _retorno_aon = teste.get('retorno_aon',teste["retorno"])
                if criterio_aon.strip() !='':
                    if _retorno_aon==1 or _retorno_aon == True:
                        pb.novo_criterio(criterio_aon)
                        if pb.erros =='':
                            retorno = pb.analisar_mapa_pesquisa()
                        if pb.erros != '' or not retorno:
                            falha = 'CRITÉRIO AND OR NOT - FALHA ESPERADO TRUE ***'
                            print(falha)
                            if pb.erros != '':
                                print('ERRO NOS CRITÉRIOS: ', pb.erros)
                            pb.print_debug = True
                            pb.print()
                            pb.analisar_mapa_pesquisa()
                            self.fail('ERRO NO CRITÉRIO AON')
                else:
                    # não faz o teste do AON
                    #print(f'   AON => VAZIO *** ')
                    pass

    ###########################################################
    ## REGRAS
    REGRAS_TESTES = [{'grupo' : 'receitas_bolo', 'rotulo': 'Receita de Bolo', 'regra': 'receita ADJ10 bolo'},
                {'grupo' : 'receitas_bolo', 'rotulo': 'Receita de Bolo', 'regra': 'aprenda ADJ5 fazer ADJ10 bolo'},
                {'grupo' : 'receitas_pao', 'rotulo': 'Receita de Pão', 'regra': 'receita PROX15 pao'},
                {'grupo' : 'grupo teste', 'rotulo': 'teste', 'regra': 'teste'},
                {'grupo' : 'grupo removido', 'rotulo': 'removido teste', 'regra': 'teste remover(teste) remover(aspas)'},
                {'grupo' : 'grupo removido', 'rotulo': 'removido aspas', 'regra': 'removidos E trecho remover(aspas)'}
                ]
    def teste_regras_1(self):
        regras = self.REGRAS_TESTES
        # receita de bolo
        texto = 'nessa receita você vai aprender a fazer bolos incríveis'
        pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
        rotulos = pbr.aplicar_regras(texto = texto)
        print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)
        self.assertCountEqual(rotulos['rotulos'], ['Receita de Bolo'])
        # receita de pão
        texto = 'pão de ló, uma receita incrível'
        pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
        rotulos = pbr.aplicar_regras(texto = texto)
        print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)
        self.assertCountEqual(rotulos['rotulos'], ['Receita de Pão'])
        # receita de pão e bolo
        texto = 'pão de ló, uma receita incrível para uma nova forma de fazer um bolo'
        pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
        rotulos = pbr.aplicar_regras(texto = texto)
        print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)
        self.assertCountEqual(rotulos['rotulos'], ['Receita de Pão', 'Receita de Bolo'])
        # removendo teste e aspas
        texto = 'esse texto tem trechos "entre aspas que serão removidos"'
        pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
        rotulos = pbr.aplicar_regras(texto = texto)
        print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)
        self.assertCountEqual(rotulos['rotulos'], [])
        # removendo aspas
        texto = 'esse texto tem trechos "entre aspas que serão removidos"'
        pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
        rotulos = pbr.aplicar_regras(texto = texto)
        print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)
        self.assertCountEqual(rotulos['rotulos'], [])

    ###########################################################
    ## REGRAS MULTI RETORNO
    REGRAS_MULTI = [{'grupo' : 'grupo multi', 'rotulo': 'multi1', 'regra': 'R:termoa', 'ordem': 0},
                    {'grupo' : 'grupo multi', 'rotulo': 'multi2', 'regra': 'termob E termoc', 'ordem': 1},
                    {'grupo' : 'grupo multi', 'rotulo': 'multi3', 'regra': 'termod E termoe', 'ordem': 2}]
    def teste_regras_n_rotulos(self):
        # um rótulo
        texto = 'teste termoa termob termoc termod termoe'
        with self.subTest(f'Multi - primeiro do grupo'):
            pbr = RegrasPesquisaBR(regras = self.REGRAS_MULTI, print_debug=False)
            retorno = pbr.aplicar_regras(texto = texto)
            print(f'(primeiro do grupo) Rótulos encontrados para o texto: "{texto}" >> ', retorno.get('rotulos'))
            self.assertCountEqual(retorno['rotulos'], ['multi1'])
        # n rótulos
        with self.subTest(f'Multi - todos do grupo'):
            pbr = RegrasPesquisaBR(regras = self.REGRAS_MULTI, print_debug=False)
            retorno = pbr.aplicar_regras(texto = texto, primeiro_do_grupo = False)
            print(f'(todos do grupo) Rótulos encontrados para o texto: "{texto}" >> ', retorno.get('rotulos'))
            self.assertCountEqual(retorno['rotulos'], ['multi1', 'multi2', 'multi3'])
        # n rótulos e extrações
        with self.subTest(f'Multi - todos do grupo e extrações'):
            pbr = RegrasPesquisaBR(regras = self.REGRAS_MULTI, print_debug=False)
            retorno = pbr.aplicar_regras(texto = texto, primeiro_do_grupo = False, extrair=True)
            print(f'(todos do grupo) Rótulos encontrados para o texto: "{texto}" >> ', retorno.get('rotulos'))
            self.assertCountEqual(retorno['rotulos'], ['multi1', 'multi2', 'multi3'])
            extracoes = [{'fim': 12, 'inicio': 6, 'texto': 'termoa'}]
            self.assertDictEqual({'e': retorno['extracoes']}, {'e': extracoes})
        # n rótulos detalhes
        with self.subTest(f'Multi - todos do grupo e detalhes'):
            pbr = RegrasPesquisaBR(regras = self.REGRAS_MULTI, print_debug=False)
            retorno = pbr.aplicar_regras(texto = texto, primeiro_do_grupo = False, extrair=True, detalhar=True)
            print(f'(todos do grupo) Rótulos encontrados para o texto: "{texto}" >> ', retorno)
            regras_esperadas = [{'grupo': 'grupo multi', 'rotulo': 'multi1', 'regra': 'R:termoa', 'ordem': 0, 'texto': 'teste termoa termob termoc termod termoe', 
                                 'criterios': 'termoa', "extracoes": [{"fim": 12,"inicio": 6,"texto": "termoa"}]},
                                {'grupo': 'grupo multi', 'rotulo': 'multi2', 'regra': 'termob E termoc', 'ordem': 1, 'texto': 'teste termoa termob termoc termod termoe', 'criterios': 'termob E termoc', 'criterios_aon': 'termob AND termoc'}, 
                                {'grupo': 'grupo multi', 'rotulo': 'multi3', 'regra': 'termod E termoe', 'ordem': 2, 'texto': 'teste termoa termob termoc termod termoe', 'criterios': 'termod E termoe', 'criterios_aon': 'termod AND termoe'}
                                ]
            esperado = {"qtd_regras": 3,
                        "rotulos": ["multi1","multi2","multi3"],
                        "texto_analise": 'teste termoa termob termoc termod termoe',
                        "texto": "teste termoa termob termoc termod termoe",
                        "texto_regex": "teste termoa termob termoc termod termoe"
                    }
            retorno.pop('tempo', None)
            self.assertDictEqual({'e': retorno['regras']}, {'e': regras_esperadas})
            retorno.pop('regras', None)
            # algumas chaves para facilitar analisar o erro se ocorrer
            self.assertCountEqual(retorno['rotulos'], ['multi1', 'multi2', 'multi3'])
            # no detalhamento, as extrações não devem ser retornadas aqui
            self.assertCountEqual(retorno.get('extracoes',[]), esperado.get('extracoes',[]))
            #completo para verificar tudo
            self.assertDictEqual(retorno, esperado)

    def teste_regras_remocao(self):
        testes = [{'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': 'receita OU pao OU bolo remover(de receit*#) remover(e bolo) remover(de pão)'}],
                   'texto' :'esse é um teste de receita de pao e bolo com remoção', 'rotulos':[]},
                  {'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': 'bolo ou pão remover(aspas)'}],
                   'texto' :'esse é um teste de receita de "pao e bolo com remoção"', 'rotulos':[]}, 
                  {'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': 'receita E bolo E pao NAO teste remover(esse é um teste)'}],
                   'texto' :'esse é um teste de receita de "pao e bolo com remoção"', 'rotulos':['rotulo']}, 
                  {'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': ' bolo E pao remover(esse*##)'}],
                   'texto' :'esse é um teste de muitas coisas como as receitas de: \n "pao e bolo"', 'rotulos':['rotulo']}, 
                  {'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': ' bolo E pao NAO receita remover(receita?)'}],
                   'texto' :'esse é um teste de muitas coisas como as receitas de "pao e bolo" e a receita de jiló', 'rotulos':['rotulo']}, 
                  {'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': ' teto E te E to NAO teste NAO texto remover(te&t&)'}],
                   'texto' :'esse é um teste de texto de teto te to', 'rotulos':['rotulo']}, 
                  {'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': 'usando testando remover("usando") remover("tes*ndo")'}],
                   'texto' :'teste entre aspas "usando" "testando"', 'rotulos':[]}, 
                  {'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': 'casa adj2 papel remover(termo&)'}],
                   'texto' :'casa termoa termob termoc termod de papel', 'rotulos':['rotulo']}, 
                  {'regras': [{'grupo' : 'grupo', 'rotulo': 'rotulo', 'regra': 'teste NAO (bolo ou pao) remover(aspas)'}],
                   'texto' :'esse é um teste de receita de "pao e bolo com remoção"', 'rotulos':['rotulo']}, 
        ]
        for i,teste in enumerate(testes):
            with self.subTest(f'teste_regras_remocao {i+1}/{len(testes)}'):
                regras = teste['regras']
                texto = teste['texto']
                esperados = teste['rotulos']
                pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
                rotulos = pbr.aplicar_regras(texto = texto)
                print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)
                print(f' - critérios: "{regras[0]["regra"]}"')
                self.assertCountEqual(rotulos['rotulos'], esperados)

    def teste_regras_2(self):
        falha = ''
        __teste_regras__ = [{'grupo' : 'grupo 1', 'rotulo': 'ok1', 'regra': 'casa ADJ2 papel'},
                            {'grupo' : 'grupo 1', 'rotulo': 'ok1', 'regra': 'seriado ADJ2 "la casa de papel"'},
                            {'grupo' : 'grupo 2', 'rotulo': 'ok2', 'regra': '"a casa de papel"'},
                            {'grupo' : 'grupo teste', 'rotulo': 'teste', 'regra': 'teste'}
                            ]
        __teste_regras_2__ = [{'grupo' : 'grupo cabecalho', 'rotulo': 'cabecalho', 'regra': 'texto', 'qtd_cabecalho':10},
                                {'grupo' : 'grupo rodape', 'rotulo': 'rodape', 'regra': 'rodapé', 'qtd_rodape':10},
                                {'grupo' : 'grupo cab rodap', 'rotulo': 'cabrodap', 'regra': 'texto E teste','qtd_cabecalho':10, 'qtd_rodape':23},
                                {'grupo' : 'grupo n cab rodap', 'rotulo': 'ncabrodap', 'regra': 'NÃO cabecalho','qtd_cabecalho':20, 'qtd_rodape':20}
                            ]
        __texto_teste__ = 'o seriado a casa de papel é legal'
        __texto_teste_2__ = 'texto com teste depois do cabecalho e teste antes do rodapé'
        #
        _obj_teste = RegrasPesquisaBR(regras = __teste_regras__, print_debug=False)
        resdic = _obj_teste.aplicar_regras(__texto_teste__)
        self.assertCountEqual(resdic['rotulos'], ['ok1','ok2'])
        # incluindo teste na pesquisa
        resdic = _obj_teste.aplicar_regras(__texto_teste__ + ' com esse teste')
        self.assertCountEqual(resdic['rotulos'], ['ok1','ok2','teste'])
        # texto sem regras aplicáveis
        resdic = _obj_teste.aplicar_regras('esse é um texto qualquer com a casa mas não tem nada de papel')
        self.assertCountEqual(resdic['rotulos'], [])
        # testes de cabeçalho e rodapé 
        _obj_teste = RegrasPesquisaBR(regras = __teste_regras_2__, print_debug=False)
        resdic = _obj_teste.aplicar_regras(__texto_teste_2__)
        self.assertCountEqual(resdic['rotulos'], ['cabrodap','cabecalho','ncabrodap','rodape'])

    def teste_extracao(self):
        for i, teste in enumerate(TESTES_EXTRACAO):
            with self.subTest(f'Extração Regex: {i}'):
                r = RegrasPesquisaBR.aplicar_criterios(texto = teste['texto'],
                                                       detalhar =1, extrair = 1, grifar = 1, 
                                                       criterios = teste['criterio'])
                r.pop('tempo',None)
                e = teste['esperado']
                #print('------------------------')
                #print('r: ', r)
                #print('e: ', e)
                self.assertDictEqual(r, e)  

    def teste_extracao_regras(self):
        for i, teste in enumerate(TESTES_EXTRACAO_REGRAS):
            with self.subTest(f'Extração regras: {i}'):
                pbr = RegrasPesquisaBR(regras = teste['regras_externas'])
                #print('REGRAS: ', pbr.regras)
                r = pbr.aplicar_regras(texto = teste['texto'], detalhar =1, extrair = 1, primeiro_do_grupo=False)
                r.pop('tempo',None)
                e = teste['esperado']
                # extrações
                _e = e.pop('regras',[])
                _r = r.pop('regras',[])
                self.limpar_chaves(_e, ['grupo','regra'])
                self.limpar_chaves(_r, ['grupo','regra'])
                #print('------------------------')
                #print('r: ', _r)
                #print('e: ', _e)
                self.assertDictEqual({'x' : _r}, {'x' : _e})  
                # outros
                #print('------------------------')
                #print('r: ', r)
                #print('e: ', e)
                self.assertDictEqual(r, e)  

    def teste_retorno_completo(self):
        for i, teste in enumerate(TESTES_RETORNO_COMPLETO):
            with self.subTest(f'Aplicar critérios: {i}'):
                r = RegrasPesquisaBR.aplicar_criterios(texto = teste['texto'],
                                                       detalhar =1, extrair = 1, grifar = 1, 
                                                       criterios = teste['criterio'])
                r.pop('tempo',None)
                #print('r: ', r)
                self.assertDictEqual(r, teste['esperado'])  

    def testes_com_remover(self):
        for i, teste in enumerate(TESTE_COM_REMOVER):
            with self.subTest(f'Remoção de Texto: {i}'):
                processado = UtilExtracaoRe.processar_texto(teste['texto'])
                texto, criterio, original = RegrasPesquisaBR.remover_texto_criterio(texto = processado,
                                                       criterios = teste['criterio'],
                                                       texto_original=teste['texto'])
                #esperado = re.sub('\s+',' ', teste['texto_limpo'])
                #texto = re.sub('\s+',' ', texto)
                esperado = PesquisaBR.corrige_quebras_para_br(teste['texto_limpo'])
                texto = PesquisaBR.corrige_quebras_para_br(texto)
                if texto != esperado:
                    print('Texto original   : ', teste['texto'])
                    print('Texto processado : ', processado)
                    print('Texto padronizado: ', RegrasPesquisaBR.padronizar_aspas(processado))
                    print('Texto limpo      : ', texto)
                    print('Texto esperado   : ', teste['texto_limpo'])
                    print('critério         : ', teste['criterio'])
                self.assertEqual(texto, esperado)  

    def print_erro(self, msg_erro):
        if not msg_erro:
            return
        print( '###########################################################################')
        print( '########## ')
        print(f'########## {msg_erro}')
        print( '########## ')
        print( '###########################################################################')


if __name__ == '__main__':
    unittest.main(buffer=True, failfast=True)