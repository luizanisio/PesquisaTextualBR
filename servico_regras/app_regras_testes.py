# -*- coding: utf-8 -*-
import unittest

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

    def teste_criterios_regex(self):
        dados = {"texto": "esse ofício 12", 
                 "criterios" : "r:esse\\W.*12$",
                 "detalhar" : 1}
        r = smart_request().post('http://localhost:8000/analisar_criterio',json = dados)
        esperado = { "criterios": "esse\\W.*12$",
                     "retorno": True,
                     "texto": "esse oficio 12" }
        self.assertDictEqual(r.json(), esperado)

    def teste_regras(self):
        dados = {"texto": "esse ofício 12 texto tem umas receitas de pão e de bolos legais 123 456 um dois são vários testes três com o oficio número 5.174", 
                 "detalhar":0, 
                 "tags":"teste"}
        r = smart_request().post('http://localhost:8000/analisar_regras',json = dados)
        esperado = { "extracoes": [ [ "12", "numero 5174" ], [], [ "456", " um " ] ], 
                     "rotulos": [ "oficio", "teste regex", "teste" ] }
        self.assertDictEqual(r.json(), esperado)

    def teste_criterio(self):
        dados = {"texto": "esse é um texto legal", "criterio": " texto PROX10 legal", "detalhar": 1}
        r = smart_request().post('http://localhost:8000/analisar_criterio',json = dados)
        esperado = { "criterios": "texto PROX10 legal",
                     "criterios_aon": "texto AND legal",
                     "retorno": True,
                     "texto": "esse e um texto legal"}
        self.assertDictEqual(r.json(), esperado)

    def teste_criterio_dict(self):
        dados = {"texto": {"a": "a casa de papel é um seriado bem interessante numero123", "b": "segundo"}, 
                 "criterio": "(casa papel) e segund$.b.", "detalhar": 1}
        r = smart_request().post('http://localhost:8000/analisar_criterio',json= dados)
        esperado = {"criterios": "( casa E papel ) E segund$.B.",
                    "criterios_aon": "( casa AND papel ) AND segund*",
                    "retorno": True,
                    "texto": {
                        "A": "a casa de papel e um seriado bem interessante numero 123",
                        "B": "segundo"  }
                    }
        recebido = r.json()
        print('recebido: ',recebido['texto'])
        print('esperado: ',esperado['texto'])
        print(r.text)
        self.assertDictEqual(recebido, esperado)

    def teste_limpeza_cache(self):
        r = smart_request().get('http://localhost:8000/cache')
        r=r.json()
        self.assertTrue(r.get('ok'))
        r = smart_request().get('http://localhost:8000/health')
        r=r.json()
        self.assertTrue(r.get('ok'))

    def testes_completos_classe_pesquisabr(self):
        for i, e in enumerate(PesquisaBRTestes.testes_basicos()):
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

if __name__ == '__main__':
    unittest.main(buffer=True)

