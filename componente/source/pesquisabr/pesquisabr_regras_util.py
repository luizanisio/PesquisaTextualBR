# -*- coding: utf-8 -*-
#######################################################################
# Código complementar à classe PesquisaBR para registro de logs de tempo
# Esse código, dicas de uso e outras informações: 
#   -> https://github.com/luizanisio/PesquisaTextualBR
# Luiz Anísio 
# 19/04/2023 - disponibilizado no GitHub  
#######################################################################
import time
import os
from datetime import datetime

class __UtilRegrasConfig__():
    def __init__(self):
        self.regex_timeout = 5 * 60
        # logar regex que demorarem mais de x segundos
        self.tempo_lentos = 30
        # quantos logar nos erros e lentos
        self.qtd_logs = 20
        # tempo em segundos para gravar os logs em disco
        self.tempo_gravacao = 60
        # lista dos últimos x erros e lentos 
        self.erros_timeout = []
        self.lentos = []
        # 
        self.arquivo_lentos = None 
        self.arquivo_timeout = None
        # ultima gravação
        self.ultima_gravacao = 0

    def print_config(self):
        print( '----------------------------------------------')
        print( 'UtilRegrasConfig: ')
        print(f' - regras lentas:  {self.tempo_lentos}s')
        print(f' - regex timeout:  {self.regex_timeout}s')
        print(f' - tempo gravação: {self.tempo_gravacao}s')
        print(f' - qtd regras log: {self.qtd_logs}')
        print( '----------------------------------------------')

    def gravar_logs(self):
        # ao gravar os logs, limpa as listas
        if self.arquivo_lentos:
           if self.__gravar_dados__(self.arquivo_lentos, self.lentos):
              self.lentos = []

        if self.arquivo_timeout: 
           if self.__gravar_dados__(self.arquivo_timeout, self.erros_timeout):
              self.erros_timeout = [] 

    def __gravar_dados__(self, arquivo, dados):
        os.makedirs( os.path.split(arquivo)[0] , exist_ok=True)
        controle = f'{arquivo}.lc'
        if time.time() - self.__tempo_arquivo__(controle) < 5:
           return 
        # controle para várias instâncias rodando ao mesmo tempo
        try:
         with open(controle, 'w')  as f:
               f.write(f'controle')
        except: 
           return
        # a gravação é tentada, é uma amostragem das regras lentas ou com timeout
        tempo_arquivo = self.__tempo_arquivo__(arquivo)
        if time.time() - tempo_arquivo > self.tempo_gravacao:
           if tempo_arquivo == 0:
              comp = '(primeira gravação)'
           else:
              comp =  f'(última gravação com {time.time() - tempo_arquivo:.2f}s)' 
           print(f'Gravando arquivo de log {arquivo} {comp} ...')
        else:
           # não precisa gravar ainda
           return False 
        
        if arquivo and len(dados) > 0:
           try:
              # carrega o arquivo para juntar com o que está na memória
              # se tiver poucos dados na memória
              if len(dados) < self.qtd_logs and os.path.isfile(arquivo):
                 with open(arquivo, 'r') as f:
                      dados_arq = f.read().split('\n')
                      dados_arq += list(dados)
                      dados_arq = dados_arq[-self.qtd_logs:]
              else:
                 dados_arq = list(dados) 
              with open(arquivo, 'w') as f:
                   f.write('\n'.join(dados_arq[::-1] ))
              self.ultima_gravacao = time.time()
              return True
           except Exception as e:
                print(f'ERRO: gravando arquivo de log {arquivo} \n{e}')
        return False

    def inserir_log(self, regra, tempo1, tempo2, tamanho, timeout):
        # verifica se grava o log - timeout sempre grava
        if len(regra) == 0:
           return 
        if (not timeout) and (self.tempo_lentos <= 0):
           return 
        if (not timeout) and (tempo1 + tempo2 < self.tempo_lentos):
           return
        dthr = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        txt_tempo = f'( processar texto: {tempo1:.1f}s regra: {tempo2:.1f}s {tamanho} bytes - {dthr}) || '
        if timeout:
           _regra = regra.replace('\n',' ')
           self.erros_timeout.append(f'{txt_tempo}{_regra}')
           if len(self.erros_timeout) > self.qtd_logs:
              self.erros_timeout.pop(0)
        else:
           self.lentos.append(f'{txt_tempo}{regra}')
           if len(self.lentos) > self.qtd_logs:
              self.lentos.pop(0)
        self.gravar_logs()

    def retornar_logs_consolidados(self, timeout):
        if timeout:
           return self.__retornar_logs__(self.arquivo_timeout, self.erros_timeout)
        return self.__retornar_logs__(self.arquivo_lentos, self.lentos)

    def __retornar_logs__(self, arquivo, dados):
        if arquivo and os.path.isfile(arquivo):
            with open(arquivo, 'r') as f:
                dados_arq = f.read().split('\n')
                dados_arq += list(dados)
        else:
            dados_arq = list(dados)
        return list(set(dados_arq))
            
    def __tempo_arquivo__(self, arquivo):
         if os.path.exists(arquivo):
            return os.path.getmtime(arquivo)
         else:
            return 0

# para que os logs sejam gravados, é necessário configurar o nome dos arquivos
UtilRegrasConfig = __UtilRegrasConfig__()
