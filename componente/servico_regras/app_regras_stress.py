# -*- coding: utf-8 -*-
from pesquisabr.pesquisabr_testes import TESTES_COMPLETOS

import requests
from collections import Counter
import json

from multiprocessing import Pool, cpu_count, Manager
from datetime import datetime
from pesquisabr.util import Util

MULTIPLICADOR = 1
N_THREADS = 50

arq_falhas = './stress_falhas.txt'
arq_resumo = './stress_resumo.txt'
falhas = []
dados_testes = []
testes = []
print (f'Utilizando {cpu_count()} cores')
for i, d in enumerate(TESTES_COMPLETOS*MULTIPLICADOR): 
    d["id"] = str(i)
    dados_testes.append(d)

def realizar_teste(i):
    d = dados_testes[i]
    dados_post = {'texto': d['texto'], 'criterio': d['criterio'], 'detalhar': False}
    esperado = d['retorno']
    r = requests.post('http://localhost:8000/analisar_criterio',json = dados_post)
    recebido = r.json().get('retorno')
    if recebido == esperado:
        res = 'ok'
    else:
        res = 'falha'
        falhas.append(d)
        dtstr = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        with open(arq_falhas, "a") as f:
            f.write(f'{dtstr} \t {json.dumps(d)} \n')
    testes.append(res)
    print(f'Teste {i} {res} >> ', Counter(testes))


if __name__ == '__main__':
    print(f'Processando {len(dados_testes)} testes')
    ini = datetime.now()
    dtstr = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    Util.map_thread(realizar_teste, range(len(dados_testes)), n_threads = N_THREADS)
    tempo = round((datetime.now()-ini).total_seconds(),2)
    print('Resultado: ', Counter(testes), f' em {tempo}s')
    dtstr = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    with open(arq_resumo, "a") as f:
         f.write(f'{dtstr} \t {Counter(testes)} >> {tempo}s \n')
