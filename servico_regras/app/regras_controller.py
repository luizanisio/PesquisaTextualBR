import os
import json
from datetime import datetime
import re

###################################################################
from regras_util import regras_contem_tags, regras_regex_tags

###################################################################
# configurações do ambiente
from app_config import TEMPO_CACHE_SEGUNDOS, obj_regras_model

###################################################################
# carrega as configurações e preparando o cache de carga das regras
# configuração do cache de regras - 5 minutos 
from cachetools import cached, TTLCache
from threading import RLock
print(f'Tempo de cache das regras: {TEMPO_CACHE_SEGUNDOS}s')
cache_filtros_regras = TTLCache(maxsize=2000, ttl=TEMPO_CACHE_SEGUNDOS) 
lock = RLock()    

###################################################################
# exemplos
ARQ_EXEMPLOS = './exemplos.json'
EXEMPLOS = []

###################################################################
# retorna apenas as regras contenham alguma das tags informadas
# tags_lista é uma lista de tags do tipo "tag1 tag2 tag3"
# com isso, se tiver uma das tags já é aceito no filtro
# o cache evita refazer diversos filtros repetidamente
# cabecalho e rodapé serve para recortar o texto e analisar apenas o início, fim ou início e fim dele
# chaves_filtros é tupla para virar chave por conta do cache não aceitar dict
@cached(cache_filtros_regras, lock=lock)
def regras_filtradas(tags_desejadas = None, chaves_filtros = None):
    if (not tags_desejadas) and (chaves_filtros is None):
        #print(f'>>> Regras não filtradas: {len(REGRAS_CARREGADAS)}')
        return obj_regras_model.get_regras_carregadas_db()
    res = []
    re_tags_desejadas = regras_regex_tags(tags_desejadas)
    chaves_filtros = {} if chaves_filtros is None else {c:str(v) for c,v in chaves_filtros if v}
    # print('Filtros tags: ', tags_desejadas, re_tags_desejadas)
    # print('Filtros: ', chaves_filtros)
    for regra in obj_regras_model.get_regras_carregadas_db():
        # verifica se todas as chaves são verdadeiras
        chaves_ok = re_tags_desejadas is None or regras_contem_tags(re_tags_desejadas, regra.get('tags',''))
        for chave, valor in chaves_filtros.items():
            if str(regra.get(chave)) != valor:
                chaves_ok = False
                break
        if chaves_ok:
            res.append(regra)
    #print(f'>>> Regras filtradas: {len(res)}/{len(get_regras_carregadas())} >> [{tags_desejadas}]')
    return res
    
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
    print('Exemplos carregados: ', len(EXEMPLOS))

# retorna o exemplo i ou todos se i for None
def get_exemplo(i = None):
    global EXEMPLOS
    if i:
        return EXEMPLOS[i] if i < len(EXEMPLOS) else None
    return EXEMPLOS

def limpar_cache_regras():
    cache_filtros_regras.clear()
    obj_regras_model.limpar_cache_db()
    carregar_exemplos()
    print('Cache de regras reiniciado')
    return f'cache das regras reiniciado: {get_msg_resumo_regras()}.'

def get_regras_carregadas():
    return obj_regras_model.get_regras_carregadas_db()    

def get_msg_resumo_regras():
    return f'{len(obj_regras_model.get_regras_carregadas_db())} regras recarregadas e {len(obj_regras_model.get_regras_erro_db())} ignoradas por erro de construção'
