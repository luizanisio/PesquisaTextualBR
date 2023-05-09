# -*- coding: utf-8 -*-
import unittest

# https://www.datacamp.com/community/tutorials/making-http-requests-in-python?utm_source=adwords_ppc&utm_campaignid=1455363063&utm_adgroupid=65083631748&utm_device=c&utm_keyword=&utm_matchtype=b&utm_network=g&utm_adpostion=&utm_creative=278443377095&utm_targetid=aud-299261629574:dsa-429603003980&utm_loc_interest_ms=&utm_loc_physical_ms=1001541&gclid=CjwKCAiAxKv_BRBdEiwAyd40N_nVtlAEzbZkyYk-7fWaGjt6giO0CWYEeaKKa2bGoes1E4xUXQGDwhoCtNcQAvD_BwE

from pesquisabr import PesquisaBR
from pesquisabr import TESTES_RETORNO_COMPLETO, TESTES_EXTRACAO, TESTES_EXTRACAO_REGRAS, \
                                                 TESTES_COMPLETOS, TESTES_TEXTOS, TESTES_CRITERIOS, \
                                                 TESTES_GRIFAR, TESTES_CABECALHO_RODAPE, TESTE_COM_REMOVER, \
                                                 TESTES_BASICOS_RE_PRONTOS
from app_config import PATH_URL_API
# cria um smart_request mais resiliente a falhas pois o teste pode sobrecarregar o serviço
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time

def smart_request():
    # https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#retry-on-failure
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
        #method_whitelist=["HEAD", "GET", "POST", "OPTIONS"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http

TIMEOUT = 60 * 10
def smart_request_get_post(url, **kwargs):
    session = smart_request()
    if any(kwargs):
       r = session.post(url, timeout = TIMEOUT, **kwargs)
    else:
       r = session.get(url, timeout = TIMEOUT)
    if r.status_code == 200:
        r = r.json()
    else:
        r.raise_for_status()
    session.close()
    return r

class TestAppRegrasBase(unittest.TestCase):
    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        self.maxDiff = 5000

    # limpa as chaves que geralmente não são testadas
    def limpa_request(self, r, manter = [], remover = []):
        remover += ['tempo', 'criterios_analise', 'texto_analise', 
                    'analisar-criterios', 'analisar-regras', 
                    'front-end', 'rodando-testes']
        remover = [_ for _ in remover if _ not in manter]
        [r.pop(_, None) for _ in remover]
        return r

    # limpa as chaves que não estão no esperado
    def limpa_request_para_esperado(self, r, esperado):
        manter = list(esperado.keys())
        [r.pop(_, None) for _ in list(r.keys()) if _ not in manter]
        return r

    # limpa as regras para análise
    def limpa_regras(self, dados_retorno, manter = []):
        if (not any(manter)) or ('regras' not in dados_retorno):
            return
        regras = dados_retorno.get('regras',[])
        for r in regras:
            for c in list(r.keys()):
                if c not in manter:
                   r.pop(c, None)
        dados_retorno['regras'] = regras

    # limpa apenas chaves de controle do front-end
    def limpa_request_front(self, r):
        return self.limpa_request(r, manter=['criterios_analise','texto_analise'])

