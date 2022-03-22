# -*- coding: utf-8 -*-

# configuração de caminho para o componente
from regras_util import regras_corrigir_tags, regra_valida, regex_valido
from pesquisabr import RegrasPesquisaBR

ERRO_NO_CACHE = False # apenas para testes

# configuração do cache de regras do banco - 5 minutos 
from cachetools import cached, TTLCache
from threading import RLock
from app_config import TEMPO_CACHE_SEGUNDOS
CACHE_FILTRO_REGRAS = TTLCache(maxsize=2000, ttl=TEMPO_CACHE_SEGUNDOS)
LOCK_FILTRO_REGRAS = RLock()

class RegrasModelBase():
    # sobrescrever esse método para retornar uma lista de regras 
    # pode carregar do banco, do disco, de outro serviço, etc
    # [{"grupo" : "nome_grupo", "rotulo": "rotulo1", "regra": "critérios da regra", "tags": "receita bolo", "qtd_cabecalho":0, "qtd_rodape":0, "ordem": 0},]
    # incluir algum filtro com a chave filtro_tipo facilita testes na tela exemplo do serviço
    def get_regras_db(self):
        return []

    # pode-se transforar os dados de saída do serviço com base em alguma
    # regra específica do contexto da aplicação
    # pode-se tratar a chave regras com as regras aplicadas, a chave rótulos, etc
    def conversao_retorno(self, retorno: dict):
        pass 

    def __init__(self):
        self.REGRAS_ERRO = []
        self.REGRAS_CARREGADAS = []

    def limpar_cache_db(self):
        #global CACHE_FILTRO_REGRAS
        CACHE_FILTRO_REGRAS.clear()

    @cached(CACHE_FILTRO_REGRAS, lock=LOCK_FILTRO_REGRAS)
    def carregar_regras_db(self):
        print('Carregando regras')
        _regras = self.get_regras_db()
        _regras_ok = []
        _regras_erro = []
        for r in _regras:
            r['qtd_cabecalho'] = r.get('qtd_cabecalho', 0)
            r['qtd_rodape'] = r.get('qtd_rodape', 0)
            r['grupo'] = str(r.get('grupo','-'))
            r['tags'] = regras_corrigir_tags(r.get('tags',''))
            # para permitir ordenação
            r['ordem'] = int(r.get('num_ordem')) if type(r.get('num_ordem')) is int or str(r.get('num_ordem')).isdigit() else 0
            if 'filtro_tipo' in r:
                r['filtro_tipo'] = str(r.get('filtro_tipo',''))
            # se a regra for um regex, valida ele 
            # print('Verificando: ', r.get('regra'), f'{r.get("seq_regra")} - {r.get("desc_regra")}')
            if r.get('regra','')[:2].upper() == 'R:':
                if regex_valido(r.get('regra'), f'{r.get("grupo")} - {r.get("rotulo")}'):
                    _regras_ok.append(r)
                else:
                    _regras_erro.append(r)
            else:
                if regra_valida(r.get('regra'), f'{r.get("grupo")} - {r.get("rotulo")}'):
                    _regras_ok.append(r)
                else:
                    _regras_erro.append(r)
        self.REGRAS_CARREGADAS = RegrasPesquisaBR.ordenar_regras(_regras_ok)
        self.REGRAS_ERRO = _regras_erro
        print(f'Número de regras carregadas: {len(self.REGRAS_CARREGADAS)}')
        if any(self.REGRAS_ERRO):
            print(f' * número de regras ignoradas por erro: {len(self.REGRAS_ERRO)}')

    def get_regras_erro_db(self):
        self.carregar_regras_db()
        return self.REGRAS_ERRO

    def get_regras_carregadas_db(self):
        self.carregar_regras_db()
        return self.REGRAS_CARREGADAS    

### carregamento de regras pelo arquivo
import json
import os
class RegrasModelArquivo(RegrasModelBase):
    ARQ_REGRAS = './regras.json'   # arquivo texto no formato [{regra}, {regra}, {regra}]
    def get_regras_db(self):
        regras = []
        if os.path.isfile(self.ARQ_REGRAS):
            with open(self.ARQ_REGRAS,mode='r') as f:
                regras = f.read()
            regras = json.loads(regras.strip()) 
        regras = regras.get('regras',[])
        return RegrasPesquisaBR.ordenar_regras(regras)

    # converte os dados retornados pelo controller 
    def conversao_retorno(self, retorno: dict):
        return
        # exemplo para injetar uma chave com os grupos retornados
        # poderia buscar outros dados no BD, em outro serviço, transformar dados, etc
        if 'regras' in retorno:
           regras = retorno['regras']
           grupos = []
           for r in regras:
               if r.get('grupo') and r.get('grupo') not in grupos:
                  grupos.append(r.get('grupo'))
           retorno['grupos'] = grupos
