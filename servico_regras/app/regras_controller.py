from copy import deepcopy
from datetime import date, datetime
import os
import json

###################################################################
from regras_util import regex_valido, regra_valida, regras_contem_tags, regras_regex_tags

###################################################################
# configurações do ambiente
from app_config import obj_regras_model, CONFIG

###################################################################
# carrega as configurações e preparando o cache de carga das regras
# configuração do cache de regras - 5 minutos
from cachetools import cached, LFUCache
from threading import RLock
CACHE_REGRAS_FILTRADAS = LFUCache(maxsize=10000)
lock = RLock()    

###################################################################
# exemplos
ARQ_EXEMPLOS = './exemplos.json'
EXEMPLOS_CARREGADOS = False
EXEMPLOS = []

###################################################################
# retorna apenas as regras contenham alguma das tags informadas
# caso receba regras_externas, usa as regras enviadas
# tags_lista é uma lista de tags do tipo "tag1 tag2 tag3"
# com isso, se tiver uma das tags já é aceito no filtro
# o cache evita refazer diversos filtros repetidamente
# cabecalho e rodapé serve para recortar o texto e analisar apenas o início, fim ou início e fim dele
# chaves_filtros é tupla para virar chave por conta do cache não aceitar dict
@cached(CACHE_REGRAS_FILTRADAS, lock=lock)
def regras_filtradas_cache(tags_desejadas = None, chaves_filtros = None, id_cache = ''):
    return regras_filtradas(tags_desejadas=tags_desejadas, chaves_filtros=chaves_filtros)

def regras_filtradas(tags_desejadas = None, chaves_filtros = None, regras_externas = None):
    if type(regras_externas) is list:
        _regras_analise, _ = obj_regras_model.corrigir_validar_regras(regras_externas, True)
    else:
        _regras_analise =  obj_regras_model.get_regras_carregadas_db()
    #print('Regras externas rf: ', regras_externas)
    #print('Regras análise: ', _regras_analise)
    if (not tags_desejadas) and (chaves_filtros is None):
        #print(f'>>> Regras não filtradas: {len(_regras_analise)}')
        return _regras_analise
    res = []
    re_tags_desejadas = regras_regex_tags(tags_desejadas)
    chaves_filtros = {} if chaves_filtros is None else {c:str(v) for c,v in chaves_filtros if v}
    #print('Filtros tags: ', tags_desejadas, re_tags_desejadas)
    #print('Filtros: ', chaves_filtros)
    for regra in _regras_analise:
        # verifica se todas as chaves são verdadeiras e existe pelo menos uma tag desejada
        chaves_ok = re_tags_desejadas is None or regras_contem_tags(re_tags_desejadas, regra.get('tags',''))
        if chaves_ok:
            # caso a regra tenha alguma chave com tags_ ou tags- e esteja preenchida, é necessário garantir esse filtro
            # pelo menos uma tag informada no filtro deve coincidir com uma tag informada na regra
            chaves_tags = [_ for _ in regra.keys() if _.lower()[:5] in ('tags_', 'tags-') and regra[_]]
            # verifica cada filtro se foi atendido
            for chave, valor in chaves_filtros.items():
                if chave in chaves_tags:
                   _re_tags_filtro = regras_regex_tags(valor) # regex com as tags desejadas no filtro
                   #print(f'chave com tags: [{valor}] => [{regra[chave]}] ', _re_tags_filtro, '?')
                   if regras_contem_tags(_re_tags_filtro, regra[chave]):
                       #print('chave com tags: ', valor , ' => ', regra[chave], ' o/')
                       chaves_tags.pop(chaves_tags.index(chave)) # está ok
                   else:
                       chaves_ok = False 
                       break
                elif chave.lower()[:5] in ('tags_', 'tags-'):
                    # foi passado um filtro de tag mas a regra não filtra tags, então está ok
                    continue
                elif str(regra.get(chave)) != valor:
                    chaves_ok = False
                    break
        # não pode ter sobrado uma chave com tag sem verificação, 
        # significa que o filtro veio vazio para ela
        if chaves_ok and not any(chaves_tags):
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
    global EXEMPLOS, EXEMPLOS_CARREGADOS
    if not EXEMPLOS_CARREGADOS:
        carregar_exemplos()
        EXEMPLOS_CARREGADOS = True
    if i:
        return EXEMPLOS[i] if i < len(EXEMPLOS) else None
    return EXEMPLOS

def limpar_cache_regras():
    obj_regras_model.limpar_cache_regras_db()
    msg = f'{get_msg_resumo_regras()}'
    carregar_exemplos()
    print(f'(* {msg} *)')
    return msg

def get_regras_carregadas():
    return obj_regras_model.get_regras_carregadas_db()    

def get_msg_resumo_regras():
    return f'{len(obj_regras_model.get_regras_carregadas_db())} regras recarregadas e {len(obj_regras_model.get_regras_erro_db())} ignoradas por erro de construção - carga das regras: {CONFIG.data_carga_regras} - controle do cache: {obj_regras_model.get_controle_cache_db()}'

def get_regras_erros():
    # conversão erros vai traduzir os códigos de erros para uma forma fácil de ser identificada pelo negócio
    # por exemplo um seq virar um título da regra
    erros = obj_regras_model.get_regras_erro_visual()
    for e in erros:
        if e.get('regra','')[:2].lower() == 'r:':
           e['erro'] = regex_valido(e.get('regra','')[2:], '', True)
        else:
           e['erro'] = regra_valida(e.get('regra',''), '', True)
    return erros

def get_logs_regras_visual():
    return obj_regras_model.get_logs_regras_visual()

# realiza conversões específicas dos dados de entrada recebidos para as regras logo após o recebimento do get/post
def conversao_get_post_regras(dados):
    if obj_regras_model:
        obj_regras_model.conversao_get_post_regras(dados)

def get_controle_cache():
    return obj_regras_model.get_controle_cache_db()        
