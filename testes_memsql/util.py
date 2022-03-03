# -*- coding: utf-8 -*-
import platform
from multiprocessing import cpu_count
from multiprocessing.dummy import Pool as ThreadPool
import re
import time

class Util():
    @staticmethod
    def carregar_arquivo(arq, limpar=False, juntar_linhas=False, retornar_tipo=False):
        arq = Util.corrige_pasta_os(arq)
        tipos = ['utf8', 'ascii', 'latin1']
        linhas = None
        tipo = None
        for tp in tipos:
            try:
                with open(arq, encoding=tp) as f:
                    tipo, linhas = (tp, f.read().splitlines())
                    break
            except UnicodeError:
                continue
        if not linhas:
            with open(arq, encoding='latin1', errors='ignore') as f:
                tipo, linhas = ('latin1', f.read().splitlines())
        # otimiza os tipos de retorno
        if limpar and juntar_linhas:
            linhas = re.sub('\s+\s*', ' ', ' '.join(linhas))
        elif limpar:
            linhas = [re.sub('\s+\s*', ' ', l) for l in linhas]
        elif juntar_linhas:
            linhas = ' '.join(linhas)
        if retornar_tipo:
            return tipo, linhas
        else:
            return linhas

    @staticmethod
    def gravar(arquivo, texto, append=False, tipo="utf8"):
        if type(texto) is str:
            texto = [texto]
        fout = open(arquivo, "w" if not append else "a", encoding=tipo)
        for i, linha in enumerate(texto):
            quebra = '\n' if i<len(texto)-1 else ''
            if type(linha) is list:
                fout.write(' '.join(linha) + quebra)
            else:
                fout.write(str(linha) + quebra)
        fout.close()

    @staticmethod
    def corrige_pasta_os(caminho):
        if platform.system().lower().find('linux') >= 0:
            caminho = caminho.replace('\\', '/')
        return caminho

    @staticmethod
    def progress_bar(current_value, total, msg=''):
        increments = 50
        percentual = int((current_value / total) * 100)
        i = int(percentual // (100 / increments))
        text = "\r[{0: <{1}}] {2:.2f}%".format('=' * i, increments, percentual)
        print('{} {}           '.format(text, msg), end="\n" if percentual == 100 else "")

    @staticmethod
    def mensagem_inline(msg=''):
        i = random.randint(0,1)
        comp = "  . . ." if i==0 else ' . . .'
        comp=comp.ljust(100)
        print(f'\r{msg}{comp}', end="\n" if not msg else "" )

    @staticmethod
    def map_thread(func, lista, n_threads=None):
        if (not n_threads) or (n_threads<2):
            n_threads = Util.cpus()
        #print('Iniciando {} threads'.format(n_threads))
        pool = ThreadPool(n_threads)
        pool.map(func, lista)
        pool.close()
        pool.join()

    #recebe uma lista e transforma os dados da própria lista usando a função
    #a função vai receber o valor de cada item e o retorno dela vai substituir o valor do item na lista
    @staticmethod
    def map_thread_transform(func, lista, n_threads=None, msg_progresso=None):
        prog=[0]
        def _transforma(i):
            if msg_progresso is not None:
                Util.progress_bar(prog[0], len(lista),f'{msg_progresso} {prog[0]+1}/{len(lista)}')
                prog[0] = prog[0] + 1
            lista[i] = func(lista[i])
        Util.map_thread(func=_transforma, lista= range(len(lista)))
        if msg_progresso is not None:
            Util.progress_bar(1,1) #finaliza a barra

    @staticmethod
    def cpus(uma_livre=True):
        num_livres = 1 if uma_livre else 0
        return cpu_count() if cpu_count() < 3 else cpu_count() - num_livres

    @staticmethod
    def pausa(segundos, progresso = True):
        if segundos ==0:
            return
        if segundos<1:
            segundos =1
        for ps in range(0,segundos):
            time.sleep(1)
            Util.progress_bar(ps,segundos+1,f'Pausa por {segundos-ps}s')
        Util.progress_bar(segundos,segundos,f'Pausa finalizada {segundos}s')