class TestAppRegrasCriterios(TestAppRegrasBase):
    TESTE_RESUMIDO = True
    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        self.maxDiff = 5000

    def teste_regex_timed_out(self):
        for chave, esperado in [('teste-timeout',408),('testetimeout',408),('detalhar', 0)]:
            with self.subTest(f'Regex timed out'):
                dados = {"texto": '123', f'{chave}': True, 'outro_dado' : 1}
                try:
                    res_code = 0
                    smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
                except requests.HTTPError as e:
                    res_code = e.response.status_code
                    dados = json.loads(e.response.content)
                    # verifica o dicionário de retorno quando ocorre erro de timeout
                    self.assertEqual(1, dados.get('outro_dado',0))
                    self.assertEqual(408, dados.get('status',0))
                    self.assertEqual('regex timed out', dados.get('erro',''))
                self.assertEqual( res_code, esperado)

    def teste_catastrophic_backtracking(self):
        with self.subTest(f'Catastrophic backtracking'):
            texto, esperado = '012345678901234567890123456789z',False
            regra = 'r:^(\d+)*$'
            dados = {"texto": texto, 
                    "criterios" : regra,
                    "detalhar" : 1}
            r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
            retorno = r.get('retorno')
            self.assertEqual(retorno, esperado)

    def teste_texto_simples(self):
        for i, teste in enumerate(TEXTOS_TESTES_SIMPLES_QUEBRAS):
            with self.subTest(f'Textos testes simples {i+1}'):
                texto, esperado = teste
                dados = {"texto": texto, 
                        "criterios" : "x",
                        "detalhar" : 1}
                r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
                retorno = PesquisaBR.corrige_quebras_para_br(r.get('texto',''))
                esperado = PesquisaBR.corrige_quebras_para_br(esperado)
                self.assertDictEqual({'r':retorno}, {'r':esperado})

    def teste_criterios_regex(self):
        dados = {"texto": "esse ofício 12", 
                 "criterios" : "r:esse\\W.*12$",
                 "detalhar" : 1}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
        r = self.limpa_request(r)
        esperado = { "criterios": "esse\\W.*12$",
                     "retorno": True,
                     'extracao': [{'fim': 14, 'inicio': 0, 'texto': 'esse ofício 12'}],
                     "texto": "esse oficio 12" }
        self.assertDictEqual(r, esperado)

    def teste_regras(self):
        dados = {"texto": "esse ofício 12 texto tem umas receitas de pão e de bolos legais 123 456 um dois são vários testes três com o ofício número 5.174", 
                 "detalhar":0, "extrair" : 1, 'rodando-testes' : 1, 
                 "tags":"teste", 'regras_externas' : REGRAS_TESTES}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
        r = self.limpa_request(r)
        esperado = { "extracoes": [{"fim": 14, "inicio": 5, "texto": "ofício 12" },
                                   {"fim": 41, "inicio": 22, "texto": "ofício número 5.174"},
                                   {"fim": 96, "inicio": 91, "texto": "teste"}], 
                     "rotulos": [ "oficio", "teste regex", "teste" ] }
        self.assertDictEqual(r, esperado)

    def teste_criterio(self):
        dados = {"texto": "esse é um texto legal", "criterio": " texto PROX10 legal", "detalhar": 1}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
        r = self.limpa_request(r)
        esperado = { "criterios": "texto PROX10 legal",
                     "criterios_aon": "texto AND legal",
                     "retorno": True,
                     "texto": "esse e um texto legal"}
        self.assertDictEqual(r, esperado)

    def teste_criterio_re_pronto(self):
        testes = TESTES_SIMPLES_RE_PRONTOS + TESTES_BASICOS_RE_PRONTOS
        for i, teste in enumerate(testes):
            texto = teste.get('texto','')
            criterio = teste.get('criterio','')
            criterio = f'r:{criterio}' if criterio[:2] != 'r:' else criterio
            with self.subTest(f'Regex Prontos {i+1}'):
                 dados = {"texto": texto,
                          "detalhar": 1, "extrair" : 0, "grifar" : 0, 
                          "criterios" : criterio}
            r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
            if r.get('retorno') != teste.get('retorno'):
               print('Retorno recebido: ', r)
            self.assertEqual(r.get('retorno'), teste.get('retorno') )

    def teste_criterio_dict(self):
        dados = {"texto": {"a": "a casa de papel é um seriado bem interessante número123", "b": "segundo"}, 
                 "criterio": "(casa papel) e segund$.b.", "detalhar": 1}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json= dados)
        r = self.limpa_request(r, manter=['texto_analise'])
        esperado = {"criterios": "( casa E papel ) E segund$.B.",
                    "criterios_aon": "( casa AND papel ) AND segund*",
                    "retorno": True,
                    "texto": {
                        "A": "a casa de papel e um seriado bem interessante numero 123",
                        "B": "segundo"  },
                    "texto_analise": {'a': 'a casa de papel é um seriado bem interessante número123',
                                      'b': 'segundo'}
                    }
        # facilita a visualização do erro separar em duas análises
        self.assertEqual(r['texto'], esperado['texto'])
        r.pop('texto', None)
        esperado.pop('texto', None)
        #print('recebido: ',r['texto'])
        #print('esperado: ',esperado['texto'])
        #print(json.dumps(r))
        self.assertDictEqual(r, esperado)

    def teste_criterio_dict_regex(self):
        dados = {"texto": {"a": "a casa de papel é um seriado bem interessante número123", "b": "segundo texto da casa sem papel"}, 
                 "criterio": "r:casa.{1,20}papel", "detalhar": 1, "grifar" : 1}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json= dados)
        r = self.limpa_request(r, manter=['texto_analise'])
        esperado = { 'criterios': 'casa.{1,20}papel',
                     'extracao': [{'chave': 'a', 'fim': 15, 'inicio': 2, 'texto': 'casa de papel'},
                                  {'chave': 'b', 'fim': 31, 'inicio': 17, 'texto': 'casa sem papel'}],
                     "retorno": True,
                     "texto": {"a": "a casa de papel e um seriado bem interessante numero123",
                               "b": "segundo texto da casa sem papel"  },
                    "texto_analise": {'a': 'a casa de papel é um seriado bem interessante número123',
                                      'b': 'segundo texto da casa sem papel'},
                    'texto_grifado': {'a': 'a <mark>casa de papel</mark> é um seriado bem interessante número123',
                                      'b': 'segundo texto da <mark>casa sem papel</mark>'},
                     "retorno": True
                    }
        # facilita a visualização do erro separar em duas análises
        self.assertEqual(r['texto'], esperado['texto'])
        self.assertEqual(r['texto_analise'], esperado['texto_analise'])
        r.pop('texto', None)
        esperado.pop('texto', None)
        r.pop('texto_analise', None)
        esperado.pop('texto_analise', None)
        self.assertDictEqual(r, esperado)

    def teste_criterio_list_regex(self):
        dados = {"texto": ["a casa de papel é um seriado bem interessante número123", "segundo texto da casa sem papel"], 
                 "criterio": "r:casa.{1,20}papel", "detalhar": 1, "grifar" : 1}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json= dados)
        r = self.limpa_request(r, manter=['texto_analise'])
        esperado = { 'criterios': 'casa.{1,20}papel',
                     'extracao': [{'fim': 15, 'inicio': 2, 'texto': 'casa de papel', 'pagina': 1},
                                  {'fim': 31, 'inicio': 17, 'texto': 'casa sem papel', 'pagina': 2}],
                     "retorno": True,
                     "texto": ["a casa de papel e um seriado bem interessante numero123", "segundo texto da casa sem papel"],
                     "texto_analise": ["a casa de papel é um seriado bem interessante número123", "segundo texto da casa sem papel"],
                     'texto_grifado': ['a <mark>casa de papel</mark> é um seriado bem interessante número123',
                                       'segundo texto da <mark>casa sem papel</mark>'],
                     "retorno": True
                    }
        # facilita a visualização do erro separar em duas análises
        self.assertEqual(r['texto'], esperado['texto'])
        self.assertEqual(r['texto_analise'], esperado['texto_analise'])
        r.pop('texto', None)
        esperado.pop('texto', None)
        r.pop('texto_analise', None)
        esperado.pop('texto_analise', None)
        self.assertDictEqual(r, esperado)

    def teste_criterio_list_pesquisa(self):
        dados = {"texto": ["a casa de papel é um seriado bem interessante número123", "segundo texto da casa sem papel"], 
                 "criterio": "casa adj2 papel sem adj papel", "detalhar": 1, "grifar" : 1}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json= dados)
        r = self.limpa_request(r, manter=['texto_analise'])
        esperado = {"criterios": "casa ADJ2 papel E sem ADJ1 papel",
                    "criterios_aon": "casa AND papel AND sem AND papel",
                    "retorno": True,
                    "texto": ["a casa de papel e um seriado bem interessante numero 123",
                              "segundo texto da casa sem papel"],
                    "texto_analise": ["a casa de papel é um seriado bem interessante número123",
                                      "segundo texto da casa sem papel"],
                    "texto_grifado": ["a <mark>casa</mark> de <mark>papel</mark> é um seriado bem interessante número123",
                                      "segundo texto da <mark>casa</mark> <mark>sem</mark> <mark>papel</mark>"]
                }
        # facilita a visualização do erro separar em duas análises
        self.assertEqual(r['texto'], esperado['texto'])
        self.assertEqual(r['texto_analise'], esperado['texto_analise'])
        self.assertEqual(r['texto_grifado'], esperado['texto_grifado'])
        r.pop('texto', None)
        esperado.pop('texto', None)
        r.pop('texto_analise', None)
        esperado.pop('texto_analise', None)
        self.assertDictEqual(r, esperado)

    def teste_criterio_dict_pesquisa(self):
        dados = {"texto": {"a": "a casa de papel é um seriado bem interessante número123", "b": "segundo texto da casa sem papel"}, 
                 "criterio": "casa adj2 papel sem adj papel", "detalhar": 1, "grifar" : 1}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json= dados)
        r = self.limpa_request(r, manter=['texto_analise','criterios_analise'])
        esperado = { "criterios": "casa ADJ2 papel E sem ADJ1 papel",
                     "criterios_analise": "casa adj2 papel sem adj papel",
                     "criterios_aon": "casa AND papel AND sem AND papel",
                     "texto": {
                         "A": "a casa de papel e um seriado bem interessante numero 123",
                         "B": "segundo texto da casa sem papel" },
                     "texto_analise": {
                         "a": "a casa de papel é um seriado bem interessante número123",
                         "b": "segundo texto da casa sem papel" },
                     "texto_grifado": {
                         "a": "a <mark>casa</mark> de <mark>papel</mark> é um seriado bem interessante número123",
                         "b": "segundo texto da <mark>casa</mark> <mark>sem</mark> <mark>papel</mark>" },
                     "retorno": True
                    }
        # facilita a visualização do erro separar em duas análises
        self.assertEqual(r['texto'], esperado['texto'])
        self.assertEqual(r['texto_analise'], esperado['texto_analise'])
        self.assertEqual(r['texto_grifado'], esperado['texto_grifado'])
        r.pop('texto', None)
        esperado.pop('texto', None)
        r.pop('texto_analise', None)
        esperado.pop('texto_analise', None)
        r.pop('texto_grifado', None)
        esperado.pop('texto_grifado', None)
        self.assertDictEqual(r, esperado)

    def teste_limpeza_cache(self):
        # controle do id de cache e limpeza
        r = smart_request_get_post(f'{PATH_URL_API}health')
        id_cache = r['cache']['id_cache']
        dt_cache = r['cache']['data_carga_regras']
        self.assertTrue(r.get('ok'))
        r = smart_request_get_post(f'{PATH_URL_API}cache')
        self.assertTrue(r.get('ok'))

        # testando a limpeza de cache - modo teste
        dados = {"texto": "teste limpar cache", "detalhar":0, "extrair" : 0, 'rodando-testes' : 1, "tags":"teste", "modo_teste": 1}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
        self.assertTrue(r.get('cache_limpo'))
        dados['modo_teste'] = True
        r = smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
        self.assertTrue(r.get('cache_limpo'))

        # testando a limpeza de cache - limpar cache
        dados = {"texto": "teste limpar cache", "detalhar":0, "extrair" : 0, 'rodando-testes' : 1, "tags":"teste", "limpar_cache": True}
        r = smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
        self.assertTrue(r.get('cache_limpo'))

        # testando se a carga no banco não foi refeita
        # vai dar erro caso ocorra um recarregamento ou atualização das regras nesse momento
        # vai dar erro se as datas são de instâncias diferentes. O teste funciona se rodado em uma instância
        #r = smart_request_get_post(f'{PATH_URL_API}health')
        #id_cache2 = r['cache']['id_cache']
        #dt_cache2 = r['cache']['data_carga_regras']
        #self.assertTrue(r.get('ok'))
        #self.assertTrue(id_cache == id_cache2)
        #print('Caches datas: ', dt_cache, dt_cache2)
        #self.assertTrue(dt_cache == dt_cache2)


    def testes_retorno_completo(self):
        for i, teste in enumerate(TESTES_RETORNO_COMPLETO):
            with self.subTest(f'Retorno completo {i+1}'):
                 dados = {"texto": teste.get('texto',''),
                          "detalhar": 1, "extrair" : 1, "grifar" : 1, 
                          "criterios" : teste.get('criterio','')}
            r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
            esperado = teste.get('esperado',{})
            # ajusta o retorno para as mesmas chaves avaliadas no esperado
            r = self.limpa_request_para_esperado(r, esperado)
            esperado['texto'] = PesquisaBR.corrige_quebras_para_br(esperado['texto'], True)
            esperado['texto_grifado'] = PesquisaBR.corrige_quebras_para_br(esperado['texto_grifado'], True)
            r['texto'] = PesquisaBR.corrige_quebras_para_br(r.get('texto',''), True)
            r['texto_grifado'] = PesquisaBR.corrige_quebras_para_br(r.get('texto_grifado',''), True)
            self.assertDictEqual({'r': r}, {'r': esperado} )  

    def testes_completos_classe_pesquisabr(self):
        for i, e in enumerate(TESTES_COMPLETOS):
            subteste = f'Subteste {i}'
            with self.subTest(subteste):
                texto = e.get('texto','')
                criterio = str(e.get('criterio',''))
                esperado = e.get('retorno')
                dados = {"texto": texto, "criterio": criterio, "detalhar": 1}
                r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio', json = dados)
                retorno = r.get('retorno')
                if retorno != esperado:
                    print(f'- TESTES_COMPLETOS {i}------------------------------------------------------------------')
                    print(f'Esperado: {esperado}   Retorno: ', r.get('retorno'))
                    print('- texto: ', PesquisaBR.corrige_quebras_para_br(r.get('texto')) )
                    print('- critério: ', r.get('criterios'))
                    dados['texto'] = PesquisaBR.corrige_quebras_para_br(dados['texto'])
                    print('Dados: ', dados)
                # espera true se for match e false se for match_0
                self.assertTrue(r.get('retorno') == esperado)

    def testes_filtros_regras_multi(self):
        # rodando-testes é para controlar as conversões de saída pois podem dar 
        # falso negativo de inconsistência da saída esperada
        dados = {"texto": "multi teste com vários retornos do mesmo grupo", "detalhar": 1, 
                 "extrair" : 1, "primeiro_do_grupo" : False, 'rodando-testes' : 1,
                 "filtro_tipo" : "multi", 'regras_externas' : REGRAS_TESTES, 'rodando-testes' : 1}
        with self.subTest('Filtro e Multi vários'):
            r = smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
            r = self.limpa_request(r)
            self.limpa_regras(r, ['extracoes','rotulo'])
            esperado = {"qtd_regras": 3,
                        "rotulos": ["multi1","multi2","multi3"],
                        "texto": "multi teste com vario retorno do mesmo grupo",
                        "texto_regex": "multi teste com varios retornos do mesmo grupo",
                        "regras": [{"rotulo": "multi1"},
                                   {"rotulo": "multi2", "extracoes": [{"fim": 5,"inicio": 0,"texto": "multi"}]},
                                   {"rotulo": "multi3"} ]
                    }
            self.assertDictEqual(r, esperado)        
        # multi único
        dados['primeiro_do_grupo'] = 1
        with self.subTest('Filtro e Multi único'):
            r = smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
            r = self.limpa_request(r, remover = ['regras'])
            esperado = {"qtd_regras": 3,
                        "rotulos": ["multi1"],
                        "texto": "multi teste com vario retorno do mesmo grupo"
                    }
            self.assertDictEqual(r, esperado)     
        # multi texto   
        dados['primeiro_do_grupo'] = 1
        dados['texto'] = [dados['texto'],'segunda página multi']
        with self.subTest('Filtro e Multi único - textos múltiplos'):
            r = smart_request_get_post(f'{PATH_URL_API}analisar_regras', json = dados)
            r = self.limpa_request(r, remover = ['regras'])
            esperado = {"qtd_regras": 3,
                        "rotulos": ["multi1"],
                        "texto": ["multi teste com vario retorno do mesmo grupo",'segunda pagina multi']
                       }
            self.assertEqual(r['texto'], esperado['texto'])
            r.pop('texto')
            esperado.pop('texto')
            self.assertDictEqual(r, esperado)

    def testes_filtros_regras_tags(self):
        # rodando-testes é para controlar as conversões de saída
        # caso tenha uma chave na regra "tags-....", a regra só é aplicada de coincidir com pelo menos uma das tags enviadas em tags-....
        # pode ser tags- ou tags_
        dados = {"texto": "teste um dois tres quatro cinco seis a b c ", "detalhar": 1, 
                 "primeiro_do_grupo" : False, 'rodando-testes' : 1,
                 'regras_externas' : REGRAS_TESTES_TAGS}
        testes = [{"esperado" : ['neutro1','neutro2'] },
                  {"tags_numero" : "um dois tres", "esperado" : ['teste1', 'teste2','teste3','neutro1','neutro2'] },
                  {"tags_numero" : "1 2 3", "esperado" : ['teste1', 'teste2','teste3','neutro1','neutro2'] },
                  {"tags_numero" : "um 1 2 dois 3 tre quatro cinco", "esperado" : ['teste1', 'teste2','teste3','neutro1','neutro2'] },
                  {"tags_numero" : "um dois", "esperado" : ['teste1', 'teste2','neutro1','neutro2'] },
                  {"tags_numero" : "um tres", "esperado" : ['teste1', 'teste3','neutro1','neutro2'] },
                  {"tags_numero" : "dois", "esperado" : ['teste2','neutro2','neutro1'] },
                  {"tags_numero" : "*", "esperado" : ['teste1', 'teste2','teste3','neutro1','neutro2'] },
                  {"tags_numero" : "*", "tags":"neutro", "esperado" : ['neutro1','neutro2'] },
                  {"tags_letra" : "*", "esperado" : ['testea', 'testeb','testec','neutro1','neutro2'] },
                  {"tags_letra" : "a", "esperado" : ['testea', 'neutro1','neutro2'] },
                  {"tags_letra" : "c a", "esperado" : ['testea', 'testec', 'neutro1','neutro2'] },
                  {"tags_letra" : "c a", "tags_numero" : "1 dois", "esperado" : ['testea', 'testec', 'teste1', 'teste2', 'neutro1','neutro2'] },
                  {"tags_letra" : "*", "tags_numero" : "*", "esperado" : ['testea', 'testeb', 'testec', 'teste1', 'teste2', 'teste3', 'neutro1','neutro2'] },
                  ]
        for teste in testes:
            with self.subTest(f'Filtro de tags: {teste.get("tags_numero","-")}'):
                if teste.get("tags_numero"):
                   dados["tags_numero"] = teste["tags_numero"]
                else:
                   dados.pop("tags_numero",None)
                if teste.get("tags_letra"):
                   dados["tags_letra"] = teste["tags_letra"]
                else:
                   dados.pop("tags_letra",None)
                if teste.get("tags"):
                   dados["tags"] = teste["tags"]
                else:
                   dados.pop("tags",None)
                esperado = teste['esperado']
                r = smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
                r = self.limpa_request(r)
                #print('Dados: ', dados)
                #print('Retorno: ', r)
                retornado = r.get('rotulos',[])
                esperado.sort()
                retornado.sort()
                self.assertEqual(esperado, retornado)

    def testes_dados_retorno(self):
        with self.subTest('Retorno PesquisaBR'):
            dados = {"texto": "esse teste é simples 123,45 123.123 simples", 
                     "detalhar": 1, "extrair" : 1, "grifar" : 1, "criterios" : "esse teste simples"}
            r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
            r = self.limpa_request_front(r)
            esperado = {"criterios": "esse E teste E simples",
                        "criterios_analise": "esse teste simples",
                        "criterios_aon": "esse AND teste AND simples",
                        "retorno": True,
                        "texto": "esse teste e simples 12345 123123 simples",
                        "texto_analise": "esse teste é simples 123,45 123.123 simples",
                        "texto_grifado": "<mark>esse</mark> <mark>teste</mark> é <mark>simples</mark> 123,45 123.123 <mark>simples</mark>"
                        }            
            self.assertDictEqual(r, esperado)  

        with self.subTest('Retorno Regex'):
            dados = {"texto": "esse teste é simples 123,45 123.123 simples", 
                     "detalhar": 1, "extrair" : 1, "grifar" : 1, "criterios" : "r:(esse)|(teste)|(simples)"}
            r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
            r = self.limpa_request_front(r)
            esperado = { "criterios":"(esse)|(teste)|(simples)",
                         "criterios_analise":"r:(esse)|(teste)|(simples)",
                         "extracao":[{"fim":4,"inicio":0,"texto":"esse"},
                                     {"fim":10,"inicio":5,"texto":"teste"},
                                     {"fim":20,"inicio":13,"texto":"simples"},
                                     {"fim":43,"inicio":36,"texto":"simples"}],   
                         "retorno": True,
                         "texto": "esse teste e simples 123,45 123.123 simples",
                         "texto_analise": "esse teste é simples 123,45 123.123 simples",
                         "texto_grifado": "<mark>esse</mark> <mark>teste</mark> é <mark>simples</mark> 123,45 123.123 <mark>simples</mark>"
                       }
            # facilita a visualização do erro separar em duas análises
            self.assertEqual(r['texto'], esperado['texto'])
            r.pop('texto', None)
            esperado.pop('texto', None)
            self.assertEqual(r['texto_analise'], esperado['texto_analise'])
            r.pop('texto_analise', None)
            esperado.pop('texto_analise', None)
            self.assertEqual(r['texto_grifado'], esperado['texto_grifado'])
            r.pop('texto_grifado', None)
            esperado.pop('texto_grifado', None)
            self.assertDictEqual(r, esperado)        

    def testes_grifar(self):
        for i, teste in enumerate(TESTES_GRIFAR):
            with self.subTest(f'Retorno grifar PesquisaBR {i+1}'):
                 dados = {"texto": teste.get('texto',''),
                          "detalhar": 1, "extrair" : 1, "grifar" : 1, 
                          "criterios" : teste.get('criterio','')}
            r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
            r = self.limpa_request_front(r)
            esperado = PesquisaBR.corrige_quebras_para_br(teste.get("texto_grifado",''), True)
            r = PesquisaBR.corrige_quebras_para_br(r.get('texto_grifado',''), True)
            self.assertDictEqual({'r': r}, {'r': esperado} )  

    def testes_cabecalho_rodape(self):
        for i, teste in enumerate(TESTES_CABECALHO_RODAPE):
            with self.subTest(f'Retorno cabeçalho rodapé {i+1}'):
                 dados = {"texto": teste.get('texto',''), "detalhar": 1, "extrair" : 1, 
                          "primeiro_do_grupo" : False, 'rodando-testes' : 1,
                          'regras_externas' : teste['regras_externas'], 'rodando-testes' : 1}
            r = smart_request_get_post(f'{PATH_URL_API}analisar_regras',json = dados)
            esperado = sorted(teste.get('esperado',[]))
            rotulos = sorted(r.get('rotulos', []))
            #print('Esperado: ', esperado)
            #print('Rótulo  : ', rotulos)
            self.assertEqual(esperado, rotulos)  

    def testes_remover(self):
        for i, teste in enumerate(TESTE_COM_REMOVER):
            with self.subTest(f'Critério Remover() {i+1}'):
                 dados = {"texto": teste['texto'], "detalhar": 1, "extrair" : 0, 
                          'rodando-testes' : 1, 'criterio' : teste['criterio']}
            r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados)
            esperado = PesquisaBR.corrige_quebras_para_br(teste.get('texto_limpo',''),True)
            retornado = PesquisaBR.corrige_quebras_para_br(r.get('texto', ''),True)
            #print('Esperado: ', esperado)
            if esperado != retornado:
               print('Esperado: ', f'|{esperado}|')
               print('Retornado: ', f'|{retornado}|')
            #print('Rótulo  : ', rotulos)
            self.assertEqual(esperado, retornado)

