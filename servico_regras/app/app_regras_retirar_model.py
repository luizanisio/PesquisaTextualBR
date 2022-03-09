# -*- coding: utf-8 -*-
# teste para aplicação de regras
# http://localhost:8000/analisar_regras?texto=esse%20texto%20tem%20uma%20receita%20de%20pao%20e%20de%20bolo%20legal&criterio=texto&debug=0
# teste para análise de critérios
# http://localhost:8000/analisar_criterio?texto=esse%20texto%20legal&criterio=texto&debug=1

from flask import Flask, jsonify, request, render_template, render_template_string, redirect, Markup

from flask_bootstrap import Bootstrap
from jinja2 import TemplateNotFound

import os
import json
from datetime import datetime
import re 

# configuração de caminho para o componente
from pesquisabr import PesquisaBR, RegrasPesquisaBR

app = Flask(__name__, template_folder='./templates')
bootstrap  = Bootstrap(app)

ARQ_CONFIG = './config.json'
ARQ_REGRAS = './regras.json'   # arquivo texto no formato [{regra}, {regra}, {regra}]
ARQ_EXEMPLOS = './exemplos.json'
CONFIG = {}
REGRAS = []
REGRAS_ERROS = 0
EXEMPLOS = []
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

def carregar_exemplos():
    global EXEMPLOS
    _exemplos = []
    if os.path.isfile(ARQ_EXEMPLOS):
       with open(ARQ_EXEMPLOS,mode='r') as f:
           _exemplos = f.read().replace('\n',' ').strip()
           if _exemplos and _exemplos[0]=='{' and _exemplos[-1]=='}':
              _exemplos = json.loads(_exemplos)
              _exemplos = _exemplos.get('exemplos',[])
    # atualização dos exemplos
    EXEMPLOS = []
    for i, _ in enumerate(_exemplos):
        if _.get('texto') or _.get('criterios'):
            _['rotulo'] = _.get('texto')[:15] + '...'
            _['n'] = i
            EXEMPLOS.append(_)

    

###################################################################
# carrega as configurações e preparando o cache de carga das regras
carregar_config()
# configuração do cache de regras - 5 minutos 
from cachetools import cached, TTLCache
from threading import RLock
ttl_cache = CONFIG.get('tempo_regras',0)
ttl_cache = 5* 60 if ttl_cache < 1 else ttl_cache
print(f'Tempo de cache das regras: {ttl_cache}s')
cache_filtros_regras = TTLCache(maxsize=2000, ttl=ttl_cache) 
lock = RLock()


REGEX_CORRIGE_TAGS = re.compile(r'[,;#\s]+')
def carregar_regras():
    global REGRAS, dthr_regras, REGRAS_ERROS
    # recarrega as regras a cada 5 minutos
    # é um exemplo pois poderia recarregar do banco de dados ou de algum microserviço
    if dthr_regras and (datetime.now()-dthr_regras).total_seconds()<300:
        return 
    dthr_regras = datetime.now()
    _regras = []
    invalidas = 0
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
            if regex_valido(r.get('regra'), r.get('rotulo')) \
                and regex_valido('r:'+r.get('extracao',''), r.get('rotulo')) \
                and regra_valida(r.get('regra'), r.get('rotulo')):
               _regras_tags.append(r)
            else:
                invalidas += 1
        REGRAS = _regras_tags
        REGRAS_ERROS = invalidas
    else:
        REGRAS = []
        REGRAS_ERROS = 0
    print(f'Número de regras carregadas: {len(REGRAS)}')
    if invalidas>0:
        print(f' * número de regras ignoradas por erro: {invalidas}')


# retorna true para regex válido em regras ou extrações
def regex_valido(txt_regex, rotulo):
    if (not txt_regex) or (txt_regex[:2] not in {'r:','R:'}):
        return True
    try:
        re.compile(str(txt_regex))
        print(f'REGEX OK: rótulo "{rotulo}" - regex: {txt_regex}')
        return True
    except re.error:
        pass 
    print(f'**ERRO: REGEX inválido: "{rotulo}"')
    print(f'        texto de regex: {txt_regex}')
    return False

