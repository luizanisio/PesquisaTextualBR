# -*- coding: utf-8 -*-
# teste para aplicação de regras
# http://localhost:8000/analisar_regras?texto=esse%20texto%20tem%20uma%20receita%20de%20pao%20e%20de%20bolo%20legal&criterio=texto&debug=0
# teste para análise de critérios
# http://localhost:8000/analisar_criterio?texto=esse%20texto%20legal&criterio=texto&debug=1

# debug=qualquer coisa vai ativar o retorno com mais informações e print de debug

import time
from flask import Flask, jsonify, request
from multiprocessing import Process, Value, Queue
import os
import json
from datetime import datetime, timedelta

import sys
sys.path.insert(1, '../pesquisabr')
from pesquisabr import PesquisaBR, RegrasPesquisaBR

app = Flask(__name__)

ARQ_CONFIG = './config.json'
ARQ_REGRAS = './regras.json'   # arquivo texto no formato [{regra}, {regra}, {regra}]
CONFIG = {}
REGRAS = []
dthr_regras = None

def carregar_config():
    global CONFIG
    _config = {}
    if os.path.isfile(ARQ_CONFIG):
       with open(ARQ_CONFIG,mode='r') as f:
           _config = f.read().replace('\n',' ').strip()
           if _config and _config[0]=='{' and _config[-1]=='}':
              _config = json.loads(_config)
    # correções do tempo de refresh das regras
    _config['tempo_regras'] = _config.get('tempo_regras',300)
    if (type(_config['tempo_regras']) != int) or (_config['tempo_regras']<5):
       _config['tempo_regras'] = 5
    # atualização da configuração
    CONFIG = _config

def carregar_regras():
    global REGRAS, dthr_regras
    # recarrega as regras a cada 5 minutos
    # é um exemplo pois poderia recarregar do banco de dados ou de algum microserviço
    if dthr_regras and (datetime.now()-dthr_regras).total_seconds()<300:
        return 
    dthr_regras = datetime.now()
    _regras = []
    if os.path.isfile(ARQ_REGRAS):
        with open(ARQ_REGRAS,mode='r') as f:
            _regras = f.read().strip()
            _regras = json.loads(_regras)
            _regras = _regras.get('regras')
            _regras = sorted(_regras, key=lambda k:k.get('grupo',''))    
        REGRAS = _regras 
    else:
        REGRAS = []
    print(f'Número de regras carregadas: {len(REGRAS)}')

def get_post(req:request):
    res = (
            dict(request.args)
            or request.form.to_dict()
            or request.get_json(force=True, silent=True)
            or {}
        )
    #print('Dados enviados: ', res)
    return res

@app.route('/health', methods=['GET'])
def get_health():
    _criterios = 'casas ADJ2 papeis PROX10 legal PROX10 seriado'
    _texto = 'a casa de papel é um seriado muito legal'
    pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
    if not pb.retorno():
       print('\n\n')
       print('=========================================================')
       print('=    ERRO NO CRITÉRIO DE PESQUISA DO HEALTH CHECK       =')
       pb.print_resumo() 
       print('=========================================================')
       print('\n\n')
       raise Exception(f'Health check - ERRO na avaliação do critério de pesquisa')
    print('\n===== HEALTH CHECK OK =====\n')
    return jsonify({'ok': True, 'criterios': pb.criterios, 'criterios_aon': pb.criterios_and_or_not, 'texto': pb.texto })


# recebe {'texto': 'texto para ser analisado pelas regras'}
# retorna {'retorno': true/false }
@app.route('/analisar_regras', methods=['GET','POST'])
def analisar_regras():
    carregar_regras()
    global REGRAS
    dados = get_post(request)
    _texto = str(dados.get("texto",""))
    _detalhar = str(dados.get("detalhar","")) not in ("","0","False")
    _criterios = 'teste PROX10 legal'
    pbr = RegrasPesquisaBR(regras=[], print_debug=False)
    pbr.regras = REGRAS # não reprocessa a ordenação, só para diminuir o processamento
    res = pbr.aplicar_regras(texto=_texto, detalhar=_detalhar)
    if _detalhar:
        # o retorno detalhado é (texto processado, rotulos, extrações)
        return jsonify({'rotulos': res[1], 'texto': res[0], 'extracoes': res[2], 'regras': res[3] })
    return jsonify({'rotulos': res[1], 'extracoes': res[2] })

# recebe {'texto': 'texto para ser analisado pelas regras', 'criterio':'critérios de pesquisa'}
# retorna {'retorno': true/false }
@app.route('/analisar_criterio', methods=['GET','POST'])
def analisar_criterio():
    dados = get_post(request)
    _texto = str(dados.get("texto",""))
    _criterios = str(dados.get("criterio",""))
    _detalhar = str(dados.get("detalhar","")) not in ("","0","False")
    if not _criterios:
       _criterios = str(dados.get("criterios",""))
    #print('Texto: ', type(_texto),_texto)
    #print('Critério: ', type(_criterios),_criterios)
    pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
    if _detalhar:
       return jsonify({'retorno': pb.retorno(), 
                       'criterios': pb.criterios, 
                       'criterios_aon': pb.criterios_and_or_not, 
                       'texto': ' '.join(pb.tokens_texto) })
    return jsonify({'retorno': pb.retorno()})


if __name__ == "__main__":
    # carrega as configurações
    carregar_config()
    # carrega as regras
    carregar_regras()

    print('#########################################')
    print('Iniciando o serviço')
    print('Configuações: ', json.dumps(CONFIG))
    print('-----------------------------------------')
    app.run(host='0.0.0.0', debug=True,port=8000) 

