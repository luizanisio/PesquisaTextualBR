import os
import json
ARQ_CONFIG = './config.json'
CONFIG = {}
TEMPO_CACHE_SEGUNDOS = 0

'''Usado na configuração da API'''
PATH_API = '/'
''' Usado nos testes '''
PATH_URL = 'http://localhost:8000'
PATH_URL_API = f'{PATH_URL}{PATH_API}'

import os 
from datetime import time, timedelta , datetime
from hashlib import sha1

class CONFIG:
    __EM_DEBUG__ = False 
    __EM_DEBUG_TM__ = None

    # último id_cache que controla o hash do cache utilizado na carga de regras e filtros de regras
    id_cache = '' # será guardado o id de controle de validade do cache
    # registrar a última carga de regras
    data_carga_regras = ''
    @classmethod
    def to_string(cls):
        return f'[ id_cache: {cls.id_cache}, data_carga_regras: {cls.data_carga_regras} ]'

    @classmethod
    def em_debug(cls):
        if (cls.__EM_DEBUG_TM__ == None) or ((datetime.now()-cls.__EM_DEBUG_TM__).total_seconds() > 60):
            cls.__EM_DEBUG__ = os.path.isfile('debug.txt')
            cls.__EM_DEBUG_TM__ = datetime.now()
            print(f'<< EM DEBUG TESTADO PID#{os.getpid()}: ', f'|controle {cls.__EM_DEBUG_TM__}|', f'|em debug {cls.__EM_DEBUG__}| >>')
        return cls.__EM_DEBUG__        

    @classmethod
    def sha1(cls, texto):
        return sha1(str(texto).encode('utf-8')).hexdigest()

    @classmethod
    def sha1_mini(cls, texto, salto = 4):
        return cls.sha1(texto)[::salto]

    @classmethod
    def print_log_debug(cls,funcionalidade='', msg = '', id_print =''):
        if not cls.em_debug():
            return 
        _txt_comp = ''
        _func = f'_{funcionalidade}_'.ljust(20,'_') if funcionalidade else ''
        if _func and id_print:
           _txt_comp = f'|{_func} - {id_print}|' 
        elif _func or id_print:
           _txt_comp = f'|{_func}{id_print}|' 
        _msg = f'<< DEBUG PID#{os.getpid()} - {datetime.now().strftime("%H:%M:%S")} {_txt_comp} {msg} >>'
        print(_msg)

###################################################################################
# configurando novos padrões prontos de regex
from pesquisabr import UtilExtracaoRe
#novos_prontos = {'OAB' : r'\b([a-z]{2}[\.\-,; ]?\d{2,7}|\d{2,7}[\.\-,; ]?[a-z]{2})\b'}
#UtilExtracaoRe.PRONTOS.update(novos_prontos)

###################################################################################
# define o tipo de objeto de regras que será carregado
# pode-se criar um tipo personalizado carregando do banco ou de onde for necessário
from regras_model import RegrasModelArquivo
obj_regras_model = RegrasModelArquivo()

###################################################################################
# dicionário do PesquisaBR
from pesquisabr import PesquisaBR
# para termos simples
# se eu pesquisar "alegre", é o mesmo que pesquisar (feliz ou sorridente)
PesquisaBR.SINONIMOS = {'alegre': ['feliz','sorridente']}
# para termos compostos
# se eu pesquisar entre aspas "instituto nacional de seguridade social", é o mesmo que pesquisar "inss"
# se eu pesquisar entre aspas "inss", é o mesmo que pesquisar entre aspas "instituto nacional de seguridade social"
PesquisaBR.TERMOS_EQUIVALENTES = {"inss" : ['instituto nacional de seguridade social','previdencia social oficial']}