# verifica se a regra é válida e ignora ela caso tenha algum erro na construção
def regra_valida(txt_regra, rotulo):
    if (not txt_regra) or (txt_regra[:2] in {'r:','R:'}):
        return True
    pb = PesquisaBR(texto='', criterios=txt_regra)
    if pb.erros:
        print(f'**ERRO: REGRA inválida: "{rotulo}"')
        print(f'        texto de regra: {txt_regra}')
        print(f'                 erro : {pb.erros}')
        return False
    print(f'REGRA OK: rótulo "{rotulo}" com o texto de regra: {txt_regra}')
    return True

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

@app.route('/cache', methods=['GET'])
def limpar_cache():
    cache_filtros_regras.clear()
    print('Limpando cache de regras')
    carregar_regras()
    global REGRAS, REGRAS_ERROS
    return jsonify({'ok': True, 'msg': f'cache das regras reiniciado, {len(REGRAS)} regras recarregadas e {REGRAS_ERROS} ignoradas por erro de construção.'})


@app.route('/health', methods=['GET'])
def get_health():
    global REGRAS
    _criterios = 'casas ADJ2 papeis PROX10 legal PROX10 seriado'
    _texto = 'a casa de papel é um seriado muito legal'
    pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
    if (pb.erros) or (not pb.retorno()):
       print('\n\n')
       print('=========================================================')
       print('=    ERRO NO CRITÉRIO DE PESQUISA DO HEALTH CHECK       =')
       pb.print_resumo() 
       print('=========================================================')
       print('\n\n')
       raise Exception(f'Health check - ERRO na avaliação do critério de pesquisa')
    print(f'\n===== HEALTH CHECK OK ({len(REGRAS)} regras carregadas) =====\n')
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
    _extrair = str(dados.get("extrair","")) not in ("","0","False")
    _tags = str(dados.get("tags",""))
    _grupo = str(dados.get("grupo",""))
    pbr = RegrasPesquisaBR(regras=[], print_debug=False)
    # não envia como parâmetro para o construtor para não reprocessar a ordenação, só para diminuir o processamento
    # filtra as regras com uma das tags e/ou com o grupo informado
    pbr.regras = regras_filtradas(tags_lista=_tags, grupo=_grupo) 
    res = pbr.aplicar_regras(texto=_texto, detalhar=_detalhar, extrair=_extrair)
    return jsonify(res)

# recebe {'texto': 'texto para ser analisado pelas regras', 'criterio':'critérios de pesquisa'}
# retorna {'retorno': true/false }
@app.route('/analisar_criterio', methods=['GET','POST'])
def analisar_criterio():
    dados = get_post(request)
    _texto = dados.get("texto","")
    _texto = _texto if type(_texto) is dict else str(_texto)
    _criterios = str(dados.get("criterio","")) or str(dados.get("criterios",""))
    _detalhar = str(dados.get("detalhar","")) not in ("","0","False")
    _grifar = str(dados.get("grifar","")) not in ("","0","False")
    _extrair = str(dados.get("extrair","1")) not in ("","0","False")
    retorno = RegrasPesquisaBR.aplicar_criterios(texto = _texto, criterios= _criterios, extrair= _extrair, detalhar= _detalhar, grifar= _grifar)
    return jsonify(retorno)

