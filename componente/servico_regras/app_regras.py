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
import re 

# configuração de caminho para o componente
from pesquisabr.pesquisabr import PesquisaBR, RegrasPesquisaBR

app = Flask(__name__)

ARQ_CONFIG = './config.json'
ARQ_REGRAS = './regras.json'   # arquivo texto no formato [{regra}, {regra}, {regra}]
CONFIG = {}
REGRAS = []
dthr_regras = None

# configuração do cache de regras - 5 minutos 
from cachetools import cached, TTLCache
from threading import RLock
cache_filtros_regras = TTLCache(maxsize=2000, ttl=5 * 60) 
lock = RLock()

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

REGEX_CORRIGE_TAGS = re.compile(r'[,;#\s]+')
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
            _regras = f.read()
        _regras = json.loads(_regras.strip())
        _regras = _regras.get('regras')
        _regras = sorted(_regras, key=lambda k:k.get('grupo',''))    
        # corrige as tags das regras usando espaço como separador (para o regex achar um dos termos do filtro)
        _regras_tags = []
        for r in _regras:
            r['tags'] = ' '+REGEX_CORRIGE_TAGS.sub(' ', r.get('tags','')) + ' '
            r['qtd_cabecalho'] = r.get('qtd_cabecalho',0)
            r['qtd_rodape'] = r.get('qtd_rodape',0)
            # se a regra for um regex, valida ele 
            if regex_valido(r.get('regra'), r.get('rotulo')) and regex_valido('r:'+r.get('extracao',''), r.get('rotulo')):
               _regras_tags.append(r)
        REGRAS = _regras_tags
    else:
        REGRAS = []
    print(f'Número de regras carregadas: {len(REGRAS)}')

# retorna true para regex válido em regras ou extrações
def regex_valido(txt_regex, rotulo):
    if (not txt_regex) or (txt_regex[:2] not in {'r:','R:'}):
        return True
    try:
        re.compile(str(txt_regex))
        print(f'REGEX OK: rótulo "{rotulo}" com o texto de regex: {txt_regex}')
        return True
    except re.error:
        pass 
    print(f'REGEX inválido: rótulo "{rotulo}" com o texto de regex: {txt_regex}')
    return False

# retorna apenas as regras de um grupo específico e/ou que contém alguma das tags informadas
# tags_lista é uma lista de tags do tipo "tag1 tag2 tag3"
# com isso, se tiver uma das tags já é aceito no filtro
# o cache evita refazer diversos filtros repetidamente
# cabecalho e rodapé serve para recortar o texto e analisar apenas o início, fim ou início e fim dele
@cached(cache_filtros_regras, lock=lock)
def regras_filtradas(tags_lista = None, grupo = None):
    carregar_regras()
    global REGRAS
    if (not grupo) and (not tags_lista):
        #print(f'>>> Regras não filtradas: {len(REGRAS)}')
        return REGRAS
    tags_lista = '' if not tags_lista else '( ' + REGEX_CORRIGE_TAGS.sub(' ', str(tags_lista)).strip().replace(' ',' )|( ') + ' )'
    re_tags_lista = re.compile(tags_lista)
    res = []
    for r in REGRAS:
        if grupo and str(grupo) != str(r.get('grupo','')):
            continue
        if tags_lista and not re_tags_lista.search(r.get('tags','')):
            continue
        res.append(r)
    #print(f'>>> Regras filtradas: {len(res)}/{len(REGRAS)} >> [{tags_lista}]')
    return res

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
    _tags = str(dados.get("tags",""))
    _grupo = str(dados.get("grupo",""))
    pbr = RegrasPesquisaBR(regras=[], print_debug=False)
    # não envia como parâmetro para o construtor para não reprocessar a ordenação, só para diminuir o processamento
    # filtra as regras com uma das tags e/ou com o grupo informado
    pbr.regras = regras_filtradas(tags_lista=_tags, grupo=_grupo) 
    res = pbr.aplicar_regras(texto=_texto, detalhar=_detalhar)
    return jsonify(res)

# recebe {'texto': 'texto para ser analisado pelas regras', 'criterio':'critérios de pesquisa'}
# retorna {'retorno': true/false }
@app.route('/analisar_criterio', methods=['GET','POST'])
def analisar_criterio():
    dados = get_post(request)
    _texto = dados.get("texto","")
    _texto = _texto if type(_texto) is dict else str(_texto)
    _criterios = str(dados.get("criterio",""))
    _detalhar = str(dados.get("detalhar","")) not in ("","0","False")
    if not _criterios:
       _criterios = str(dados.get("criterios",""))
    pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
    if _detalhar:
        if type(pb.tokens_texto) is dict:
            _texto_processado = {k: ' '.join(v) for k, v in pb.tokens_texto.items()}
        else:
            _texto_processado = ' '.join(pb.tokens_texto)
        return jsonify({'retorno': pb.retorno(), 
                        'criterios': pb.criterios, 
                        'criterios_aon': pb.criterios_and_or_not, 
                        'texto': _texto_processado })
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

