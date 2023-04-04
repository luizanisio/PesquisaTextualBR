# -*- coding: utf-8 -*-
from pesquisabr.util_memsql import MemSQL_Conexao
from pesquisabr.pesquisabr import PesquisaBR, TESTES_COMPLETOS
import enum
from datetime import datetime 
import json
import regex as re
from cachetools import cached, LRUCache, TTLCache
from threading import RLock
from hashlib import sha1 as hl_sha1

cache_mapa = TTLCache(maxsize=20000, ttl=60 * 60 * 24)
# impede o cache de status vazio pois será gravado no banco depois da comparação finalizada
class CacheCompara(TTLCache):
    def __setitem__(self, key, value, cache_setitem=TTLCache.__setitem__):
        if value == '':
            #print('######################### cache ignorado: ', key, f'valor = "{value}"')
            pass
        else:
            super().__setitem__(key=key, value=value, cache_setitem=TTLCache.__setitem__)
            #print('######################### cache armazenado: ', key, f'valor = "{value}"')

cache_compara = CacheCompara(maxsize=100000, ttl=60 * 60 * 24) # cache de 1 dia para as comparações
lock = RLock()

class PesquisaBRMemSQLTeste():
      def __init__(self, db_instance: MemSQL_Conexao):
          self.db_instance = db_instance
          self.pbmem= PesquisaBRMemSQL(self.db_instance, print_debug=True)
          self.pb = PesquisaBR()

    
      RE_BR = re.compile('\s*<br>\s*')

      def testes_processamento(self):
            diferentes = 0
            retorno_dict = dict({'retorno': []})
            textos = [t['texto'] for t in TESTES_COMPLETOS if t.get('texto')]
            textos.append('as casas são legais inss tais quais leis lençóis anzóis as is guis quais ruins blablares blablales raizes juizes ')
            _funcao = self.pbmem.FUNCAO_PROCESSAMENTO
            for i, t in enumerate(textos):
                # planifica o texto
                if type(t) is dict:
                    _texto = [v for _,v in t.items()]
                    _texto = ' '.join(_texto)
                else:
                    _texto = t               
                print('------------------------------------------------------')
                print('Texto original      : ',  _texto.replace('\n',' <br> '))
                self.pb.novo_texto(_texto)
                procpy = str(' '.join(self.pb.tokens_texto)).strip().replace('\n','<br>')
                procpy = self.RE_BR.sub('<br>',procpy)
                print('Processamento python: ', procpy)
                
                procdb = self.db_instance.get_valor(f'select {_funcao}(%s,true)',[_texto],'') 
                procdb = self.RE_BR.sub('<br>',procdb)
                print('Processamento banco:  ', procdb)
                if procpy != procdb:
                    print('PROCESSAMENTOS DIFERENTES ')
                    print('Tokens: ', self.pb.tokens_texto)
                    print('Proc: ', self.pb.processar_texto(_texto))
                    exit()
                    diferentes += 1
            print('------------------------------------------------------')
            print('Total de textos diferentes: ', diferentes)

class TiposPesquisa(enum.Enum):
   Nova = 1
   Filtro = 2
   Uniao = 3

def hash_string_sha1(texto):
    _txt = '|'.join(texto) if type(texto) is list else str(texto)
    return hl_sha1(_txt.encode('utf-8')).hexdigest()    

class ConfigTipoDocumento():
    RE_NUMEROS = re.compile('^[0-9]+$')
    def __init__(self, configuracoes:dict, id_documento = ''):
        if (not configuracoes) or (len(configuracoes.keys()) == 0):
            raise Exception(f'PesquisaBRMemSQL: tipo de documento não configurado corretamente')
        if not configuracoes.get('tabela'):
            raise Exception(f'PesquisaBRMemSQL: tabela não configurada para o tipo de documento especificado')
        if not (configuracoes.get('campo_id') or configuracoes.get('campo_seq')):
            raise Exception(f'PesquisaBRMemSQL: campo id/seq não configurado para o tipo de documento especificado')
        if not configuracoes.get('campo_texto'):
            raise Exception(f'PesquisaBRMemSQL: campo texto não configurado para o tipo de documento especificado')
        if not configuracoes.get('campo_data'):
            raise Exception(f'PesquisaBRMemSQL: campo data não configurado para o tipo de documento especificado')
        def _limpa_campo(campo):
            return '' if (campo is None ) else campo.replace('"','').replace("'",'').strip()
        self.tabela = _limpa_campo( configuracoes.get('tabela','') )
        self.campo_texto = _limpa_campo( configuracoes.get('campo_texto','') )
        self.campo_id = _limpa_campo( configuracoes.get('campo_id','') )
        self.campo_seq = _limpa_campo( configuracoes.get('campo_seq','') )
        self.campo_data = _limpa_campo( configuracoes.get('campo_data','') )
        self.campo_score = _limpa_campo( configuracoes.get('campo_score') )
        self.campo_id_seq = self.campo_id if self.campo_id else self.campo_seq
        self.campo_pesquisa_id_seq = 'id_documento' if self.campo_id else 'seq_documento'
        self.campo_json = configuracoes.get('ind_json_campos',0) == 1
        self.substituir_texto = configuracoes.get('ind_substituir_texto',0) == 1
        self.set_id(id_documento)

    # recebe o id de um documento e preenche os campos opcionais de acordo com o mapeamento
    # para a montagem de sqls de forma dinâmica
    def set_id(self, id_documento):
        if self.campo_id:
            self.valor_id = str(id_documento)
            self.valor_id_seq = self.valor_id
            self.valor_seq = int(id_documento) if self.RE_NUMEROS.match(id_documento) else 0
        else:
            if type(id_documento) is str:
                self.valor_seq = int(id_documento) if self.RE_NUMEROS.match(id_documento) else 0
            else:
                self.valor_seq = int(id_documento)
            self.valor_id_seq = self.valor_seq
            self.valor_id = str(self.valor_seq)