#############################################################################
#############################################################################
## formulários de teste das regras e critérios
@app.route('/testar_regras',methods=['GET','POST'])
def testar_regras():
    try:
        title = "PesquisaBR: Análise de regras"
        dados = get_post(request)
        #print(dados)
        texto_analise = str(dados.get("texto_analise",""))
        texto_processado = ''
        carregar_exemplo = int(dados.get("exemplo",-1))
        if carregar_exemplo>=0 and len(EXEMPLOS)> carregar_exemplo:
            exemplo = EXEMPLOS[carregar_exemplo]
            texto_analise = exemplo['texto'] if exemplo.get('texto') else texto_analise
        rotulos_retornados = ''
        tags = str(dados.get("tags",""))
        grupo = str(dados.get("grupo",""))
        qtd_regras = 0
        _tempo = ''
        rotulos_retornados = []
        if texto_analise:
            carregar_regras()
            global REGRAS
            pb = PesquisaBR(texto=texto_analise)
            texto_processado = ' '.join(pb.tokens_texto)
            _ini = datetime.now()
            pbr = RegrasPesquisaBR(regras=[], print_debug=False)
            pbr.regras = regras_filtradas(tags_lista=tags, grupo=grupo) 
            qtd_regras = len(pbr.regras)
            res = pbr.aplicar_regras(texto=texto_analise, detalhar=True)
            _tempo = round((datetime.now()-_ini).total_seconds(),3)
            _tempo = f'{_tempo:.3f} s'
            rotulos_retornados = list(res.get('rotulos',[]))
            #print('Texto análise: ', texto_analise)
            #print('Regras: ')
            #[print(_) for _ in pbr.regras]

        return render_template("aplicar_regras.html", 
                texto_analise = texto_analise, 
                texto_processado = texto_processado,
                rotulos_retornados = rotulos_retornados,
                qtd_regras = qtd_regras,
                tempo = _tempo,
                grupo = grupo,
                tags = tags,
                ativo_regras='active',
                title=title,
                exemplos_regras = EXEMPLOS)
    except TemplateNotFound as e:
        return render_template_string(f'Página não encontrada: {e.message}')

@app.route('/')
@app.route('/testar')
@app.route('/testes')
@app.route('/teste')
@app.route('/testar_criterios',methods=['GET','POST'])
def testar_criterios():
    try:
        global EXEMPLOS
        title = "PesquisaBR: Análise de criterios"
        dados = get_post(request)
        texto_analise = str(dados.get("texto_analise",""))
        texto_criterio = str(dados.get("texto_criterio",""))
        carregar_exemplo = int(dados.get("exemplo",-1))
        if carregar_exemplo>=0 and len(EXEMPLOS)> carregar_exemplo:
            exemplo = EXEMPLOS[carregar_exemplo]
            texto_analise = exemplo['texto'] if exemplo.get('texto') else texto_analise
            texto_criterio = exemplo['criterios'] if exemplo.get('criterios') else texto_criterio
        criterio_ok = ''
        texto_processado = ''
        texto_grifado = ''
        criterio_processado = ''
        _tempo = ''
        # verifica critérios de remoção
        rpbr = RegrasPesquisaBR()
        texto_r, criterios_r = rpbr.remover_texto_criterio(texto = texto_analise, criterios = texto_criterio )
        criterio_raw = texto_criterio
        texto_raw = texto_analise
        if texto_r:
            texto_analise, texto_criterio = texto_r, criterios_r
        # verifica os critérios no texto
        if texto_analise or texto_criterio:
            _ini = datetime.now()
            pb = PesquisaBR(texto=texto_analise, criterios=texto_criterio)
            if texto_analise:
                texto_processado = ' '.join(pb.tokens_texto)
            if texto_criterio:
               criterio_processado = pb.criterios
            if texto_analise and texto_criterio:
               criterio_ok = 'SIM' if pb.retorno() else 'NAO'
            texto_grifado = Markup(pb.grifar_criterios(texto=texto_analise))
            _tempo = round((datetime.now()-_ini).total_seconds(),3)
            _tempo = f'{_tempo:.3f} s'

        return render_template("aplicar_criterio.html", 
                texto_analise = texto_raw, 
                texto_criterio = criterio_raw, 
                criterio_ok = criterio_ok,
                texto_processado = texto_processado,
                texto_grifado = texto_grifado,
                criterio_processado = criterio_processado,
                tempo = _tempo,
                ativo_criterios='active',
                title=title,
                exemplos_criterios = EXEMPLOS)
    except TemplateNotFound as e:
        return render_template_string(f'Página não encontrada: {e.message}')

@app.route('/exemplos',methods=['GET'])
def exemplos():
    return render_template("exemplos_servico.html", 
                title = "PesquisaBR: Exemplos de uso do serviço",
                ativo_exemplos='active')

#############################################################################
#############################################################################

if __name__ == "__main__":
    # carrega as regras
    carregar_regras()
    carregar_exemplos()

    print( '#########################################')
    print( 'Iniciando o serviço')
    print( 'Configuações: ', json.dumps(CONFIG))
    print(f' - tempo de cache: {ttl_cache}s')
    print( '-----------------------------------------')
    app.run(host='0.0.0.0', debug=True,port=8000) 

