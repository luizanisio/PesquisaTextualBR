# -*- coding: utf-8 -*-
#######################################################################
# Código complementar à classe PesquisaBR para pesquisas por regex
# Esse código, dicas de uso e outras informações: 
#   -> https://github.com/luizanisio/PesquisaTextualBR
# Luiz Anísio 
# 30/11/2020 - disponibilizado no GitHub  
#######################################################################

from enum import Flag
import re
import copy
from unicodedata import normalize

from regex import F

class UtilExtracaoRe():
    # recebe um critério regex compilado ou não e retorna as posições extraídas e o texto extraído
    # em um dicionário {'inicio': int, 'fim': int, 'texto': str}
    # prontos - são substituições prontas de regex conhecidos para facilitar a construção
    #   Ex.: CPF-OCR: \b[0-9ilo]{3}[\.,;]?[0-9ilo]{3}[\.,;]?[0-9ilo]{3}\-?[0-9ilo]{2}\b
    #        CPF: \b\d{3}\.?\d{3}\.?\d{3}\-?\d{2}\b
    #        CNPJ: \b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b
    # Como usar: colocar no trecho do regex <CPF> que será substituído por (regex do cpf)
    PRONTOS = {'CPF' : r'\b\d{3}\.?\d{3}\.?\d{3}\-?\d{2}\b',
               'CPF-OCR': r'\b[0-9ilo]{3}[\.,;]?[0-9ilo]{3}[\.,;]?[0-9ilo]{3}\-?[0-9ilo]{2}\b',
               'CNPJ' : r'\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b',
               'CNPJ-OCR' : r'\b[0-9ilo]{2}[\.,;]?[0-9ilo]{3}[\.,;]?[0-9ilo]{3}[\/|/]?[0-9ilo]{4}-?[0-9ilo]{2}\b',
               'FIMTERMO' : r'(\w*)',
               'TERMO' : r'(\W+\w*)'}
    @classmethod
    def extrair_regex(cls, texto, criterio, texto_original=None):
        try:
            if type(criterio) is str:
               criterio_regex = cls.like_to_regex(cls.preparar_regex_pronto(criterio), verificar_criterio = True)
               # remove acentos do critério pois o texto não terá acentos
               criterio_regex = cls.RE_UNICODE.sub('', normalize("NFD", str(criterio_regex) ))
               rx = re.compile(criterio_regex, flags= re.IGNORECASE)
               #print(f'Critério: |{criterio}| para |{rx.pattern}|')
            else:
               criterio_regex = criterio.pattern
               rx = criterio

        except re.error as msg:
            return f'ERRO "{msg}" em: {criterio_regex}'        
        res = []
        # para ser mais rápido, pode receber o texto pré-processado (lower e sem acentos)
        if texto_original:
            # tendo o objeto texto_original, assume-se que ele seque o mesmo tipo do texto (dict ou list)
            _texto_original = cls.quebra_para_n(texto_original)
            _texto = cls.quebra_para_n(texto)
        elif type(texto) is list:
            _texto_original = [str(cls.quebra_para_n(t)) for t in texto]
            _texto = [cls.processar_texto(t.lower()) for t in texto]
        elif type(texto) is dict:
            _texto_original = {c: str(cls.quebra_para_n(t)) for c, t in texto.items() }
            _texto = {c: cls.processar_texto(t.lower()) for c, t in texto.items()}
        else:
            _texto_original = str(cls.quebra_para_n(texto))
            _texto = cls.processar_texto(cls.quebra_para_n(texto.lower()))
        #print(_texto)
        #print(_texto_original)
        #print('type: ', type(_texto))
        # foi recebida uma lista de texto, considera-se que cada uma é uma página
        if type(_texto) is list:
            pagina = 1
            for _txt, _txto in zip(_texto, _texto_original):
                _res = cls.aplicar_regex(_txt, _txto, regex=rx)
                for r in _res:
                    r['pagina'] = pagina
                    res.append(r)
                pagina += 1
            return res
        # foi recebido um dict de texto, considera-se que cada chave é um texto
        if type(_texto) is dict:
            for c, _txt in _texto.items():
                _res = cls.aplicar_regex(_txt, _texto_original.get(c,_txt), regex=rx)
                for r in _res:
                    r['chave'] = c
                    res.append(r)
            return res
        return cls.aplicar_regex(_texto, _texto_original, regex=rx)

    @classmethod
    def quebra_para_n(cls, texto):
        if type(texto) is dict:
            return {c: cls.quebra_para_n(v) for c,v in texto.items()}
        elif type(texto) is list:
            return [cls.quebra_para_n(t) for t in texto]
        return texto.replace('<br>','\n').replace('\r','\n')

    # aplicação do regex no texto
    @classmethod
    def aplicar_regex(cls, _txt, _txto, regex):
        res = []
        for m in regex.finditer(_txt):
            ini = m.start()
            fim = m.end()
            trecho = _txto[ini:fim]
            d = {'inicio':ini, 'fim':fim, 'texto':trecho}
            res.append(d)
        return res

    @classmethod
    def grifar_texto(cls, texto_original, extracoes, tag_ini = '<mark>', tag_fim='</mark>', quebra = '<br>'):
        if not any(extracoes):
            return texto_original.replace('\n', str(quebra)) if quebra else texto_original
        texto_novo = ''
        cursor = 0
        _texto_original = cls.quebra_para_n(texto_original)
        for ex in extracoes:
            ini = ex.get('inicio',0)
            fim = ex.get('fim',0)
            texto_novo += _texto_original[cursor:ini]
            texto_novo += f'{tag_ini}{_texto_original[ini:fim]}{tag_fim}'
            cursor = fim
        texto_novo += _texto_original[cursor:]
        return texto_novo.replace('\n', str(quebra)) if quebra else texto_novo

    # recebe um dict de textos ou uma lista de textos
    @classmethod
    def grifar_textos(cls, texto_original, extracoes, tag_ini = '<mark>', tag_fim='</mark>', quebra = '<br>'):
        # no dict, as extrações conterão a "chave" do texto extraído
        if type(texto_original) is dict:
            res = {}
            for chave, texto in texto_original.items():
                _extracoes = [e for e in extracoes if e.get('chave','') == chave]
                res[chave] = cls.grifar_texto(texto, _extracoes, tag_ini, tag_fim, quebra)
            return res 
        # na lista, as extrações conterão a "pagina" (i+1) do texto 
        if type(texto_original) is list:
            res = []
            for i, texto in enumerate(texto_original):
                _extracoes = [e for e in extracoes if e.get('pagina','') == i+1]
                res.append( cls.grifar_texto(texto, _extracoes, tag_ini, tag_fim, quebra) )
            return res 
        # de outra forma, grifa o texto com todas as extrações
        return cls.grifar_texto(str(texto_original), extracoes, tag_ini, tag_fim, quebra)

    # substitui os marcadores de regex prontos pelos seus grupos de reges
    @classmethod
    def preparar_regex_pronto(cls, texto_regex):
        res = str(texto_regex)
        for c, rg in cls.PRONTOS.items():
            res = res.replace(f'<{c}>', f'({rg})')
        #print('Prontos: ', len(cls.PRONTOS))
        #print('- regex: ', texto_regex)
        #print('- final: ', res)
        return res

    # testa o regex ou um conjunto de regex
    @classmethod
    def testar_regex(cls, texto_regex):
        if type(texto_regex) is list:
           res = []
           # roda os testes para cada regex
           for _texto in texto_regex:
               txt = cls.testar_regex( texto_regex=_texto)
               if txt:
                  return txt
           return ''
        try:
            re.compile(texto_regex)
        except re.error as msg:
            return f'ERRO "{msg}" em: {texto_regex}'
        return ''

    # recebe uma lista de critérios onde cada critério é um dicionário com o regex e outros metadados
    # retorna o dicionário sem o regex com o texto extraído para cada aplicação do regex com 
    # o início e fim da extração do texto e os metadados do regex que resultaram na extração
    # exemplo: criterios = [{'re' : re.compile(r'testes?'), 'tipo':'TESTE', 'subtipo':'a'}, {'re' : r'\sextra.*o\s', 'tipo':'EXTRA', 'subtipo':'b'}]
    # considera-se que cada item da lista "texto" é uma página
    @classmethod
    def extrair_regex_tipo(cls, texto, criterios, chave_regex='re',chaves_removidas_retorno = []):
        if type(texto) is list:
           res = []
           # roda os critérios para cada item e inclui o número da página
           pagina = 1
           for _texto in texto:
               ex = cls.extrair_regex_tipo( texto=_texto, 
                                               criterios=criterios,
                                               chave_regex=chave_regex, 
                                               chaves_removidas_retorno=chaves_removidas_retorno)
               # retorno string, ocorreu erro
               if type(ex) is str:
                   return ex
               for i in range(len(ex)):
                   ex[i]['pagina'] = pagina
               pagina += 1
               res.extend(ex)
           return res

        res = []
        _texto = cls.processar_texto(texto.lower())
        for r in criterios:
            _ = cls.extrair_regex(_texto, r[chave_regex], 
                                    texto_original=str(texto))
            for i in range(len(_)):
                _dados = copy.deepcopy(r)
                _dados.pop(chave_regex,None)
                if chaves_removidas_retorno != None:
                   [_dados.pop(c,None) for c in chaves_removidas_retorno]
                _[i].update(_dados)
            res.extend(_)
        res.sort(key=lambda x:x['inicio'])
        return res

    ################################################################################
    # faz um pré processamento do texto para remover acentos e padronizar quebra de linha
    ################################################################################
    RE_UNICODE = re.compile("[\u0300-\u036f]")
    @classmethod
    def processar_texto(cls, texto):
        # se o texto for um dict de {'campo': texto}
        # retorna cada chave com o valor processado
        if type(texto) is dict:
           _textos = dict({})
           for c, t in texto.items():
               _textos[c] = cls.processar_texto(texto = str(t))
           return _textos
        if type(texto) is list:
           return [cls.processar_texto(texto = str(t)) for t in texto]
        _res = cls.RE_UNICODE.sub('', normalize("NFD", str(texto) )).lower()
        return cls.quebra_para_n(_res) # cls.RE_UNICODE.sub('', normalize("NFD", str(texto) )).lower().replace('<br>','\n').replace('\r','\n')

    # converte um critério usando like para uma expressão regular
    # curingas do like: % e _ 
    # o like considera todo o texto, então não basta ter uma substring se o curinga % não estiver no início e fim
    # teste termo1 teste >> like termo1 >> é false
    # teste termo1 teste >> like %termo1% >> é true
    # verificar_criterio >> converte para like apenas se iniciar com L: ou l:
    @classmethod
    def like_to_regex(cls, criterio_like, verificar_criterio = False):
        if not criterio_like:
            return ''
        if criterio_like[:2].upper() == 'L:':
           criterio_like = criterio_like[2:] 
        elif verificar_criterio:
           #retorna o critério sem modificação se não for verificado o pedido L: 
           return criterio_like
        if criterio_like[:2].upper() == 'L:':
           criterio_like = criterio_like[2:] 
        res = criterio_like.replace('%','.*').replace('_','.')
        return f'^{res}$'

    ################################################################################
    @classmethod
    def testes(self):
        texto = 'teste de extração de critérios com outros testes teste CPF: 123.123.123-12 CNPJ: 03.778.130/0001-11'
        criterios = [{'re' : r'\btestes?\b', 'tipo':'TESTE', 'subtipo':'a'},
                    {'re' : re.compile(r'\b((testes?).*(de)\b)'), 'tipo':'GRUPOS', 'subtipo':'c'},
                    {'re' : r'\bextra.*o\b', 'tipo':'EXTRA', 'subtipo':'b'},
                    {'re' : r'\b(testes?)\s(de)\s(extra.*o)\b', 'tipo':'TESTE_EXTRA', 'subtipo':'a'},
                    {'re' : r'<CPF-OCR>|<CNPJ-OCR>', 'tipo':'CPF_CNPJ', 'subtipo':'x'},
                    {'re' : r'L:%extra__o%', 'tipo':'LIKE', 'subtipo':'x'}]
        res = UtilExtracaoRe.extrair_regex_tipo(texto, criterios, chave_regex='re')
        [print(_) for _ in res]
        print('Texto grifado: ', UtilExtracaoRe.grifar_texto(texto_original = texto, extracoes= res, tag_ini= '<mark>', tag_fim= '</mark>\n') )

if __name__ == "__main__":
    UtilExtracaoRe.testes()
