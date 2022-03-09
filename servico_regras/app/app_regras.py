# -*- coding: utf-8 -*-
# teste para aplicação de regras
# http://localhost:8000/analisar_regras?texto=esse%20texto%20tem%20uma%20receita%20de%20pao%20e%20de%20bolo%20legal&criterio=texto&debug=0
# teste para análise de critérios
# http://localhost:8000/analisar_criterio?texto=esse%20texto%20legal&criterio=texto&debug=1

from flask import Flask, jsonify, request, render_template
from flask import render_template_string, redirect, url_for, Markup

from flask_bootstrap import Bootstrap
from jinja2 import TemplateNotFound

import os
import json
from app_config import CONFIG, TEMPO_CACHE_SEGUNDOS

###################################################################
# controller
from regras_controller import carregar_exemplos, get_exemplo, limpar_cache_regras
from regras_controller_aplicar import analisar_criterios, get_dados_health, analisar_regras, analisar_criterio_remover_trechos

EM_DEBUG = os.path.isfile('debug.txt')

app = Flask(__name__, template_folder='./templates')
bootstrap  = Bootstrap(app)

#PATH_API = '/api/ia-regras/'
PATH_API = '/'

###################################################################
# converte request ou dados para dict 
def get_post(req:request):
    res = (
            dict(req.args)
            or req.form.to_dict()
            or req.get_json(force=True, silent=True)
            or {}
        )
    #print('Dados enviados: ', res)
    return res

###################################################################
# limpeza do cache
@app.route(f'{PATH_API}cache', methods=['GET'])
def limpar_cache():
    msg = limpar_cache_regras()
    return jsonify({'ok': True, 'msg': msg, 'erro':False})

@app.route(f'{PATH_API}health', methods=['GET'])
@app.route('/health', methods=['GET'])
def get_health():
    return jsonify(get_dados_health())

###################################################################
# recebe {'texto': 'texto para ser analisado pelas regras'}
# retorna {'retorno': true/false }
# pode receber seq_regra, seq_grupo_regra ou seq_alvo para filtrar
@app.route(f'{PATH_API}analisar_regras', methods=['GET','POST'])
def srv_analisar_regras():
    dados = get_post(request)
    retorno = analisar_regras(dados)
    retorno.pop('texto_analise', None)
    return jsonify( retorno )

###################################################################
# recebe {'texto': 'texto para ser analisado pelas regras', 'criterio':'critérios de pesquisa'}
# retorna {'retorno': true/false }
@app.route(f'{PATH_API}analisar_criterio', methods=['GET','POST'])
def srv_analisar_criterio():
    dados = get_post(request)
    retorno = analisar_criterios(dados)
    return jsonify(retorno)

#############################################################################
#############################################################################
## formulários de teste das regras

@app.route(f'{PATH_API}testar_regras',methods=['GET','POST'])
def testar_regras():
    try:
        title = "PesquisaBR: Análise de regras"
        dados = get_post(request)
        dados['primeiro_do_grupo'] = 'primeiro_do_grupo' in dados
        dados['detalhar'] = True
        # recebe um filtro da tela para filtrar as regras, remove o filtro se não for preenchido
        dados['filtro_tipo'] = dados.get('filtro_tipo','').strip()
        if not dados['filtro_tipo']:
           dados.pop('filtro_tipo', None)
        retorno = analisar_regras(dados)
        # retorna apenas as descrições dos rótulos
        rotulos_retornados = [r.get('rotulo','-') for r in retorno.get('regras', [])]

        return render_template("aplicar_regras.html", 
                texto = str(retorno.get('texto_analise','')),
                texto_processado = str(retorno.get('texto','')),
                rotulos_retornados = rotulos_retornados,
                qtd_regras = retorno.get('qtd_regras', 0),
                tempo = f"{retorno.get('tempo', 0):.3f} s",
                tags = str(dados.get("tags","")),
                primeiro_do_grupo = dados['primeiro_do_grupo'],
                primeiro_do_grupo_ck = 'CHECKED' if dados['primeiro_do_grupo'] else '',
                ativo_regras='active',
                title=title,
                filtro_tipo=dados.get('filtro_tipo',''),
                exemplos_regras = get_exemplo())
    except TemplateNotFound as e:
        return render_template_string(f'Página não encontrada: {e.message}')

#############################################################################
#############################################################################
## formulários de teste de critérios
@app.route('/')
@app.route('/teste')
@app.route(f'{PATH_API}')
@app.route(f'{PATH_API}teste')
def testar():
    return redirect(url_for('testar_criterios'))
##
@app.route(f'{PATH_API}testar_criterios',methods=['GET','POST'])
def testar_criterios():
    try:
        title = "PesquisaBR: Análise de criterios"
        dados = get_post(request)
        dados['detalhar'] = True
        dados['grifar'] = True
        dados['extrair'] = True
        retorno = analisar_criterios(dados)
        exemplos_com_criterios = [_ for _ in get_exemplo() if _.get('criterios')]
        contem_trechos_extraidos = any(retorno.get('extracoes', []))
        trechos_extraidos = [json.dumps(_) for _ in retorno.get('extracoes', [])]
        trechos_extraidos = '<br>'.join(trechos_extraidos)
        
        return render_template("aplicar_criterio.html",
                texto = str(retorno.get('texto_analise','')),
                criterios = str(retorno.get('criterios_analise','')),
                criterios_ok = retorno.get('retorno'),
                texto_processado = str(retorno.get('texto','')),
                criterios_processados = str(retorno.get('criterios','')),
                tempo = f"{retorno.get('tempo', 0):.3f} s",
                ativo_criterios='active',
                erros = str(retorno.get('erros','')),
                title=title,
                texto_grifado= Markup(str(retorno.get('texto_grifado',''))),
                exemplos_criterios = exemplos_com_criterios,
                trechos_extraidos = Markup(trechos_extraidos),
                contem_trechos_extraidos = contem_trechos_extraidos
        )
    except TemplateNotFound as e:
        return render_template_string(f'Página não encontrada: {e.message}')

#############################################################################
#############################################################################
# exemplos de uso do serviço
@app.route(f'{PATH_API}exemplos',methods=['GET'])
def exemplos():
    return render_template("exemplos_servico.html", 
                title = "PesquisaBR: Exemplos de uso do serviço",
                ativo_exemplos='active')

#############################################################################
#############################################################################

if __name__ == "__main__":
    # carrega as regras
    carregar_exemplos()
    print( '#########################################')
    print( 'Iniciando o serviço')
    print( 'Configuações: ', json.dumps(CONFIG))
    print(f' - tempo de cache: {TEMPO_CACHE_SEGUNDOS}s')
    print( '-----------------------------------------')
    app.run(host='0.0.0.0', debug=EM_DEBUG,port=8000) 