REGRAS_TESTES = [
    {"grupo" : "grupo_teste", "rotulo": "teste", "regra": "teste", "tags": "teste", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "grupo"},
    {"grupo" : "grupo_regex", "rotulo": "teste regex", "regra": "r:teste|testar?", "tags": "teste", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "grupo"},
    {"grupo" : "grupo_oficio", "rotulo": "oficio", "regra": "r:oficio\\s?(n.{0,10})?\\d+", "tags": "teste oficio", "qtd_cabecalho":20, "qtd_rodape":20, "filtro_tipo" : "grupo"},
    {"grupo" : "grupo_multi", "rotulo": "multi2", "regra": "R:multi", "tags": "multi", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "multi", "ordem": 1},
    {"grupo" : "grupo_multi", "rotulo": "multi1", "regra": "multi", "tags": "multi", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "multi", "ordem": 0},
    {"grupo" : "grupo_multi", "rotulo": "multi3", "regra": "multi", "tags": "multi", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "multi", "ordem": 3},
    {"grupo" : "tags tipo", "rotulo": "tagtipo1", "regra": "tagtipo1", "tags-tipo": "um dois tres", "qtd_cabecalho":0, "qtd_rodape":0, "ordem": 1},
 ]

REGRAS_TESTES_TAGS = [
    {"grupo" : "grupo_um", "rotulo": "teste1", "regra": "r:um", "tags": "geral", "tags_numero": "um 1"},
    {"grupo" : "grupo_dois", "rotulo": "teste2", "regra": "r:dois", "tags": "geral", "tags_numero": "dois 2"},
    {"grupo" : "grupo_tres", "rotulo": "teste3", "regra": "r:tres", "tags": "geral","tags_numero": "tres 3"},
    {"grupo" : "grupo_neutro1", "rotulo": "neutro1", "regra": "r:teste", "tags" : "neutro n"},
    {"grupo" : "grupo_neutro2", "rotulo": "neutro2", "regra": "r:teste", "tags" : "neutro n"},
    {"grupo" : "grupo_a", "rotulo": "testea", "regra": r"r:\ba\b", "tags": "geral", "tags_letra": "a"},
    {"grupo" : "grupo_b", "rotulo": "testeb", "regra": r"r:\bb\b", "tags": "geral", "tags_letra": "b"},
    {"grupo" : "grupo_c", "rotulo": "testec", "regra": r"r:\bc\b", "tags": "geral","tags_letra": "c"},
 ]