class PesquisaBRMemSQL():
    LIMITE_MAXIMO = 300000
    DATABASE = 'pesquisabr'
    TABELA_SESSAO = 'pesquisabr.sessao_pesquisa'
    TABELA_SESSAO_DOC = 'pesquisabr.sessao_pesquisa_doc'
    TABELA_MAPA = 'pesquisabr.mapa_pesquisa'
    TABELA_CACHE = 'pesquisabr.cache_pesquisa'
    TABELA_TEXTO = 'pesquisabr.documento_pesquisa'
    FUNCAO_PROCESSAMENTO = 'pesquisabr.f_pre_processar_texto'
    TEMPO_LIMPEZA_PESQUISA = 12      # 12 horas
    TEMPO_LIMPEZA_CACHE = 180 # 180 dias 
    TEMPO_RODAR_LIMPEZA_PESQUISA = 5 # 5 minutos
    ultima_limpeza = None
    debug_metodo_anterior = ''

    def __init__(self, db_instance: MemSQL_Conexao, print_debug = False ):
        self.print_debug = print_debug
        self.db_instance = db_instance
        
        self.print_msg_debug()
        self.print_msg_debug(msg=f'conectado {self.db_instance.host}:{self.db_instance.porta} | database {self.db_instance.database}', metodo = 'init')
        self.print_msg_debug(msg=f'Tipos de documentos configurados: ' + ', '.join(self.carregar_tipos_documento_cfg()), metodo = 'init')

        self.limpar_pesquisas_antigas(True)

    def pesquisar(self, sessao:str, tipo_documento:str, criterios:str, tipo_pesquisa= TiposPesquisa.Nova, limite=1000):
        _sessao = self.limpar_nome_sessao(sessao)
        pb = PesquisaBR(criterios=criterios)
        # carrega até o limite máximo de registros pela consulta do memSQL
        qtd_pre = self.pre_pesquisar(sessao=sessao, tipo_documento=tipo_documento, criterios_and_or_not= str(pb.criterios_and_or_not), tipo_pesquisa = tipo_pesquisa, limite=self.LIMITE_MAXIMO)
        if qtd_pre.get('erros'):
            return qtd_pre
        qtd_pre = qtd_pre.get('qtd_documentos',0)
        # filtra até retornar o limite que o usuário pediu
        self.print_msg_debug(f'Filtrando critérios completos até {limite}/{qtd_pre}: tipo_documento = {tipo_documento} sessão = {sessao}', 'pesquisar')
        qtd_final = self.filtrar(sessao=sessao, tipo_documento=tipo_documento, criterios_completos=str(criterios), limite=self.LIMITE_MAXIMO, limite_resultado=limite)
        qtd_final = qtd_final.get('qtd_documentos',0)
        self.print_msg_debug(f'Pesquisa concluída - {qtd_final}/{qtd_pre}: tipo_documento = {tipo_documento} sessão = {sessao}', 'pesquisar')
        self.db_instance.exec_sql(f'delete from {self.TABELA_SESSAO_DOC} where sessao=%s and ind_status <> "F" ',[_sessao])
        return self.retorno_padrao(qtd_documentos_recebidos=qtd_pre, qtd_documentos=qtd_final, sessao=sessao, criterios=criterios, criterios_and_or_not=pb.criterios_and_or_not,erros = pb.erros, limite=limite,tipo_pesquisa=tipo_pesquisa)

    def limpar_nome_sessao(self, sessao:str):
        return str(sessao).replace('"','').replace("'",'')
    def limpar_nome_tipo_documento(self, tipo_documento:str):
        return str(tipo_documento).replace('"','').replace("'",'')
    def limpar_criterios(self, criterios:str, aspas = True):
        if aspas:
            return "'" + criterios.strip().replace("'",'"') + "'"
        else:
            return criterios.strip().replace("'",'"')

    def carregar_tipo_documento_cfg(self,tipo_documento, id_documento = ''):
        _tipo_documento = self.limpar_nome_tipo_documento(tipo_documento)
        tdc = self.db_instance.get_dict(f'select * from {self.DATABASE}.tipo_documento_cfg where tipo_documento=%s',[str(_tipo_documento)])
        tdc = ConfigTipoDocumento(configuracoes= tdc, id_documento=id_documento)
        tdc.tipo_documento = _tipo_documento
        return tdc

    def carregar_tipos_documento_cfg(self):
        df = self.db_instance.get_df(f'select tipo_documento from {self.DATABASE}.tipo_documento_cfg ')
        return list(df['tipo_documento'])

    # busca o status atual dos filtros da pesquisa e atualiza na tabela da pesquisa
    def atualizar_status_pesquisa(self, sessao:str, tipo_documento:str, finalizada = False):
        _sessao = self.limpar_nome_sessao(sessao)
        _tipo_documento = self.limpar_nome_tipo_documento(tipo_documento)
        if not finalizada:
            _sql_status = f'select ind_status, dthr_status from {self.TABELA_SESSAO_DOC}  ' +\
                        '  where sessao = %s ' + \
                        '  order by case when ind_status = "N" then 0 ' +\
                        '                when ind_status = "M" then 1 ' + \
                        '                when ind_status = "P" then 2 ' + \
                        '                else 3 end ' + \
                        'limit 1 '
            status = self.db_instance.get_dict(_sql_status, [str(_sessao)])
            ind_status = status.get('ind_status','N') if status else 'N'
        else:
            ind_status = 'F'
        if self.db_instance.get_valor(f'select 1 from {self.TABELA_SESSAO} where sessao = %s',[str(_sessao)],0) == 0:
           _sql = f'insert into {self.TABELA_SESSAO} (sessao, ind_status, dthr_status, tipo_documento) values (%s,%s,now(),%s)'
           self.db_instance.exec_sql(_sql, [str(_sessao), str(ind_status), str(_tipo_documento)])
        else:
            _sql = f'update {self.TABELA_SESSAO} set ind_status = %s, dthr_status = now() where sessao = %s '
            self.db_instance.exec_sql(_sql, [str(ind_status),str(_sessao)])
        # atualiza as quantidades
        _sql_quantidades = 'update pesquisabr.sessao_pesquisa s ' + \
                           ' set qtd_pesquisa_rapida = (select count(1) from pesquisabr.sessao_pesquisa_doc d where d.sessao =s.sessao ), ' + \
	                       '     qtd_doc_aceitos = (select count(1) from pesquisabr.sessao_pesquisa_doc d where d.sessao =s.sessao and ind_status="F"), ' + \
	                       '     qtd_doc_removidos = (select count(1) from pesquisabr.sessao_pesquisa_doc d where d.sessao =s.sessao and ind_status="X") ' + \
                           ' where sessao = %s'
        self.db_instance.exec_sql(_sql_quantidades, [str(_sessao)])
        # finaliza retornando o código do status geral da pesquisa
        self.print_msg_debug(f'sessão: "{_sessao}" tipo_documento: {tipo_documento}| {ind_status} ', 'atualizar_status_pesquisa')            
        return str(ind_status)

    def retorno_padrao(self, qtd_documentos_recebidos=None, qtd_documentos=None, sessao= None, tipo_documento = None, 
                       criterios = None, criterios_and_or_not = None, limite =None, tipo_pesquisa = None, erros=None):
        _res = {'qtd_documentos': qtd_documentos, 
                'qtd_documentos_recebidos': qtd_documentos_recebidos,
                'sessao' : sessao,        
                'criterios': criterios.replace('"',"'") if criterios != None else None, 
                'criterios_aon': criterios_and_or_not.replace('"',"'") if criterios_and_or_not != None else None, 
                'erros': erros, 
                'limite': limite, 
                'tipo_pesquisa': str(tipo_pesquisa)}        
        return {c:v for c,v in _res.items() if v != None}

    ## busca os documentos realizando a pesquisa com os critérios AND OR NOT e incluindo os ids na sessão de pesquisa
    # os registros já iniciam com o status P (pré_filtrado)
    def pre_pesquisar(self, sessao:str, tipo_documento:str, criterios_and_or_not:str, limite=1000, tipo_pesquisa= TiposPesquisa.Nova):
        if tipo_pesquisa == TiposPesquisa.Filtro:
            _q = self.pre_filtrar( sessao= sessao, tipo_documento = tipo_documento, criterios_and_or_not = criterios_and_or_not)
            return self.retorno_padrao(qtd_documentos=_q, sessao=sessao, criterios_and_or_not=criterios_and_or_not, limite=limite,tipo_pesquisa=tipo_pesquisa)
        if tipo_pesquisa == TiposPesquisa.Nova:
           self.limpar_pesquisa(sessao)
        _config = self.carregar_tipo_documento_cfg(tipo_documento)
        _sessao = self.limpar_nome_sessao(sessao)
        _criterios = self.limpar_criterios(criterios_and_or_not)
        _retorno = self.retorno_padrao()

        if _criterios.replace('"','').replace("'",'') == '':
            msg_erro = f'nenhum critério informado'
            self.print_msg_debug(msg = msg_erro, metodo='pre_pesquisar')
            return self.retorno_padrao(erros = msg_erro, qtd_documentos=0, sessao=sessao, criterios_and_or_not=criterios_and_or_not, limite=limite,tipo_pesquisa=tipo_pesquisa)

        if _config.campo_score:
            _valor_score = f" {_config.campo_score} + (MATCH({_config.campo_texto}) AGAINST ({_criterios}) )"
        else:
            _valor_score = f" MATCH({_config.campo_texto}) AGAINST ({_criterios}) "

        _limit = f' limit {int(limite)}' if type(limite) is int and limite > 0 else f'{self.LIMITE_MAXIMO}'
        _sql_insert = f'insert into {self.TABELA_SESSAO_DOC} (sessao, id_documento, seq_documento, score, ind_status, dthr_status) '
        if _config.campo_id:
           _sql_busca = f'select "{_sessao}", {_config.campo_id_seq}, 0, {_valor_score} as score, "P", now() from {_config.tabela} tbl where MATCH({_config.campo_texto}) AGAINST ({_criterios})  '
        else:
           _sql_busca = f'select "{_sessao}", "",{_config.campo_id_seq}, {_valor_score} as score, "P", now() from {_config.tabela} tbl where MATCH({_config.campo_texto}) AGAINST ({_criterios})  '

        #print(_sql_busca)
        _sql_extra = ''
        _msg_dbug = 'nova pré pesquisa'
        if tipo_pesquisa == TiposPesquisa.Uniao:
            _msg_dbug = 'pré pesquisa complementar'
            _sql_extra = f' and not exists(select 1 from {self.TABELA_SESSAO_DOC} tbl2 where tbl2.id_documento = tbl.{_config.campo_id_seq} and tbl2.sessao="{_sessao}" )'

        _sql_busca = f'{_sql_insert} {_sql_busca} {_sql_extra} {_limit}'
        self.print_msg_debug(msg = f'iniciando {_msg_dbug} [sessao={_sessao}]: {_criterios}', metodo='pre_pesquisar')
        # realiza a pesquisa com o insert na tabela de sessão
        _q = self.db_instance.exec_sql(_sql_busca)
        self.print_msg_debug(f'{_msg_dbug} realizada [sessao={_sessao}]: {_q} registros encontrados', metodo='pre_pesquisar')
        # atualizar o status da sessão
        self.atualizar_status_pesquisa(_sessao, tipo_documento)
        return self.retorno_padrao(qtd_documentos=_q, sessao=sessao, criterios_and_or_not=criterios_and_or_not, limite=limite,tipo_pesquisa=tipo_pesquisa)

    ## busca os documentos realizando a pesquisa com os critérios AND OR NOT e incluindo os ids na sessão de pesquisa
    # os registros com status N (novos) e M (executando Match) são verificados e atualizados para o status P (pré_filtrado) ou X (excluído)
    def pre_filtrar(self, sessao:str, tipo_documento:str, criterios_and_or_not:str):
        _config = self.carregar_tipo_documento_cfg(tipo_documento)
        _sessao = self.limpar_nome_sessao(sessao)
        _criterios = self.limpar_criterios(criterios_and_or_not)
        if _criterios == '':
            msg_erro = f'nenhum critério informado'
            self.print_msg_debug(msg = msg_erro, metodo='pre_filtrar')
            return self.retorno_padrao(erros = msg_erro, qtd_documentos=0, sessao=sessao, criterios_and_or_not=criterios_and_or_not, tipo_pesquisa=TiposPesquisa.Filtro)

        # indica que os documentos da sessão iniciaram o match
        self.print_msg_debug(msg = f'preparando sessão para o filtro AON [sessao={_sessao}]: {_criterios}', metodo='pre_filtrar')
        _sql_filtro = f'update {self.TABELA_SESSAO_DOC} set ind_status = "M", dthr_status = now() where ind_status in ("M","N") and sessao = "{_sessao}" '
        self.db_instance.exec_sql(_sql_filtro)

        # indica como pré-processados os documentos que são retornados atualizados pelo match
        self.print_msg_debug(msg = f'realizando o match dos documentos da sessão [sessao={_sessao}]: {_criterios}', metodo='pre_filtrar')
        _sql_filtro = f'update {self.TABELA_SESSAO_DOC} tbl2 ' + \
                      f'   inner join {_config.tabela} tbl on tbl2.{_config.campo_pesquisa_id_seq} = tbl.{_config.campo_id_seq} and tbl2.sessao="{_sessao}" and tbl2.ind_status = "M" ' + \
                      f'set tbl2.ind_status = "P", dthr_status = now()        ' + \
                      f'where tbl2.sessao="{_sessao}" and tbl2.ind_status = "M"  ' + \
                      f'and MATCH(tbl.{_config.campo_texto}) AGAINST ({_criterios}) > 0.1  ' 
        _qok = self.db_instance.exec_sql(_sql_filtro)

        # indica que o match não ocorreu para os que continuam com M
        self.print_msg_debug(msg = f'finalizando status dos documentos da sessão [sessao={_sessao}]: {_criterios}', metodo='pre_filtrar')
        _sql_filtro = f'update {self.TABELA_SESSAO_DOC} set ind_status = "X", dthr_status = now() where ind_status = "M" and sessao = "{_sessao}" '
        _q = self.db_instance.exec_sql(_sql_filtro)

        # realiza a pesquisa com o insert na tabela de sessão
        self.print_msg_debug(f'filtro AON finalizado [sessao={_sessao}]: {_qok}/{_q} registros encontrados', metodo='pre_filtrar')
        # atualizar o status da sessão
        self.atualizar_status_pesquisa(_sessao, tipo_documento)
        return self.retorno_padrao(qtd_documentos=_q, sessao=sessao, criterios_and_or_not=criterios_and_or_not, tipo_pesquisa=TiposPesquisa.Filtro)


    def gravar_cache_comparacao(self, tipo_documento:str, criterios_completos:str, id_documento, ind_status:str):
        _config = self.carregar_tipo_documento_cfg(tipo_documento, id_documento)
        _hash_criterios = hash_string_sha1(criterios_completos)
        _sql_remove = f'delete from {self.TABELA_CACHE} where tipo_documento = %s and seq_documento = %s and id_documento = %s and hash_criterios = %s '
        _msg_dados = f'|{tipo_documento}| {_config.campo_id_seq} = {_config.valor_id_seq} | hash_criterios = {_hash_criterios} '
        # atualiza o status no cache
        if ind_status:
           self.db_instance.exec_sql(_sql_remove,[str(_config.tipo_documento), int(_config.valor_seq), str(_config.valor_id), str(_hash_criterios)])
           _sql_insere = f'insert into {self.TABELA_CACHE} (tipo_documento, seq_documento, id_documento, hash_criterios, ind_status) values (%s, %s, %s, %s, %s )'  
           self.db_instance.exec_sql(_sql_insere,[str(_config.tipo_documento), int(_config.valor_seq), str(_config.valor_id), str(_hash_criterios),str(ind_status)])
           self.print_msg_debug(f'incluindo no cache {_msg_dados}','gravar_cache_comparacao')
        return str(ind_status)

    # verifica se tem um cache válido de comparação entre o documento e o critério completo
    @cached(cache_compara, lock=lock)
    def carregar_cache_comparacao(self, tipo_documento:str, criterios_completos:str, id_documento):
        _config = self.carregar_tipo_documento_cfg(tipo_documento, id_documento)
        _hash_criterios = hash_string_sha1(criterios_completos)
        _sql_remove = f'delete from {self.TABELA_CACHE} where tipo_documento = %s and seq_documento = %s and id_documento = %s and hash_criterios = %s '
        _msg_dados = f'|{tipo_documento}| {_config.campo_id_seq} = {_config.valor_id_seq} | hash_criterios = {_hash_criterios} '
         # busca o status no cache
        _sql_busca = f'select tbc.ind_status, case when tbtxt.{_config.campo_data}<= tbc.dthr then 1 else 0 end as ind_ok from {_config.tabela} tbtxt  ' + \
                      f'inner join {self.TABELA_CACHE} tbc on tbc.{_config.campo_pesquisa_id_seq} = %s and tbc.tipo_documento = %s and hash_criterios = %s ' + \
                      f'where tbtxt.{_config.campo_id_seq} = %s '
        _qok = self.db_instance.get_dict(_sql_busca,[_config.valor_id_seq, str(_config.tipo_documento), str(_hash_criterios), _config.valor_id_seq])
        _ind_status = ''
        if _qok:
            if _qok['ind_ok'] == 0 or str(_qok['ind_status']) not in ('X','F'):
               self.db_instance.exec_sql(_sql_remove,[str(_config.tipo_documento), int(_config.valor_seq), str(_config.valor_id), str(_hash_criterios)])
               _ind_status = ''
            else:
               _ind_status = _qok.get('ind_status','')
        if _ind_status !='':
            self.print_msg_debug(f'carregando do cache ind_status = {_ind_status} - {_msg_dados}','carregar_cache_comparacao')
        else:
            self.print_msg_debug(f'ignorando do cache {_msg_dados}','carregar_cache_comparacao')
        return _ind_status

    def filtrar_cache_comparacao(sessao:str,tipo_documento:str, criterios_completos:str):
        _config = self.carregar_tipo_documento_cfg(tipo_documento)
        _hash_criterios = hash_string_sha1(criterios_completos)
        _sessao = self.limpar_nome_sessao(sessao)
        >>>>>>>>>>>>> Ajustes finais em andamento
        _sql_busca = f'select tbc.ind_status, case when tbtxt.{_config.campo_data}<= tbc.dthr then 1 else 0 end as ind_ok from {_config.tabela} tbtxt  ' + \
                      f'inner join {self.TABELA_CACHE} tbc on tbc.{_config.campo_pesquisa_id_seq} = %s and tbc.tipo_documento = %s and hash_criterios = %s ' + \
                      f'where tbtxt.{_config.campo_id_seq} = %s '
        _qok = self.db_instance.get_dict(_sql_busca,[_config.valor_id_seq, str(_config.tipo_documento), str(_hash_criterios), _config.valor_id_seq])

    # atualiza a data de utilização do cache para mantê-lo ativo - evita atualização se o uso for recente
    # serve para a limpeza do cache não para controle de uso
    # atualiza os mapas e os caches de comparação da pesquisa informada
    def atualizar_uso_cache(self, tipo_documento:str, criterios_completos:str, sessao: str):        
        _config = self.carregar_tipo_documento_cfg(tipo_documento)
        _hash_criterios = hash_string_sha1(criterios_completos)
        _sessao = self.limpar_nome_sessao(sessao)
        _sql_atualiza = f'update {self.TABELA_CACHE} cp ' + \
                        f' inner join {self.TABELA_SESSAO} sp on sp.tipo_documento =cp.tipo_documento ' + \
                        f' inner join {self.TABELA_SESSAO_DOC} spd on spd.sessao =sp.sessao and (spd.{_config.campo_pesquisa_id_seq} =cp.{_config.campo_pesquisa_id_seq}  ) ' + \
                        f' set cp.dthr_utilizacao= now()' + \
                        f' where cp.dthr_utilizacao< ADDDATE(now(), INTERVAL - 1 day) and sp.sessao = %s and cp.hash_criterios = %s and spd.ind_status in ("F","X")'
        #print('Atualiza uso do cache: ', _sql_atualiza, f'"{_sessao}"', f'"{_hash_criterios}"')
        q = self.db_instance.exec_sql(_sql_atualiza,[_sessao, _hash_criterios])
        if q > 0:
            self.print_msg_debug(f'Uso do cache atualizado {_sessao} com {q} documentos vs hash','atualizar_uso_cache')
        # utiliza;áo do mapa de documento
        _sql_atualiza = f'update {self.TABELA_MAPA} cm ' + \
                        f' inner join {self.TABELA_SESSAO} sp on sp.tipo_documento =cm.tipo_documento ' + \
                        f' inner join {self.TABELA_SESSAO_DOC} spd on spd.sessao =sp.sessao and (spd.{_config.campo_pesquisa_id_seq} =cm.{_config.campo_pesquisa_id_seq}  ) ' + \
                        f' set cm.dthr_utilizacao= now()' + \
                        f' where cm.dthr_utilizacao< ADDDATE(now(), INTERVAL - 1 day) and sp.sessao = %s and spd.ind_status in ("F","X")'
        #print('Atualiza uso do cache: ', _sql_atualiza, f'"{_sessao}"', f'"{_hash_criterios}"')
        q = self.db_instance.exec_sql(_sql_atualiza,[_sessao])
        if q > 0:
            self.print_msg_debug(f'Uso do cache atualizado {_sessao} com {q} mapas de documentos','atualizar_uso_cache')

    ## busca os documentos realizando a pesquisa com os critérios AND OR NOT e incluindo os ids na sessão de pesquisa
    # os registros com status N (novos) e M (executando Match) são verificados e atualizados para o status P (pré_filtrado) ou X (excluído)
    def filtrar(self, sessao:str, tipo_documento:str, criterios_completos:str, limite = 100, limite_resultado = 100):
        _config = self.carregar_tipo_documento_cfg(tipo_documento)
        _sessao = self.limpar_nome_sessao(sessao)
        _criterios = self.limpar_criterios(criterios = criterios_completos, aspas=False)
        if _criterios == '':
            msg_erro = f'nenhum critério informado'
            self.print_msg_debug(msg = msg_erro, metodo='filtrar')
            return self.retorno_padrao(qtd_documentos=0, sessao=sessao, criterios='', criterios_and_or_not='',erros = msg_erro, limite=limite,tipo_pesquisa=TiposPesquisa.Filtro)
        pb = PesquisaBR(criterios=criterios_completos)
        # verifica se a pesquisa tem algum operador especial e finaliza todos que já passaram pelo filtro de operadores simples
        if not pb.contem_operadores_especiais:
           _sql_finaliza = f'update {self.TABELA_SESSAO_DOC} set ind_status = "F", dthr_status = now() where ind_status = "P" and sessao = "{_sessao}" '
           q = self.db_instance.exec_sql(_sql_finaliza)
           self.print_msg_debug(f'filtro completo ignorado em {q} documento - nenhum operador especial [sessao={_sessao}]', metodo='filtrar')
           # atualizar o status da sessão
           self.atualizar_status_pesquisa(_sessao, tipo_documento,finalizada=True)
           return self.retorno_padrao(qtd_documentos_recebidos=q, qtd_documentos=q, sessao=sessao, criterios=pb.criterios, criterios_and_or_not=pb.criterios_and_or_not,erros = pb.erros, limite=limite,tipo_pesquisa=TiposPesquisa.Filtro)
        _sql_qtd = f'select count(1) from {self.TABELA_SESSAO_DOC} where sessao = %s and ind_status not in ("F","X") '
        qtd_filtrar = self.db_instance.get_valor(_sql_qtd,[str(_sessao)],0)
        if qtd_filtrar == 0:
            return self.retorno_padrao(qtd_documentos_recebidos=0, qtd_documentos=0, sessao=sessao, criterios=pb.criterios, criterios_and_or_not=pb.criterios_and_or_not,erros = pb.erros, limite=limite,tipo_pesquisa=TiposPesquisa.Filtro)
        # atualiza o status para F ou X caso a comparação id vs hash esteja no cache ainda válido
        self.filtrar_cache_comparacao(sessao=sessao,tipo_documento=tipo_documento, criterios_completos=criterios_completos)
        # busca os próximos n registros para filtrar - buscando os de maior score primeiro      
        _sql_registros = f'select {_config.campo_pesquisa_id_seq} from {self.TABELA_SESSAO_DOC} where sessao = %s and ind_status not in ("F","X") '
        _sql_registros = f'{_sql_registros} order by score desc '    
        _sql_registros = f'{_sql_registros} limit {int(limite)} '
        _registros = self.db_instance.get_dicts(_sql_registros, [str(_sessao)])
        self.print_msg_debug(f'filtro completo para {len(_registros)} documentos [sessao={_sessao}]', metodo='filtrar')
        _qtd_ok = 0

        for i, reg in enumerate(_registros):
            _id_doc = reg.get(_config.campo_pesquisa_id_seq,'')
            # verifica se existe cache da comparação
            _cache_comparacao = self.carregar_cache_comparacao(tipo_documento=tipo_documento, id_documento=_id_doc, criterios_completos=criterios_completos)
            _config.set_id(_id_doc)
            if _cache_comparacao == '':
                _mapa = self.carregar_mapa(tipo_documento=tipo_documento, id_documento=_id_doc)
                _doc_ok = False
                if len(_mapa)>=3:
                    pb.novo_mapa_texto(mapa_texto=_mapa, atualizar_pesquisa=True)
                    _doc_ok = pb.retorno()
                self.print_msg_debug(f'{i}:\tfiltro completo documento {_config.valor_id_seq} = {_doc_ok} [sessao={_sessao}]', metodo='filtrar')
                self.gravar_cache_comparacao(tipo_documento=tipo_documento, id_documento=_id_doc, criterios_completos=criterios_completos, ind_status = 'F' if _doc_ok else 'X')
            else:
                _doc_ok = _cache_comparacao == 'F'
                #self.print_msg_debug(f'{i}:\tfiltro completo (CACHE) documento {_id_doc} = {_doc_ok} [sessao={_sessao}]', metodo='filtrar')

            _status = 'X' if not _doc_ok else 'F'
            _sql_finaliza = f'update {self.TABELA_SESSAO_DOC} set ind_status = %s, dthr_status = now() where sessao = %s and {_config.campo_pesquisa_id_seq}=%s '
            self.db_instance.exec_sql(_sql_finaliza, [str(_status),str(_sessao), _config.valor_id_seq])
            _qtd_ok += (1 if _doc_ok else 0)
            if _qtd_ok == limite_resultado:
                break
            if i>0 and i % 20 == 0:
                # atualizar o status da sessão
                self.atualizar_status_pesquisa(_sessao, tipo_documento)

        self.atualizar_uso_cache(sessao = _sessao, tipo_documento=tipo_documento, criterios_completos=criterios_completos)
        # atualizar o status da sessão
        self.atualizar_status_pesquisa(_sessao, tipo_documento,finalizada=True)
        return self.retorno_padrao(qtd_documentos_recebidos=len(_registros), qtd_documentos=_qtd_ok, sessao=sessao, criterios=pb.criterios, criterios_and_or_not=pb.criterios_and_or_not,erros = pb.erros, limite=limite,tipo_pesquisa=TiposPesquisa.Filtro)

    def carregar_texto(self, tipo_documento, id_documento):
        _config = self.carregar_tipo_documento_cfg(tipo_documento = tipo_documento, id_documento=id_documento)
        _sql_busca = f'select {_config.campo_texto} from {_config.tabela} where {_config.campo_id_seq} = %s '
        _txt = self.db_instance.get_valor(_sql_busca,[_config.valor_id_seq],'')
        self.print_msg_debug(f'|{tipo_documento}| {_config.campo_id_seq} = {_config.valor_id_seq}  - tamanho {len(_txt)} bytes ', 'carregar_texto')
        return _txt

    @cached(cache_mapa, lock=lock)
    def carregar_mapa(self, tipo_documento, id_documento):
        _config = self.carregar_tipo_documento_cfg(tipo_documento = tipo_documento, id_documento=id_documento)
        _sql_busca = f'select tbmp.mapa from {_config.tabela} tbtxt  ' + \
                      f'inner join {self.TABELA_MAPA} tbmp on tbmp.{_config.campo_pesquisa_id_seq} = %s and tbmp.tipo_documento = %s ' + \
                      f'where tbtxt.{_config.campo_id_seq} = %s ' + \
                      f'      and tbtxt.{_config.campo_data}<= tbmp.dthr '
        #print(_sql_busca)                       
        _mapa = self.db_instance.get_valor(_sql_busca,[_config.valor_id_seq, str(_config.tipo_documento), _config.valor_id_seq],'')
        # existe um mapa e o mapa ainda é atual
        _msg_dados = f'|{tipo_documento}| {_config.campo_id_seq} = {_config.valor_id_seq}'
        if _mapa:
            self.print_msg_debug(f'mapa carregado do cache {_msg_dados}', 'carregar_mapa')
            return _mapa if type(_mapa) is dict else json.loads(_mapa)
        self.print_msg_debug(f'mapa desatualizado ou inexistente - recriado mapa {_msg_dados}','carregar_mapa')
        _texto = self.carregar_texto(tipo_documento=tipo_documento, id_documento=id_documento)
        if len(_texto.strip()) == 0:
            _mapa = dict({})
            self.print_msg_debug(f'mapa vazio - texto não encontrado {_msg_dados} - texto vazio ou inexistente ', 'carregar_mapa')
            return _mapa
        if _config.campo_json:
            _texto = _texto if type(_texto) is dict else json.loads(_texto.strip())
        pb = PesquisaBR(texto = _texto)
        _mapa = pb.mapa_texto
        # gravar o mapa
        self.db_instance.exec_sql(f'delete from {self.TABELA_MAPA} where tipo_documento=%s and {_config.campo_pesquisa_id_seq} = %s',[str(tipo_documento), _config.valor_id_seq])
        _txt_mapa = json.dumps(_mapa)
        _len_mapa = len(_txt_mapa)
        _len_texto = len(_texto)
        _sql_insert = f'insert into {self.TABELA_MAPA} (tipo_documento, id_documento, seq_documento, mapa, tamanho_texto, tamanho_mapa) values (%s,%s,%s,%s,%s,%s)'
        #print(_sql_insert, [str(tipo_documento), str(_id), int(_seq), str("_txt_mapa"), int(_len_texto), int(_len_mapa) ])
        self.db_instance.exec_sql(_sql_insert,[str(tipo_documento), str(_config.valor_id), int(_config.valor_seq), str(_txt_mapa), int(_len_texto), int(_len_mapa) ])
        self.print_msg_debug(f'mapa recriado {_msg_dados} - texto {_len_texto} bytes - mapa {_len_mapa} bytes ', 'carregar_mapa')
        return _mapa

    def limpar_pesquisa(self, sessao:str):
        self.limpar_pesquisas_antigas()
        _sessao = self.limpar_nome_sessao(sessao)
        self.db_instance.exec_sql(f'delete from {self.TABELA_SESSAO} where sessao = %s',[str(_sessao)])
        self.db_instance.exec_sql(f'delete from {self.TABELA_SESSAO_DOC} where sessao = %s',[str(_sessao)])

    #######################################
    # limpa pesquisas com mais de 12 horas
    #######################################
    def limpar_pesquisas_antigas(self, limpar_cache = False):
        _tempo_pesquisa = -1 if self.ultima_limpeza == None else (datetime.now() - self.ultima_limpeza).seconds
        if _tempo_pesquisa >= 0 and _tempo_pesquisa / 60 < self.TEMPO_RODAR_LIMPEZA_PESQUISA:
            self.print_msg_debug(msg='aguardando tempo de limpeza', metodo='limpar_pesquisas_antigas')
            return

        self.print_msg_debug(msg='limpando pesquisas antigas', metodo='limpar_pesquisas_antigas')
        _criterios_limpeza = f' (dthr_status < ADDDATE(now(), INTERVAL - {self.TEMPO_LIMPEZA_PESQUISA} hour) ) ' + \
                             f' or (dthr_status is null and dthr < ADDDATE(now(), INTERVAL - {self.TEMPO_LIMPEZA_PESQUISA} hour) )'

        self.db_instance.exec_sql(f'delete from {self.TABELA_SESSAO} where {_criterios_limpeza}')
        self.db_instance.exec_sql(f'delete from {self.TABELA_SESSAO_DOC} where {_criterios_limpeza}')

        self.print_msg_debug(msg=f'limpando cache de documento vs hash critérios {self.TEMPO_LIMPEZA_CACHE} dias', metodo='limpar_pesquisas_antigas')
        self.db_instance.exec_sql(f'delete from {self.TABELA_CACHE} where dthr_utilizacao< ADDDATE(now(), INTERVAL - {self.TEMPO_LIMPEZA_CACHE} day)')
        self.print_msg_debug(msg=f'limpando cache de mapas {self.TEMPO_LIMPEZA_CACHE} dias', metodo='limpar_pesquisas_antigas')
        self.db_instance.exec_sql(f'delete from {self.TABELA_MAPA} where dthr_utilizacao< ADDDATE(now(), INTERVAL - {self.TEMPO_LIMPEZA_CACHE} day)')

        self.ultima_limpeza = datetime.now()

        self.print_msg_debug(msg='pesquisas antigas removidas', metodo='limpar_pesquisas_antigas')


    #######################################
    # mostra mensagens de debug da classe
    # se estiver ativo o debug
    #######################################
    def print_msg_debug(self, msg='', metodo=''):
        if not self.print_debug:
            return
        _metodo = f'{metodo}' if metodo else ''
        if not msg:
            print(f'PesquisaBRMemSQL()')
        else:
            _comp = '        ' + (' ' * len(self.debug_metodo_anterior)) if  self.debug_metodo_anterior == _metodo else f'    {_metodo} >> '
            print(f'{_comp}{msg}')
        self.debug_metodo_anterior = _metodo

class PesquisaBRDjango(PesquisaBRMemSQL):
    def __init__(self, conexao, print_debug=False):
        mem = MemSQL_Conexao(host='django_connection', conexao_pronta = conexao )
        super().__init__(db_instance = mem, print_debug=print_debug)

