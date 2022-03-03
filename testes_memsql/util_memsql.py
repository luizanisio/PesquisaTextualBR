# -*- coding: utf-8 -*-
import pandas as pd
import os
from datetime import datetime
import json
#conexão com o MemSQL
import MySQLdb  #o cliente MySQL é utilizado para conexão com o banco MemSQL

class MemSQL_Conexao:
    def clone(self):
        return MemSQL_Conexao(host=self.host, porta=self.porta,
                                 database=self.database, 
                                 usuario=self.usuario, senha=self.senha, 
                                 connect_timeout=self.connect_timeout, conexao_pronta=self.conexao_pronta)

    def __init__(self, host, porta=3306, database=None, usuario=None, senha=None, connect_timeout=15, conexao_pronta = None):
        self.host = host
        self.porta = porta if type(porta) is int and porta>0 else 3306
        self.usuario = usuario
        self.senha = senha
        self.database = database
        self.conexao_pronta = conexao_pronta
        if conexao_pronta is None:
            self.connect_timeout = connect_timeout if type(connect_timeout) is int and connect_timeout>0 else 15
            self.conexao = MySQLdb.connect(host=f'{self.host}',user=f'{self.usuario}',passwd=f'{self.senha}', 
                                        port=self.porta, connect_timeout=self.connect_timeout, 
                                        charset='utf8' )
            self.conexao.autocommit(True)
            if self.database:
                self.conexao.cursor().execute(f'use {self.database}')
        else:
            self.conexao = conexao_pronta


    def get_dicts(self, sql, parametros=None, dumps = False):
        df = self.get_df(sql=sql, parametros=parametros)
        if not (type(df) is pd.DataFrame):
            return df
        def _timestamp_str(d):
            if type(d) is pd.Timestamp:
                return pd.Timestamp(d).strftime("%Y-%m-%d %H:%M:%S") # d.astype(str) #datetime.fromtimestamp(d).strftime("%Y/%m/%d %H:%M:%S")
            elif type(d) is datetime:
                return d.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return d
        colunas = list(df.columns)
        dados = []
        for _, row in df.iterrows():
            dados.append({c: _timestamp_str( row[c] ) for c in colunas})
        return dados if not dumps else json.dumps(dados)

    def get_dict(self, sql, parametros = None, dumps = False):
        dados = self.get_dicts(sql=sql, parametros=parametros)
        if not (type(dados) is list):
            return dados
        dados = dados[0] if len(dados)>0 else dict({})
        return dados if not dumps else json.dumps(dados)

    def get_df(self,sql, parametros=None):
        return pd.read_sql(sql, self.conexao, params=parametros)

    def get_valor(self,sql, parametros=None, default=None):
        cursor = self.conexao.cursor()
        cursor.execute(sql, parametros)
        data = cursor.fetchall()
        return data[0][0] if len(data)>0 else default

    def exec_sql(self,sql, parametros=None):
        cursor = self.conexao.cursor()
        cursor.execute(sql,parametros)
        return cursor.rowcount

    def fetchall_sql(self,sql, parametros=None):
        cursor = self.conexao.cursor()
        cursor.execute(sql,parametros)
        return cursor.fetchall()

    @staticmethod
    def erro_mem_sql_repetir(msg_erro):
        msg = str(msg_erro).lower()
        if not msg:
            return False
        return msg.find('re-running the query')>=0 or \
            msg.find('lock wait timeout exceeded')>=0 or \
            msg.find('memory used by memsql')>0 or \
            msg.find('failed to allocate memory')>0 or \
            msg.find('too many queries are queued for execution')>0 or \
            msg.find('maximum_memory')>0 or \
            msg.find('internally killed')>0 or \
            msg.find('connection reset by peer')>0 or \
            msg.find('lost connection to mysql')>0 or \
            msg.find('unknown mysql server host')>0 or \
            (msg.find('has no master instance')>0 and msg.find('partition are down')>0) or \
            msg.find('connection refused')>0 or msg.find('errno=111')>0 or \
            msg.find('unable to connect to leaf')>0 or \
            msg.find('partition are down')>0 or \
            msg.find('mysql server has gone away')>0 or \
            msg.find("can't connect to mysql server on")>0 or \
            msg.find('leaf error')>0 or \
            msg.find('failed to fsync plancache directory')>0 or \
            msg.find('er_compilation_timeout')>0 or \
            msg.find('er_command_proc_dead')>0 or \
            msg.find('er_memsql_failed_code_gen')>0 or \
            msg.find('errno=104')>0

    @staticmethod
    def erro_mem_sql_user_raise(msg_erro):
        msg = str(msg_erro).lower()
        if not msg:
            return False
        return msg.find('er_user_raise')>=0 

    @staticmethod
    def erro_mem_sql_chave_duplicada( msg_erro):
        msg = str(msg_erro).lower()
        if not msg:
            return False
        return msg.find('duplicate entry')>=0 
    
    def close(self):
        self.conexao.close()

    def sql_diff_tempo_horas(self, campo_data, tempo_horas:int):
        return f' dthr_status < ADDDATE(now(), INTERVAL - {tempo_horas} hour) '
    def sql_diff_tempo_minutos(self, campo_data, tempo_minutos:int):
        return f' dthr_status < ADDDATE(now(), INTERVAL - {tempo_minutos} minute) '

if __name__ == '__main__':
    mem = MemSQL_Conexao(host='meumem', usuario='mem', senha='mem')
    print(mem.get_df('show processlist'))

