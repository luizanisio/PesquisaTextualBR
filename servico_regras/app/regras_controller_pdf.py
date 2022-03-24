# -*- coding: utf-8 -*-
from codecs import ignore_errors
from fileinput import filename
import os, time
import uuid
import pdfplumber
import traceback
import re

class UtilExtrairTextoPDF():
    __MARCADOR_PAGINA__ ='<<pg>>'

    # retorna um texto linha a linha (cada linha é uma página)
    # https://github.com/jalan/pdftotext
    @classmethod
    def extrair_textos_pdf(cls, path_arquivo):
        # Espera o caminho completo do arquivo
        if not os.path.isfile(path_arquivo):
            raise Exception('Arquivo não encontrado '+path_arquivo)

        # Load your PDF
        pdf = pdfplumber.open(path_arquivo)
        # retorna uma linha por página
        pages = [page.extract_text() for page in pdf.pages]
        pdf.close()
        return pages

    # verifica se o tipo de erro é um erro de extração (inconsistência no arquivo PDF)
    @classmethod
    def erro_extracao(cls, msg_erro):
        msg = str(msg_erro).lower()
        if not msg:
            return False
        msg += ' TRACE: ' + traceback.format_exc()
        if msg.find("argument of type")>=0 and msg.find("is not iterable")>=0 and msg.find('pdfinterp.py')>=0:
            print("\n======================\nERRO: erro_extracao na leitura do texto do PDF\n======================\n")
            return True
        return False
    
    # verifica se o tipo de erro é um erro de extração (inconsistência no arquivo PDF)
    @classmethod
    def erro_nao_pdf(cls, msg_erro):
        msg = str(msg_erro).lower()
        if not msg:
            return False
        return msg.find('pdfsyntaxerror')>0 or \
               msg.find('no /root object')>0 or \
               msg.find('is this really a pdf')>0

    # extrai as páginas do PDF ou o texto de um arquivo texto.
    # usa o marcador de páginas que será usado depois para tratar o texto como lista
    # sendo um item da lista = uma página
    # no txt, supõe que a página tenha cerca de 3k caracteres caso não tenha o marcador no próprio texto
    PASTA_TEMP = './TEMP'
    @classmethod
    def extrair_texto_request_pdf(cls, request_file):
        if not os.path.isdir(cls.PASTA_TEMP):
            os.makedirs(cls.PASTA_TEMP)
        file_name_pdf = str(uuid.uuid4())
        if str(request_file.content_type).lower().find('pdf') > 0:
            file_name_pdf = os.path.join(cls.PASTA_TEMP, file_name_pdf) + '_pdf.tmp'
            request_file.save(file_name_pdf)
            paginas = cls.extrair_textos_pdf(file_name_pdf)
            paginas = [f'{_}{cls.__MARCADOR_PAGINA__}' for _ in paginas]
        else:
            file_name_pdf = os.path.join(cls.PASTA_TEMP, file_name_pdf) + '_txt.tmp'
            request_file.save(file_name_pdf)
            paginas = cls.carregar_arquivo(file_name_pdf)
        try:
            os.remove(file_name_pdf)
            cls.limpar_temp()
        except:
            pass
        return paginas

    @classmethod
    def analisar_request_pdf(cls, request, texto_alternativo, chave_file = 'pdf'):
        # no caso de receber um arquivo PDF
        paginas = []
        if chave_file in request.files and request.files[chave_file]:
            request_file = request.files[chave_file]
            print(f'Arquivo recebido: gravando e extraindo páginas - {request_file.mimetype} .....')
            paginas = cls.extrair_texto_request_pdf(request_file)
            print(f'Arquivo recebido: finalizado com {len(paginas)} páginas')
            paginas = [cls.unir_paragrafos_quebrados(_) if _ else [''] for _ in paginas]
            paginas = ['\n'.join(_) for _ in paginas]
            print(f'Arquivo recebido: parágrafos corrigidos')
        else:
            paginas = [str(texto_alternativo)]
        # retorna um marcador de páginas como separador para tratamento de localização nas extrações
        return '\n'.join([str(_) if _ else '' for _ in paginas])

    @classmethod
    def carregar_arquivo(cls, arq):
        tipos = ['utf8', 'ascii', 'latin1']
        linhas = None
        for tp in tipos:
            try:
                with open(arq, encoding=tp) as f:
                    linhas = f.read().splitlines()
                    break
            except UnicodeError:
                continue
        if not linhas:
            with open(arq, encoding='latin1', errors='ignore') as f:
                 linhas = f.read().splitlines()
        return linhas        
        
    @classmethod
    # limpa temporários com mais de 60 minutos
    def limpar_temp(cls):
        extensao = '.tmp'
        for path, _, file_list in os.walk(cls.PASTA_TEMP):      
            for file_name in file_list:
                if file_name.lower().endswith(extensao):
                    file_name = os.path.join(path,file_name)
                    if cls.file_age(file_name) > 60:
                       try:
                           os.remove(file_name)
                       except:
                           pass

    @classmethod
    def file_age(cls, filepath):
        # tempo em minutos
        segundos =time.time() - os.path.getmtime(filepath)
        return round( segundos / 60)

    ABREVIACOES = ['sra?s?', 'exm[ao]s?', 'ns?', 'nos?', 'doc', 'ac', 'publ', 'ex', 'lv', 'vlr?', 'vls?',
                'exmo\(a\)', 'ilmo\(a\)', 'av', 'of', 'min', 'livr?', 'co?ls?', 'univ', 'resp', 'cli', 'lb',
                'dra?s?', '[a-z]+r\(as?\)', 'ed', 'pa?g', 'cod', 'prof', 'op', 'plan', 'edf?', 'func', 'ch',
                'arts?', 'artigs?', 'artg', 'pars?', 'rel', 'tel', 'res', '[a-z]', 'vls?', 'gab', 'bel',
                'ilm[oa]', 'parc', 'proc', 'adv', 'vols?', 'cels?', 'pp', 'ex[ao]', 'eg', 'pl', 'ref',
                'reg', 'f[ilí]s?', 'inc', 'par', 'alin', 'fts', 'publ?', 'ex', 'v. em', 'v.rev',
                'des', 'des\(a\)', 'desemb']

    ABREVIACOES_RGX = re.compile(r'(?:\b{})\.\s*$'.format(r'|\b'.join(ABREVIACOES)), re.IGNORECASE)
    PONTUACAO_FINAL = re.compile(r'([\.\?\!]\s+)')
    PONTUACAO_FINAL_LISTA = {'.','?','!'}
    RE_NUMEROPONTO = re.compile(r'(\d+)\.(?=\d)')
    RE_NAO_LETRAS = re.compile('[^\wá-ú]')
    # recebe uma lista de parágrafos quebrados (normalmente de um PDF)
    # e tenta identificar quais deveriam estar juntos de acordo com o final de
    # cada linha e o início da próxima
    # retorna uma lista de parágrafos
    @classmethod
    def unir_paragrafos_quebrados(cls, texto):
        lista = texto if type(texto) is list else texto.split('\n')
        res = []
        def _final_pontuacao(_t):
            if len(_t.strip()) == 0:
                return False
            return _t.strip()[-1] in cls.PONTUACAO_FINAL_LISTA
        for i, linha in enumerate(lista):
            if i==0:
                res.append(linha)
            elif (not _final_pontuacao(lista[i-1])) or \
                (_final_pontuacao(lista[i-1]) and (cls.ABREVIACOES_RGX.search(lista[i-1]))):
                if len(res) ==0:
                   res =['']
                res[len(res)-1] = res[-1].strip() + ' '+ linha
            else:
                res.append(linha)
        return res

    # dado uma string, verifica se tem marcação de páginas e retorna a lista de páginas
    # ou a própria string se não tiver marcador de páginas
    @classmethod
    def retorna_lista_paginas(cls, texto):
        if texto.find(cls.__MARCADOR_PAGINA__):
            return texto.split(cls.__MARCADOR_PAGINA__)
        return texto
