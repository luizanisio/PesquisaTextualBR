# -*- coding: utf-8 -*-
from pesquisabr import PesquisaBRTestes
from app_config import PATH_URL_API
from app_regras_testes import smart_request_get_post

from collections import Counter
import json

from multiprocessing import Pool, cpu_count, Manager
from datetime import datetime
from pesquisabr.util import Util

MULTIPLICADOR = 10
N_THREADS = 30 # cpu_count() * 2

arq_falhas = './stress_falhas.txt'
arq_resumo = './stress_resumo.txt'
falhas = []
dados_testes = []
testes = []
# prepara um texto com pelo menos 10k para teste
TAMANHO_TEXTO_GIGANTE = 10000
# carrega a lista de testes da classe multiplicando pelo tamanho do teste
texto_gigante_base = 'esse é um teste de texto que foi multiplicado para ficar gigante bla bla bla bla bla bla bla bla bla '
texto_gigante = texto_gigante_base
print (f'Utilizando {N_THREADS} threads')
for i, d in enumerate(PesquisaBRTestes.testes_completos()): 
    dados_testes.append(d)
    if len(texto_gigante)< TAMANHO_TEXTO_GIGANTE:
        texto_gigante += f'{(d["texto"])} '

# constrói o texto gigante
while len(texto_gigante) < TAMANHO_TEXTO_GIGANTE:
    texto_gigante += texto_gigante_base
# texto com 10k
print(f'Texto gigante criado com {len(texto_gigante)} caracters')
dados_testes.append({'texto':texto_gigante, 'criterio': 'teste E texto ADJ10 gigante com bla','retorno':True})    

# teste com regex
dados_testes.append({"texto": "esse ofício 12", "criterio" : "r:esse\\W.*12$", "retorno" : True})

# multiplica o teste 
dados_testes *=  MULTIPLICADOR

def realizar_teste(i):
    d = dados_testes[i]
    dados_post = {'texto': d['texto'], 'criterio': d['criterio'], 'detalhar': False}
    esperado = d['retorno']
    _ini = datetime.now()
    r = smart_request_get_post(f'{PATH_URL_API}analisar_criterio',json = dados_post)
    _tempo = round((datetime.now()-_ini).total_seconds(),2)
    recebido = r.get('retorno')
    if recebido == esperado:
        res = 'ok'
    else:
        res = 'falha'
        falhas.append(d)
        dtstr = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        with open(arq_falhas, "a") as f:
            f.write(f'{dtstr} \t {json.dumps(d)} >> {_tempo}s\n')
    testes.append(res)
    print(f'Teste {i+1}/{len(dados_testes)} {res} >> ', Counter(testes), f'{_tempo}s')

def teste_inicial():
    r = smart_request_get_post(f'{PATH_URL_API}cache')
    assert r.get('ok'), 'Teste de limpeza de cache falhou'
    r = smart_request_get_post(f'{PATH_URL_API}health')
    assert r.get('ok'), 'Teste de health falhou'
    print('Cache reiniciado e health testado')

if __name__ == '__main__':
    print('##########################################################################')
    print('Iniciando os testes de stress na URL: ', PATH_URL_API)
    print('==========================================================================')

    try:
        teste_inicial()
        print(f'Processando {len(dados_testes)} testes')
        tempo = None
        ini = datetime.now()
        dtstr = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        Util.map_thread(realizar_teste, range(len(dados_testes)), n_threads = N_THREADS)
        tempo = round((datetime.now()-ini).total_seconds(),2)
        print('----------------------------------------------')
        print('Resultado: ', Counter(testes), f' em {tempo}s')
        print('----------------------------------------------')
        dtstr = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    finally:
        # no caso de erro, o tempo não é contado
        tempo = tempo if tempo else round((datetime.now()-ini).total_seconds(),2)
        qtd_testes = len(dados_testes)
        erro = ''
        if qtd_testes>len(testes):
            erro = ' **** ERRO: TESTES INCONPLETOS'
        with open(arq_resumo, "a") as f:
            f.write(f'{dtstr} \t {Counter(testes)} de {qtd_testes} >> {tempo}s {erro}\n')
