import unittest
import re 

# https://www.datacamp.com/community/tutorials/making-http-requests-in-python?utm_source=adwords_ppc&utm_campaignid=1455363063&utm_adgroupid=65083631748&utm_device=c&utm_keyword=&utm_matchtype=b&utm_network=g&utm_adpostion=&utm_creative=278443377095&utm_targetid=aud-299261629574:dsa-429603003980&utm_loc_interest_ms=&utm_loc_physical_ms=1001541&gclid=CjwKCAiAxKv_BRBdEiwAyd40N_nVtlAEzbZkyYk-7fWaGjt6giO0CWYEeaKKa2bGoes1E4xUXQGDwhoCtNcQAvD_BwE

import requests

class TestAppRegras(unittest.TestCase):

    def teste_regras(self):
        dados = {"texto": "esse ofício 12 texto tem umas receitas de pão e de bolos legais 123 456 um dois são vários testes três com o oficio número 5.174", 
                 "detalhar":0, 
                 "tags":"teste"}
        r = requests.post('http://localhost:8000/analisar_regras',data = dados)
        esperado = { "extracoes": [ [ "12", "numero 5174" ], [], [ "456", " um " ] ], 
                     "rotulos": [ "oficio", "teste regex", "teste" ] }
        self.assertDictEqual(r.json(), esperado)

    def teste_criterio(self):
        dados = {"texto": "esse é um texto legal", "criterio": " texto PROX10 legal", "detalhar": "1"}
        r = requests.post('http://localhost:8000/analisar_criterio',data = dados)
        esperado = { "criterios": "texto PROX10 legal",
                     "criterios_aon": "texto AND legal",
                     "retorno": True,
                     "texto": "esse e um texto legal"}
        self.assertDictEqual(r.json(), esperado)

if __name__ == '__main__':
    unittest.main(buffer=True)

