# -*- coding: utf-8 -*-
import unittest
import json 

# https://www.datacamp.com/community/tutorials/making-http-requests-in-python?utm_source=adwords_ppc&utm_campaignid=1455363063&utm_adgroupid=65083631748&utm_device=c&utm_keyword=&utm_matchtype=b&utm_network=g&utm_adpostion=&utm_creative=278443377095&utm_targetid=aud-299261629574:dsa-429603003980&utm_loc_interest_ms=&utm_loc_physical_ms=1001541&gclid=CjwKCAiAxKv_BRBdEiwAyd40N_nVtlAEzbZkyYk-7fWaGjt6giO0CWYEeaKKa2bGoes1E4xUXQGDwhoCtNcQAvD_BwE

from pesquisabr import PesquisaBRTestes

# cria um smart_request mais resiliente a falhas pois o teste pode sobrecarregar o serviço
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
def smart_request():
    # https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#retry-on-failure
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "POST", "OPTIONS"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http

class TestAppRegras(unittest.TestCase):

    TESTE_RESUMIDO = True

    def limpa_request(self, r, manter = [], remover = []):
        remover += ['tempo', 'criterios_analise', 'texto_analise']
        remover = [_ for _ in remover if _ not in manter]
        r = r.json()
        [r.pop(_, None) for _ in remover]
        return r
        
    def teste_criterios_regex(self):
        dados = {"texto": "esse ofício 12", 
                 "criterios" : "r:esse\\W.*12$",
                 "detalhar" : 1}
        r = smart_request().post('http://localhost:8000/analisar_criterio',json = dados)
        r = self.limpa_request(r)
        esperado = { "criterios": "esse\\W.*12$",
                     "retorno": True,
                     'extracao': [{'fim': 14, 'inicio': 0, 'texto': 'esse oficio 12'}],
                     "texto": "esse oficio 12" }
        self.assertDictEqual(r, esperado)

    def teste_regras(self):
        dados = {"texto": "esse ofício 12 texto tem umas receitas de pão e de bolos legais 123 456 um dois são vários testes três com o oficio número 5.174", 
                 "detalhar":0, "extrair" : 1,
                 "tags":"teste"}
        r = smart_request().post('http://localhost:8000/analisar_regras',json = dados)
        r = self.limpa_request(r)
        esperado = { "extracoes": [{"fim": 14, "inicio": 5, "texto": "oficio 12" },
                                   {"fim": 41, "inicio": 22, "texto": "oficio numero 5.174"},
                                   {"fim": 96, "inicio": 91, "texto": "teste"}], 
                     "rotulos": [ "oficio", "teste regex", "teste" ] }
        self.assertDictEqual(r, esperado)

    def teste_criterio(self):
        dados = {"texto": "esse é um texto legal", "criterio": " texto PROX10 legal", "detalhar": 1}
        r = smart_request().post('http://localhost:8000/analisar_criterio',json = dados)
        r = self.limpa_request(r)
        esperado = { "criterios": "texto PROX10 legal",
                     "criterios_aon": "texto AND legal",
                     "retorno": True,
                     "texto": "esse e um texto legal"}
        self.assertDictEqual(r, esperado)

    def teste_criterio_dict(self):
        dados = {"texto": {"a": "a casa de papel é um seriado bem interessante numero123", "b": "segundo"}, 
                 "criterio": "(casa papel) e segund$.b.", "detalhar": 1}
        r = smart_request().post('http://localhost:8000/analisar_criterio',json= dados)
        r = self.limpa_request(r)
        esperado = {"criterios": "( casa E papel ) E segund$.B.",
                    "criterios_aon": "( casa AND papel ) AND segund*",
                    "retorno": True,
                    "texto": {
                        "A": "a casa de papel e um seriado bem interessante numero 123",
                        "B": "segundo"  }
                    }
        print('recebido: ',r['texto'])
        print('esperado: ',esperado['texto'])
        print(json.dumps(r))
        self.assertDictEqual(r, esperado)

    def teste_limpeza_cache(self):
        r = smart_request().get('http://localhost:8000/cache')
        r=r.json()
        self.assertTrue(r.get('ok'))
        r = smart_request().get('http://localhost:8000/health')
        r=r.json()
        self.assertTrue(r.get('ok'))

    def testes_completos_classe_pesquisabr(self):
        for i, e in enumerate(PesquisaBRTestes.testes_basicos(self.TESTE_RESUMIDO)):
            subteste = f'Subteste {i}'
            with self.subTest(subteste):
                texto = str(e.get('texto',''))
                criterio = str(e.get('criterio',''))
                esperado = e.get('retorno')
                dados = {"texto": texto, "criterio": criterio, "detalhar": 1}
                r = smart_request().post('http://localhost:8000/analisar_criterio', json = dados)
                r = r.json()
                retorno = r.get('retorno')
                if retorno != esperado:
                    print(f'- TESTES_COMPLETOS {i}------------------------------------------------------------------')
                    print(f'Esperado: {esperado}   Retorno: ', r.get('retorno'))
                    print('- texto: ', r.get('texto'))
                    print('- critério: ', r.get('criterios'))
                    print('Dados: ', dados)
                # espera true se for match e false se for match_0
                self.assertTrue(r.get('retorno') == esperado)

    def testes_filtros_regras_multi(self):
        dados = {"texto": "multi teste com vários retornos do mesmo grupo", "detalhar": 1, 
                 "extrair" : 1, "primeiro_do_grupo" : False,
                 "filtro_tipo" : "multi"}
        with self.subTest('Filtro e Multi vários'):
            r = smart_request().post('http://localhost:8000/analisar_regras',json = dados)
            r = self.limpa_request(r, remover = ['regras'])
            esperado = {"extracoes": [{"fim": 5,"inicio": 0,"texto": "multi"}],
                        "qtd_regras": 3,
                        "rotulos": ["multi1","multi2","multi3"],
                        "texto": "multi teste com vario retorno do mesmo grupo",
                        "texto_regex": "multi teste com varios retornos do mesmo grupo"
                    }
            self.assertDictEqual(r, esperado)        
        dados['primeiro_do_grupo'] = 1
        with self.subTest('Filtro e Multi único'):
            r = smart_request().post('http://localhost:8000/analisar_regras',json = dados)
            r = self.limpa_request(r, remover = ['regras'])
            esperado = {"extracoes": [],
                        "qtd_regras": 3,
                        "rotulos": ["multi1"],
                        "texto": "multi teste com vario retorno do mesmo grupo"
                    }
            self.assertDictEqual(r, esperado)        

    def testes_dados_retorno(self):
        with self.subTest('Retorno PesquisaBR'):
            dados = {"texto": "esse teste é simples 123,45 123.123 simples", 
                    "detalhar": 1, "extrair" : 1, "grifar" : 1, "criterios" : "esse teste simples"}
            r = smart_request().post('http://localhost:8000/analisar_criterio',json = dados)
            r = r.json()
            r.pop('tempo',None)
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
            r = smart_request().post('http://localhost:8000/analisar_criterio',json = dados)
            r = r.json()
            r.pop('tempo',None)
            esperado = { "criterios":"(esse)|(teste)|(simples)",
                         "criterios_analise":"r:(esse)|(teste)|(simples)",
                         "extracao":[{"fim":4,"inicio":0,"texto":"esse"},
                                     {"fim":10,"inicio":5,"texto":"teste"},
                                     {"fim":20,"inicio":13,"texto":"simples"},
                                     {"fim":43,"inicio":36,"texto":"simples"}],   
                         "retorno": True,
                         "texto": "esse teste e simples 123,45 123.123 simples",
                         "texto_analise": "esse teste é simples 123,45 123.123 simples",
                         "texto_grifado": "<mark>esse</mark> <mark>teste</mark> e <mark>simples</mark> 123,45 123.123 <mark>simples</mark>"
                       }
            self.assertDictEqual(r, esperado)        

if __name__ == '__main__':
    TestAppRegras.TESTE_RESUMIDO = False
    unittest.main(buffer=True)

