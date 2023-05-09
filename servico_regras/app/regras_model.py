# -*- coding: utf-8 -*-

# configuração de caminho para o componente
from regras_util import regras_corrigir_tags, regra_valida, regex_valido
from pesquisabr import RegrasPesquisaBR
import pathlib
from datetime import datetime

ERRO_NO_CACHE = False # apenas para testes

# configuração do cache de regras do banco - 30 minutos
from cachetools import cached, LFUCache, TTLCache
from threading import RLock
from app_config import CONFIG
CACHE_FILTRO_REGRAS = LFUCache(maxsize=20000)
LOCK_CACHE = RLock()

# cache para o get da data de controle - 5s evita muitas chamadas concorrentes ao disco ou ao banco se for db
# no caso de implementar um RegrasModelBase, usar o cache como no exemplo do RegrasModelBaseArquivo
CACHE_CONTROLE_CACHE = TTLCache(maxsize=5, ttl=5)
LOCK_CACHE = RLock()

from pesquisabr import UtilRegrasConfig
from pesquisabr import UtilExtracaoRe

class RegrasModelBase():

    #################################################################################
    # SOBRESCREVER OBRIGATORIALMENTE esse médodo na nova classe que herda de RegrasModelBase
    # ele deve retornar uma lista de regras carregadas de alguma fonte de dados
    # pode-se carregar do banco, do disco, de outro serviço, etc
    # [{"grupo" : "nome_grupo", "rotulo": "rotulo1", "regra": "critérios da regra", "tags": "receita bolo", "qtd_cabecalho":0, "qtd_rodape":0, "ordem": 0},]
    # incluir algum filtro com a chave filtro_tipo facilita testes na tela exemplo do serviço
    def get_regras_db(self):
        msg = f'### ATENÇÃO ### - {self.__class__.__name__} deve implementar "get_regras_db()"'
        print(msg)
        # essa parte é para não dar erros no editor
        if 1 == 1:
            raise Exception(msg)
        return []

    #################################################################################
    # SOBRESCREVER OPCIONALMENTE esse médodo na nova classe que herda de RegrasModelBase
    # pode-se transforar os dados de saída do serviço com base em alguma
    # regra específica do contexto da aplicação
    # pode-se tratar a chave regras com as regras aplicadas, a chave rótulos, etc
    def conversao_retorno(self, retorno: dict):
        # para manter a compatibilidade com os testes básicos do serviço
        # faz com que o retorno seja o RAW por conta dos casos de teste
        if 'rodando-testes' in retorno:
            print('Em teste - ignorando conversão de retorno')
            return
        # outras implementações
        pass

    # consolida dados de erros registrados ao longo das execuções de regras e regex
    # retorna para ser apresentado na tela do serviço
    # é esperado receber uma string formatada em html
    def get_logs_regras_visual(self):
        dados1 = UtilRegrasConfig.retornar_logs_consolidados(True)
        dados2 = UtilRegrasConfig.retornar_logs_consolidados(False)
        res = []
        def _insere_(r, d, tipo):
            if len(d) > 0:
               r += [f'<b>{tipo} ({len(d)}):</b><br>\n']
               r += ['<ul>\n']
               _d = [f'<li>{_}<br></li>\n' for _ in d]
               r += _d
               r += ['</ul><br><br>']
        _insere_(res, dados1, 'Erros de TimeOut')
        _insere_(res, dados2, 'Regras lentas')
        return '\n'.join(res)

    #################################################################################
    # SOBRESCREVER OPCIONALMENTE esse médodo na nova classe que herda de RegrasModelBase
    # pode-se transforar os dados de entrada no serviço com base em alguma
    # regra específica do contexto da aplicação
    # pode-se converter dados ou incluir outras regras de negócio específicas
    # front_end, analisar_regras, analisar_criterios indicam o contexto dos dados de entrada
    def conversao_entrada(self, dados: dict, front_end = False, analisar_regras=False, analisar_criterios=False):
        # em geral não vai precisar de tratamento para regras externas recebidas
        if 'regras_externas' in dados:
            return
        # pode ser usado para tratar os dados de entrada para compatibilidade com o serviço de exemplo
        pass 

    #################################################################################
    # SOBRESCREVER OPCIONALMENTE esse médodo na nova classe que herda de RegrasModelBase
    # parecido com o conversao_entrada, mas ocorre no momento do get/post do serviço na chamada de regras apenas
    # não ocorre na chamada da tela do próprio serviço
    # pode ser usado para controle como a limpeza automática do cache dependendo do tipo de requisição feita
    def conversao_get_post_regras(self, dados: dict):
        # em geral não vai precisar de tratamento para regras externas recebidas
        if 'regras_externas' in dados:
            return
        # pode ser usado para limpar o cache dependendo de uma chamada específica
        pass

    #################################################################################
    # SOBRESCREVER OPCIONALMENTE esse médodo na nova classe que herda de RegrasModelBase
    # pode-se transformar as regras da lista alterando as chaves grupo e rotulo para ficar uma apresentação mais intuitiva
    # será usado em self.conversao_erros e self.conversao_validas
    def conversao_visual(self, regras):
        return regras
        # exemplo de conversão:
        '''
        _regras = deepcopy(regras)
        for r in _regras:
            complemento = r.get("complemento") or r.get("observacao","-")
            grupo = r.get("desc_grupo_regra") or r.get("desc_grupo") or r.get("grupo","?")
            r['grupo'] = f'{grupo} ({complemento})'
            #print(str(r))
        return _regras
        '''

    #################################################################################
    # retorna a lista de regras com erro em um formato mais visual para apresentação
    # usa o conversor self.conversao_visual
    def get_regras_erro_visual(self):
        return self.conversao_visual(self.get_regras_erro_db())

    #################################################################################
    # retorna a lista de regras validadas em um formato mais visual para apresentação
    # usa o conversor self.conversao_visual
    def get_regras_carregadas_visual(self):
        return self.conversao_visual(self.get_regras_carregadas_db())

    #################################################################################
    # SOBRESCREVER OPCIONAMENTE esse médodo na nova classe que herda de RegrasModelBase
    # para o caso da implementação db usar cache também para a data de controle de validade do cache
    def limpar_cache_regras_db(self):
        # Exemplo: CACHE_CONTROLE_CACHE.clear()
        msg = f'### ATENÇÃO ### - {self.__class__.__name__} não implementou "limpar_cache_regras_db()"'
        print(msg)

    #################################################################################
    # NÃO ALTERAR ESSE MÉTODO
    def __init__(self):
        self.REGRAS_ERRO = []
        self.REGRAS_CARREGADAS = []

    #############################################################################
    # NÃO SOBRESCREVER ESSE MÉTODO, ele corrige e transforma dados recebidos
    # da implementação self.get_regras_db()
    @cached(CACHE_FILTRO_REGRAS, lock=LOCK_CACHE)
    def carregar_regras_db(self, id_cache):
        print(f'Carregando regras com id cache = {id_cache}')
        regras = self.get_regras_db()
        self.REGRAS_CARREGADAS,self.REGRAS_ERRO = self.corrigir_validar_regras(regras)
        CONFIG.data_carga_regras = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 

    #################################################################################
    # valida, ordena e separa as regras válidas das inválidas
    def corrigir_validar_regras(self, regras, externas = False):
        regras_ok, regras_erro = [], []
        for r in regras:
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
                _regex = r['regra'][2:]
                _regex_final = UtilExtracaoRe.preparar_regex_pronto(_regex)
                if _regex != _regex_final:
                   r['regra'] = f'r:{_regex_final}'
                   r['regra_original'] = f'r:{_regex}'
                   print(f'***** Regex transformado: \n >> {_regex}\n >> {_regex_final}') 
                if regex_valido(_regex_final, f'{r.get("grupo")} - {r.get("rotulo")}'):
                    regras_ok.append(r)
                else:
                    regras_erro.append(r)
            else:
                if regra_valida(r.get('regra'), f'{r.get("grupo")} - {r.get("rotulo")}'):
                    regras_ok.append(r)
                else:
                    regras_erro.append(r)
            # busca as chaves da regra que iniciam com tags_ ou tags- para padronizar a lista
            for chave in list(r.keys()):
                if chave.lower()[:5] in ('tags_','tags-') and r[chave]:
                   r[chave] = regras_corrigir_tags(r[chave])
        regras_ok = RegrasPesquisaBR.ordenar_regras(regras_ok)
        comp = ' ' if not externas else ' externas '
        print(f'Número de regras{comp}carregadas: {len(regras_ok)}')
        if any(regras_erro):
            print(f' * número de regras{comp}ignoradas por erro: {len(regras_erro)}')
        #with open('teste.json','w') as f:
        #    f.write(json.dumps(regras_ok,indent=1))
        return regras_ok, regras_erro


    #################################################################################
    # NÃO SOBRESCREVER ESSE MÉTODO, ele recarrega e verifica as regras ou retorna do cache
    # mudança no id do controle do cache, recarrega os dados e os filtros de regras
    def get_regras_erro_db(self):
        CONFIG.id_cache = self.get_controle_cache_db()
        self.carregar_regras_db(CONFIG.id_cache)
        return self.REGRAS_ERRO

    #################################################################################
    # NÃO SOBRESCREVER ESSE MÉTODO, ele recarrega e verifica as regras ou retorna do cache
    # mudança no id do controle do cache, recarrega os dados e os filtros de regras
    def get_regras_carregadas_db(self):
        CONFIG.id_cache = self.get_controle_cache_db()
        self.carregar_regras_db(CONFIG.id_cache)
        return self.REGRAS_CARREGADAS   

    #################################################################################
    # SOBRESCREVER OPCIONALMENTE esse médodo na nova classe que herda de RegrasModelBase
    # pode ser uma data de atualização no banco ou a data de um arquivo para saber 
    # se o cache deve ser recarregado. Se não for implementado, vai retornar a data 
    # até o minuto - obrigando a recarga das regras e dos filtros a cada minuto
    # as regras são recarregadas somente se essa data for alterada ou se o cache ficar cheio
    def get_controle_cache_db(self):
        msg = f'### ATENÇÃO ### - {self.__class__.__name__} não implementou "get_controle_cache_db()"'
        print(msg)
        dt = datetime.now().strftime("%Y-%m-%d %H:%M") 
        print(f'(* data de controle de cache RegrasModelBase: {dt} *)')
        return dt

###################################################################
### EXEMPLO de implementação do RegrasModel com arquivo de regras
### carregamento de regras pelo arquivo
###################################################################
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

    # limpa o cache da data de validade do cache para exigir nova verificação
    def limpar_cache_regras_db(self):
        return CACHE_CONTROLE_CACHE.clear()
        
    # evita muitas chamadas concorrentes ao disco para pegar a data do arquivo
    # tem mais sentido para db
    @cached(CACHE_CONTROLE_CACHE, lock=LOCK_CACHE)
    def get_controle_cache_db(self):
        res = pathlib.Path(self.ARQ_REGRAS).stat().st_mtime
        print(f'(* data de controle de cache "{self.ARQ_REGRAS}": {res} *)')
        return res

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