TEXTOS_TESTES_SIMPLES_QUEBRAS = [
    ('teste de texto simples', 'teste de texto simples'),
    ('à á À Á teste ó Ò Ó ò çcÇC', 'a a a a teste o o o o cccc'),
    ('teste<br>testa\\nnada', 'teste \n testa \n nada'),
    (r'teste<br>testa\\nnada', 'teste \n testa nnada'),
    (['à á À Á teste ó Ò Ó ò çcÇC', 'teste<br>testa\\nnada'], ['a a a a teste o o o o cccc', 'teste \n testa \n nada']),
    ({'a': 'à á À Á teste ó Ò Ó ò çcÇC', 'b':'teste<br>testa\\nnada'}, {'A':'a a a a teste o o o o cccc', 'B':'teste \n testa \n nada'}),
]

TESTES_SIMPLES_RE_PRONTOS = [
    {'texto' : 'esse é um teste de regex pronto por termos', 'criterio': 'r:test<FIMTERMO><TERMO>{0,3}por', 'retorno':True},
    {'texto' : 'esse é um teste de regex pronto por termos', 'criterio': 'r:test<FIMTERMO><TERMO>{0,2}por', 'retorno':False},
    {'texto' : 'esse é um teste de cpf: 123.456.789-10 ', 'criterio': 'r:<CPF:12345678910>', 'retorno':True},
    {'texto' : 'esse é um teste de cpf: 123456789-10 ', 'criterio': 'r:<CPF:12345678910>', 'retorno':True},
    {'texto' : 'esse é um teste de cpf: 12345678910 ', 'criterio': 'r:<CPF:12345678910>', 'retorno':True},
    {'texto' : 'esse é um teste de cpf: 123.456.789-11 ', 'criterio': 'r:<CPF:12345678910>', 'retorno':False},
    {'texto' : 'esse é um teste de oab DF 1234 a', 'criterio': 'r:<OAB:df1234a>', 'retorno':True},
    {'texto' : 'esse é um teste de oab DF-1234/a', 'criterio': 'r:<OAB:df1234a>', 'retorno':True},
    {'texto' : 'esse é um teste de oab DF 1234, a', 'criterio': 'r:<OAB:df1234a>', 'retorno':False},
]

if __name__ == '__main__':
    print('##########################################################################')
    print('Iniciando os testes na URL: ', PATH_URL_API)
    print('==========================================================================')
    TestAppRegrasCriterios.TESTE_RESUMIDO = True
    unittest.main(buffer=False, failfast=True)
    
    # linha para rodar um teste específico
    # python app_regras_testes.py TestAppRegrasCriterios.testes_filtros_regras_tags
