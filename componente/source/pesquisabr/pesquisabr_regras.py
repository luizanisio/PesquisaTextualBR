# -*- coding: utf-8 -*-
#######################################################################
# Esse código, dicas de uso e outras informações: 
#   -> https://github.com/luizanisio/PesquisaTextualBR
# Luiz Anísio 
# 30/11/2020 - disponibilizado no GitHub  
#######################################################################

from copy import deepcopy
import re
from datetime import datetime

from pesquisabr import PesquisaBR
from pesquisabr.pesquisabr_extracao import UtilExtracaoRe


class RegrasPesquisaBR():
  ''' O retorno contém:
       - retorno = True/False se os critérios foram atendidos no texto analisado
       - erros = mensagem de erro quando os critérios são mal formados
       - tempo = tempo em segundos para o processamento
       (grifar = True)
       - texto_grifado = texto original grifado com os critérios analisados (não disponível nas regras)
       (extrair = True)
       - extracoes = disponível apenas nas regras de regex/like
       (detalhar = True)
       - texto_analise = texto original recebido para avaliação das regras ou critérios
       - texto = texto processado pelo tido de avaliação feita (regex/like/PesquisaBR), em regras é o texto para PesquisaBR
       - texto_regex = no caso de regras, texto processado usado no regex 
       - criterios_analise = critérios originais recebidos para análise
       - criterios = critérios processados pelo tipo de avaliação feita
       - criterios_aon = critérios convertidos para AND/OR/NOT no caso de PesquisaBR
  '''

  def __init__(self, regras = [], print_debug = False):
      self.print_debug = print_debug
      # é necessário unir as regras de cada grupo e, se existir, ordena pela ordem no grupo
      self.regras = self.ordenar_regras(regras)
      #print('Regras ordenadas:')
      #[print(_) for _ in self.regras]

  @classmethod
  def ordenar_regras(self, regras):
      return sorted(regras, key=lambda k:(k.get('grupo',''), k.get('ordem',0)))

  # retorna o critério like, regex ou None se não for nenhum dos dois 
  # e: regex de extração
  # l: like para ser convertido para regex
  # r: regex
  @classmethod
  def regra_like_regex(self, criterios):
      regra_like = None
      regra_regex = None
      if criterios[:2] in {'r:','R:'}:
         regra_regex = criterios[2:]
      elif criterios[:2] in {'e:','E:'}:
         regra_regex = criterios[2:]
      elif criterios[:2] in {'l:','L:'}:
         regra_like = criterios[2:]
         regra_regex = UtilExtracaoRe.like_to_regex(regra_like)
      return regra_like, regra_regex

  # usado para aplicação de critérios simples como a chamada de um serviço
  # aplica a remoção dos critérios de remoção e avalia se usa o PesquisaBR ou critérios Regex ou Like 
  # todo - grifar ser aplicado no texto original - para isso o remover deve retornar o texto original também
  @classmethod
  def aplicar_criterios(self, texto = None, criterios = None, detalhar = False, extrair = True, grifar = False):
      if (not texto) or (not criterios):
         if detalhar:
            return {'retorno': False, 'criterios': '', 'texto': ''}
         return {'retorno': False}
      ini_processamento = datetime.now()
      rpbr = RegrasPesquisaBR()
      texto_limpo = UtilExtracaoRe.processar_texto(texto)
      #print('Texto limpo: ', texto_limpo)
      texto_r, criterios_r, texto_orig_r = rpbr.remover_texto_criterio(texto = texto_limpo, criterios = criterios , texto_original=texto)
      _texto = texto_r if texto_r is not None else texto
      texto_limpo = texto_r if texto_r is not None else texto_limpo 
      texto_original = texto_orig_r if texto_orig_r is not None else texto
      _criterios = criterios_r if criterios_r is not None else str(criterios)
      #print('Texto limpo: ', texto_limpo)
      # regex ou like
      regra_like, regra_regex = self.regra_like_regex(_criterios)
      # verifica se existe o texto processado para regex
      if regra_regex:
         # print('texto_limpo: ', texto_limpo)
         extracoes = UtilExtracaoRe.extrair_regex(texto= texto_original, criterio=regra_regex)
         if type(extracoes) is str:
            res = {'erros': extracoes, 'criterios': regra_regex }
            if detalhar:
               res['criterios_analise'] = criterios
            return self.registrar_tempo_segundos(res, ini_processamento)
         res = {'retorno' : any(extracoes)}
         if extrair:
            res['extracao'] = extracoes
         # grifar não está preparado para dict em regras
         if grifar:
            res['texto_grifado'] = UtilExtracaoRe.grifar_textos(texto_original=texto_original, extracoes=extracoes)
         if detalhar:
            res['criterios'] = regra_regex
            res['texto'] = texto_limpo
            res['criterios_analise'] = criterios
            if regra_like:
               res['criterios_like'] = regra_like
         return self.registrar_tempo_segundos(res, ini_processamento)
      # verifica os critérios no texto
      #print('TEXTO: ', _texto)
      #print('CRITÉRIOS: ', _criterios)
      pb = PesquisaBR(texto=_texto, criterios=_criterios, print_debug=False)
      if pb.erros:
         res = {'retorno': None, 'erros': pb.erros, 'criterios': pb.criterios }
         if detalhar:
            res['criterios_analise'] = criterios
         return self.registrar_tempo_segundos(res, ini_processamento)
      res = {'retorno': pb.retorno()}
      if detalhar:
         if type(pb.tokens_texto) is dict:
            _texto_processado = {k: ' '.join(v) for k, v in pb.tokens_texto.items()}
         elif type(texto) is list:
            _texto_processado = [' '.join(t) for t in pb.tokens_texto]
         else:
            _texto_processado = ' '.join(pb.tokens_texto)
         res['texto'] = _texto_processado
         res['criterios_aon'] = pb.criterios_and_or_not
         res['criterios'] = pb.criterios
         res['criterios_analise'] = criterios
      if grifar:
         #print('TEXTO: ', _texto)
         #print('CRITÉRIOS: ', _criterios)
         if type(_texto) is dict:
            _texto_grifado = {}
            for c, v in _texto.items():
                _texto_grifado[c] = pb.grifar_criterios(v).replace('\n','<br>')
         elif type(_texto) is list:
            _texto_grifado = [pb.grifar_criterios(t).replace('\n','<br>') for t in _texto]
         else:
            _texto_grifado = pb.grifar_criterios(_texto).replace('\n','<br>')
         res['texto_grifado'] = _texto_grifado      
      return self.registrar_tempo_segundos(res, ini_processamento)

  # aplica as regras na ordem dos grupos, cada grupo só é testado até retornar TRUE
  # retorna o texto processado, os rótulos e as extrações (texto, rotulos, extracões), a regra identificada
  # o texto é retornado caso o detalhar seja true, para evitar retorno sem necessidade
  # a regra identificada é incluída no retorno no caso do detalhar=1/True
  # dicionário: {'rotulos','extracoes','texto','regras'}
  # qtd_cabecalho e qtd_rodape serve para indicar que a regra será aplicada apenas no início, fim ou início e fim do texto
  # primeiro_do_grupo = true indica que ao retornar um rótulo do grupo, ignora outras regras do grupo
  #                     false continua aplicando todas as regras do grupo retornando todos os rótulos possíveis
  # 1) remove aspas do texto
  # 2) extrai cabeçalhos e/ou rodapés
  # 3) remove critérios remover(...) do texto
  # processa regex ou regras 
  def aplicar_regras(self, texto = None, primeiro_do_grupo = True, detalhar = False, extrair = False):
      if (not self.regras) or (not texto):
         return {'rotulos':[], 'extracoes': []}
      ini_processamento = datetime.now()
      grupos_ok = []
      retorno_rotulos = []
      retorno_extracoes = []
      retorno_erros = []
      retorno_regras = []
      # cria um dicionário com objetos com texto mapeado para o caso de uso de cabeçahos e rodapés, para não ficar reprocessando o texto o tempo todo
      # caso exista um objeto no dicionário com o texto já processado da mesma forma (mesmo cabeçalho e rodapé), usa ele.
      # terá uma versão do texto para regex ou para regras, com aspas ou sem aspas para cada conjunto cabecalho-rodapé
      pbr = PesquisaBR(texto=texto)
      # caches de texto para análise
      if type(pbr.tokens_texto) is dict:
         texto_processado = {}  
         for c, v in pbr.tokens_texto.items():
             texto_processado[c] = ' '.join(v)
      elif type(texto) is list:
           texto_processado = [' '.join(t) for t in pbr.tokens_texto]
      else:
         texto_processado = ' '.join(pbr.tokens_texto)

      pbrs = {'c0r0': pbr} # objeto com o texto completo - zero cabeçhado e zero rodapé e com possíveis transcrições
      pres = {} # objeto com o texto processado para regex - zero cabeçhado e zero rodapé e com possíveis transcrições
      presorig = {} # objeto com o texto original para extração do regex - zero cabeçhado e zero rodapé e com possíveis transcrições
      if self.print_debug:
         print(f'Testando {len(self.regras)} regras para o texto: "{texto}"  processado "{texto_processado}" ')
      for r in self.regras:
          regra_detalhe = deepcopy(r) if detalhar else {} # para desvincular do objeto e alterar chaves
          grupo = r.get('grupo','')
          # se o grupo já retornou TRUE, ignora ele 
          # se for para retornar apenas o primeiro 
          # se não for para retornar apenas o primeiro, grupos_ok fica vazio
          if (grupo in grupos_ok):
             continue
          regra = r.get('regra')
          rotulo = r.get('rotulo','')
         
          # 1) remoção de aspas - com cache para as próximas regras
          # verifica se existe critério de remoção de aspas e guarda o texto processado sem citações se não foi processado ainda
          remover_aspas = self.RE_REMOVER_ASPAS.search(regra)
          _aspas = '' # usado para completar a chave do dicionário de cache
          if remover_aspas:
             _aspas = '_aspas' # usado para completar a chave do dicionário de cache de obj PesquisaBR
             # limpa o critério de remoção de aspas da regra 
             regra = self.RE_REMOVER_ASPAS.sub(' ', regra).strip()
             # guarda o cache do texto sem aspas se for necessário
             if 'c0r0_aspas' not in pbrs:
                pbr = PesquisaBR(texto = self.remover_texto_aspas(self.padronizar_aspas(texto)))
                pbrs['c0r0_aspas'] = pbr # objeto com o texto sem as aspas

          # regex ou like
          regra_like, regra_regex = self.regra_like_regex(regra)
          # verifica se existe o texto processado para regex ou processa e guarda no cache
          # guarda também o texto para regex sem trechos entre aspas no cache
          chave_cache = ''
          if regra_regex:
             if 'c0r0' not in pres:
                 pres['c0r0'] = UtilExtracaoRe.processar_texto(texto)
                 presorig['c0r0'] = texto
             if remover_aspas and 'c0r0_aspas' not in pres:
                 presorig['c0r0_aspas'] = self.remover_texto_aspas(self.padronizar_aspas(texto))
                 pres['c0r0_aspas'] = UtilExtracaoRe.processar_texto(presorig['c0r0_aspas'])

          # prepara o texto a ser analisado de acordo com o cabeçalho e rodapé definidos
          # guarda o texto para uso posterior em outras regras com o mesmo cabeçalho e rodapé
          qtd_cabecalho = r.get('qtd_cabecalho',0)
          qtd_rodape = r.get('qtd_rodape',0)
          # print(f'c{qtd_cabecalho}r{qtd_rodape}{_aspas} >> Regra: {regra}', f'\n -- texto: {texto_para_analise}" ')
          # com cabeçalho e rodapé, é como se removesse o miolo
          qtd_cabecalho = max(0, qtd_cabecalho)
          qtd_rodape = max(0, qtd_rodape)
          chave_cache = f'c{qtd_cabecalho}r{qtd_rodape}{_aspas}'
          # verifica se tem recorte e o tipo de processamento
          # verifica se o recorte de cabeçalho e rodapé já está no cache ou se precisa criar o cache
          # cria o cache para regex limpo e para extração (raw)
          if regra_regex and chave_cache not in pres:
             _texto = pres[f'c0r0{_aspas}'] 
             pres[chave_cache] = PesquisaBR.recorte_texto(_texto, qtd_cabecalho, qtd_rodape)
             _texto = presorig[f'c0r0{_aspas}'] 
             presorig[chave_cache] = PesquisaBR.recorte_texto(_texto, qtd_cabecalho, qtd_rodape)
          elif (not regra_regex) and chave_cache not in pbrs:
             _texto = pbrs[f'c0r0{_aspas}'].texto
             pbrs[chave_cache] = PesquisaBR(texto = PesquisaBR.recorte_texto(_texto, qtd_cabecalho, qtd_rodape))
          # print('CHAVE CACHE: ', chave_cache)
          # se a regra está vazia, ignora ela
          if (not regra) or (rotulo in retorno_rotulos):
             continue
          regra_ok = False
          # critério REGEX
          if regra_regex:
             texto_para_analise = pres[chave_cache]
             texto_original = presorig[chave_cache]
             #print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
             #print('xxx RÓTULO: ', r.get('rotulo'))
             #print('xxx TEXTO ANÁLISE: ', texto_para_analise)
             #print('xxx TEXTO ORIGINAL: ', texto_original)
             #print('xxx REGRA: ', regra_regex)
             _texto_com_remover, _regra_com_remover, _texto_original_com_remover = self.remover_texto_criterio(texto=texto_para_analise, criterios=regra_regex, texto_original=texto_original)
             texto_para_analise = _texto_com_remover if _texto_com_remover is not None else texto_para_analise
             texto_original = _texto_original_com_remover if _texto_original_com_remover is not None else texto_original
             regra_regex = _regra_com_remover if _regra_com_remover is not None else regra_regex
             #print('xxx TEXTO ANÁLISE: ', texto_para_analise)
             #print('xxx TEXTO ORIGINAL: ', texto_original)
             #print('xxx REGRA FINAL   : ', regra_regex)
             #print('Critério removido : ', _regra_com_remover )
             retorno = UtilExtracaoRe.extrair_regex(texto= texto_para_analise, criterio=regra_regex, texto_original=texto_original)
             if type(retorno) is str:
                retorno_erros.append(retorno)
                retorno = [] 
             regra_ok = any(retorno)
             if extrair:
                # no detalhamento, inclui a extração na regra que a gerou
                if detalhar:
                   regra_detalhe['extracoes'] = retorno
                else:
                   retorno_extracoes.extend(retorno)
             if detalhar:
                regra_detalhe['criterios'] = regra_like or regra_regex
                regra_detalhe['texto'] = texto_para_analise
          # critério textual
          else:
            # atualiza o critério para o objeto de pesquisa que já processou o texto
            # o critério muda, mas o texto é o mesmo - aproveita o mapa que está pronto
            # caso exista remoção, é necessário ignorar o cache e usar o texto original com a limpeza básica
            _pbr = pbrs[chave_cache]
            #print('REGRA PESQUISABR - rótulo: ', r.get('rotulo'), ' chave_cache: ', chave_cache) 
            #print('REGRA PESQUISABR - regra:  ', regra)
            #print('REGRA PESQUISABR - texto:  ', _pbr.texto)
            texto_para_analise = _pbr.texto
            _texto_com_remover, _regra_com_remover, _ = self.remover_texto_criterio(texto=texto_para_analise, criterios=regra)
            texto_para_analise = _texto_com_remover if _texto_com_remover is not None else texto_para_analise
            # _texto_com_remover só retorna algo se existe critério de remoção na regra
            # se não tiver texto processado com remoção, segue usando o texto original processado
            if _texto_com_remover is not None:
              # a remoção exige um novo objeto de pesquisa que não é reaproveitado pois a variação pode ser grande
              # a única remoção reaproveitada é a de aspas, pois pode ser igual em várias regras
              if self.print_debug:
                 print(f'Removendo trecho - texto final:"{_texto_com_remover}" - critérios: "{_regra_com_remover}"')
              _pbr = PesquisaBR(texto=texto_para_analise)
              texto_para_analise = _pbr.texto
              regra = _regra_com_remover
            # registra no objeto novo ou do cache o critério de pesquisa
            _pbr.novo_criterio(regra)
            if _pbr.erros:
                retorno_erros.append(_pbr.erros)
            if self.print_debug:
               print(f'Testando grupo: [{grupo}] com rótulo: [{rotulo}] e regra: {regra}')
               _pbr.print_resumo()
            regra_ok = _pbr.retorno()
            if detalhar:
               regra_detalhe['criterios'] = _pbr.criterios
               regra_detalhe['criterios_aon'] = _pbr.criterios_and_or_not
               regra_detalhe['texto'] = texto_para_analise

          # com a regra ok, registra o rótulo para retorno
          if regra_ok:
             # verifica se controla apenas um rótulo por grupo (padrão)             
             if primeiro_do_grupo:
                 # indica que o grupo já foi retornado, não retornando outras regras do grupo
                 grupos_ok.append(grupo)
             # inclui o rótulo no retorno
             retorno_rotulos.append(rotulo)
             # verifica se é retorno detalhado e inclui a regra que incluiu o rótulo no retorno
             if detalhar: 
                 retorno_regras.append(regra_detalhe)
      # finalizando o retorno
      res = {'rotulos':retorno_rotulos}
      if any(retorno_erros):
         res['erros'] = retorno_erros
      # no detalhar, a extração fica dentro das regras
      if extrair and not detalhar:
         res['extracoes'] = retorno_extracoes
      if not detalhar:
         return self.registrar_tempo_segundos(res, ini_processamento)
      # detalhando
      res['texto'] = texto_processado
      if 'c0r0' in pres:
         res['texto_regex'] = pres['c0r0']
      res['texto_analise'] = texto
      res['regras'] = retorno_regras
      res['qtd_regras'] = len(self.regras)
      self.registrar_tempo_segundos(res, ini_processamento)
      return res

  @classmethod
  def registrar_tempo_segundos(self, dados, ini_processamento):
      dados['tempo'] = round((datetime.now()- ini_processamento).total_seconds(), 3)
      return dados

  @classmethod
  def tempo_segundos(self, ini_processamento):
      return round((datetime.now()- ini_processamento).total_seconds(), 3)

  # identifica no critério operadores de remoção de texto
  # pode-se usar:
  #      remover(um texto qualquer)
  #      remover(aspas) - remove textos entre aspas
  # assume-se que o texto já está pré-processado e o conteúdo das aspas já foi removido
  # pois o conteúdo das aspas deve ser removido antes do pré-processamento do texto já que só tokens são 
  # mantidos após o processamento
  # Como usar o operador remover(texto)
  # todo o texto dentro dos parênteses serão removidos do texto processado
  # - podem ser usados curingas no trecho de remoção, são eles:
  # - $ ou * - de 0 a 100 caracteres quaisquer
  # - ? - um caractere de letra ou número opcional
  # - & - um caractere de letra ou número obrigatório
  # - # - um a 10 caracteres que não sejam letra nem número (pontuação, início ou final de texto, espaço, etc)
  # - *# - caracteres até um símbolo (pontuação, início ou final de texto, espaço, etc)
  # - *## - caracteres até uma quebra de linha
  # - % - aspas, parênteses, chaves ou colchetes (citações/explicações em geral)
  # - " - aspas normal
  # Exemplos:
  # - remover(juizado*grau) >> remove juizado[até 100 caracteres quaisquer]grau
  # - remover(%**%) >> remove o que estiver entre parênteses, aspas, colchetes ou chaves (até 200 caracteres - 100 para cada *)
  # - remover("*") >> remove o que estiver entre aspas até 100 caracteres entre a abertura e o fechamento
  # - remover(#artigo&#) >> remove artigo seguido de uma letra ou número com algum símbolo antes e depois (pontuação, espaço, etc) - exemplo do que seria removido: artigos, artigo1, artigo 
  #RE_REMOVER = re.compile(r'remover\([^\)]*\)', flags=re.IGNORECASE)
  RE_REMOVER = re.compile(r'\bremover\([^\)]*\)|\brecortar\([^\)]*\)', flags=re.IGNORECASE)
  RE_REMOVER_ASPAS = re.compile(r'remover\(\s*aspas\s*\)', flags=re.IGNORECASE)
  RE_REMOVER_ENTRE_ASPAS = re.compile('("[^"]*")')
  RE_ASPAS_PADRONIZAR = re.compile(r"“|”|'(?=\W)|(?<=\W)'|'(?=$)|(?<=^)'")
  RE_ASPAS = re.compile(r'"')
  @classmethod
  def remover_texto_criterio(self,  texto: str ='', criterios: str = '', texto_original = ''):
      # se o texto for um dict de {'campo': texto}
      # retorna cada chave com o valor processado
      if type(texto) is dict:
         _textos = dict({})
         _originais = dict({})
         _texto_original = dict({}) if (not texto_original) or type(texto_original) is str else texto_original
         for c, t in texto.items():
            _textos[c], _criterios, _originais[c] = self.remover_texto_criterio(texto = t, criterios = criterios, texto_original=_texto_original.get(c,''))
            _textos[c] = _textos[c].strip() if _textos[c] is not None else None
            _originais[c] = _originais[c].strip() if _originais[c] is not None else None
            # não tendo critérios de remoção, já retorna o padrão None
            if _criterios is None:
               return None, None, None
         # se a lista for vazia, avalia só os critérios
         if len(texto.keys()) == 0:
            _texto, _criterios, _original = self.remover_texto_criterio(texto = '', criterios = criterios, texto_original='')
            #print('Texto [] vazio: ', criterios, _criterios)
            if _criterios is None:
               return None, None, None
         return _textos, _criterios, _originais
      if type(texto) is list:
         _textos = []
         _originais = []
         _texto_original = [] if (not texto_original) or type(texto_original) is str else texto_original
         for i, t in enumerate(texto):
            _original = _texto_original[i] if any(_texto_original) else ''
            _texto, _criterios, _original = self.remover_texto_criterio(texto = t, criterios = criterios, texto_original=_original)
            _texto = _texto.strip() if _texto is not None else None
            _original = _original.strip() if _original is not None else None
            _textos.append(_texto)
            _originais.append(_original)
            # não tendo critérios de remoção, já retorna o padrão None
            if _criterios is None:
               return None, None, None
         # se a lista for vazia, avalia só os critérios
         if len(texto) == 0:
            _texto, _criterios, _original = self.remover_texto_criterio(texto = '', criterios = criterios, texto_original='')
            #print('Texto [] vazio: ', criterios, _criterios)
            if _criterios is None:
               return None, None, None
         return _textos, _criterios, _originais

      remocoes = self.RE_REMOVER.findall(criterios)
      if len(remocoes) == 0:
         #print('### SEM REMOÇÕES ###')
         return None, None, None
      # não tem texto, retorna os critérios limpos
      if not texto:
         #print('### SEM TEXTO ###')
         return '', self.RE_REMOVER.sub(' ',criterios).strip(), ''
      # padroniza as aspas do texto
      _texto = self.padronizar_aspas(texto)
      _texto_original = self.padronizar_aspas(texto_original)
      # remove as aspas do texto se solicitado - o ideal é já vir removido e o texto deveria estar
      # pré-processado, ou seja, nem tem mais aspas nos tokens
      # mas para permitir usos além do analisador padrão de regras, ele pode remover aspas se 
      # receber esse comando no critério analisado 
      if self.RE_REMOVER_ASPAS.search(criterios):      
         _texto, _criterios = self.remover_texto_criterio_aspas(_texto, criterios)
         _texto_original, _ = self.remover_texto_criterio_aspas(_texto_original, criterios)
         #print('ORIGINAL  : ', _texto_original)
         #print('PROCESSADO: ', _texto)
      else:
         _criterios = str(criterios)
         #print('## CRITÉRIOS SEM REMOÇÃO DE ASPAS: ', criterios)
        
      _pbr = PesquisaBR()
      # recortes de texto. Não tendo recortes, vale o texto todo.
      recortes = []
      originais = []
      recortou = False
      #print('Texto: ', texto)
      #print('Remoções: ', remocoes)
      for trecho in remocoes:
          if trecho[0:8].lower() == 'recortar':
             recortou = True
             _iniciofim = _pbr.processar_texto(trecho[9:-1])
             inicio, fim = f'{_iniciofim};'.split(';')[:2]
             #print(f'Recortar: |{inicio};{fim}|')
             _recorte, _original = self.recortar_texto(_texto, inicio, fim, _texto_original)
             if _recorte is not None:
                recortes.append(_recorte)
                originais.append(_original)
      if recortou:
         _texto = '\n'.join(recortes)
         _texto_original = '\n'.join(originais)
         if (not _texto) or (not _texto.replace('\n','')):
            _texto = ''
            _texto_original = ''
         #print(f'Texto recortado: {_texto}')

      # removeu aspas e tem critérios de remoção, processa os termos sem curingas
      # remocoes é a lista de critérios de remoções encontrados - um item para cada remover(...)
      for remover in remocoes:
          if remover[0:8].lower() == 'recortar':
             continue
          # [8:-1] para sobrar apenas o que está dentro do remover(...)
          #print('remover raw: ', remover[8:-1])
          #print('remover processado: ', _pbr.processar_texto(remover[8:-1]))
          remover = _pbr.processar_texto( self.padronizar_aspas(remover[8:-1]))
          #print('remover: ', remover)
          # com os tokens limpos, faz a preparação do REGEX de substituição com os curingas
          if remover:
            #print('raw remover: ', remover)
            re_remover = self.preparar_regex_remocao(remover)
            #print('regex remover: ', re_remover)
            #print('texto remover: ', _texto)
            _novo = ''
            _novo_original = ''
            _p = 0
            for m in re_remover.finditer(_texto):
                  ini = m.start()
                  fim = m.end()
                  _novo += f'{_texto[_p:ini]} '
                  _novo_original += f'{_texto_original[_p:ini]} '
                  _p = fim
            _novo += _texto[_p:]
            _novo_original += _texto_original[_p:]
            _texto = _novo
            _texto_original = _novo_original
            #_texto = re_remover.sub(' ',_texto)
            #print('texto removido: ', _texto)
      # retira os operadores de remoção dos critérios remover(...)
      _criterios = self.RE_REMOVER.sub(' ',_criterios)
      return _texto.strip(), _criterios.strip(), _texto_original

  # retorna o texto e o critério com o trecho entre aspas limpo se for solicitado nos critérios
  # ex. de critérios:  casa ADJ2 papel remover(aspas)
  # retorna o texto sem o conteúdo entre as aspas e o critério sem remover(aspas)
  # espera-se receber o texto com as aspas padronizadas para aspas duplas "
  @classmethod
  def remover_texto_criterio_aspas(self,  texto: str ='', criterios: str = ''):
      if type(texto) is dict:
         return {k: self.remover_texto_criterio_aspas(v) for k, v in texto.items()}
      elif type(texto) is list:
         return [self.remover_texto_criterio_aspas(v) for v in texto]
      if self.RE_REMOVER_ASPAS.search(criterios):
         # só faz a remoção se as aspas estiverem em pares
         return self.remover_texto_aspas(texto).strip(), \
                self.RE_REMOVER_ASPAS.sub(' ',str(criterios)).strip()
      return None,None

  # verifica se as aspas estão em número par, em número ímpar a remoção não deve ocorrer por
  # segurança para evitar que falhas no texto removam trechos importantes
  # se não tiver aspas, retorna false também
  @classmethod
  def aspas_em_pares(self, texto):
      aspas = self.RE_ASPAS.findall(texto)
      return any(aspas) and (len(aspas) % 2 == 0)

  # retorna o texto sem o trecho entre aspas
  # considera-se que o texto chegou aqui com as aspas padronizadas
  @classmethod
  def remover_texto_aspas(self,  texto: str =''):
      if type(texto) is dict:
         return {k: self.remover_texto_aspas(v) for k, v in texto.items()}
      elif type(texto) is list:
         return [self.remover_texto_aspas(v) for v in texto]
      if self.aspas_em_pares(texto):
         return self.RE_REMOVER_ENTRE_ASPAS.sub(' ',texto.strip())
      return texto

  # retorna vazio caso não tenha curingas pois não precisa de regex
  RE_CURINGAS_REMOCAO = re.compile(r'[\?$%&#*]')
  RE_CURINGAS_REPETIDOS = re.compile(r'\*{11,}')
  @classmethod
  def preparar_regex_remocao(self, remover: str = ''):
      if not remover:
          return ''
      #if not self.RE_CURINGAS_REMOCAO.search(remover):
      #    return remover
      remover = str(remover)
      # prepara o regex de remoção  substituindo ? por . 
      # algumas premissas precisam ser analisadas \ e | não podem existir e símbolos do regex serão convertidos para \\ 
      # serão válidos os curingas ?, %, &, #, * ou $ 
      _rgx_remover = remover.replace('\\',' ') # caractere inválido para análise 
      _rgx_remover = _rgx_remover.replace('|',' ') # caractere inválido para análise 
      _rgx_remover = _rgx_remover.replace('$','*') # padroniza para * 
      _rgx_remover = _rgx_remover.replace('[',r'\[').replace(']',r'\]')
      _rgx_remover = _rgx_remover.replace('.',r'\.').replace('-','\-')
      _rgx_remover = _rgx_remover.replace('^',r'\^').replace('(',r'\(')
      # aspas com asterisco de 1 a 20x funciona
      # mais que 20x* ele substitui por 20 * para não dar erro: Catastrophic backtracking
      _rgx_remover = self.RE_CURINGAS_REPETIDOS.sub('**********', _rgx_remover)
      for _ in range(21,1,-1):
          _asteriscos_ = '*' * _
          _rgx_remover = _rgx_remover.replace(f'"{_asteriscos_}"',r'"[^"]{1,100}"'.replace(',1',f',{_}'))
          _rgx_remover = _rgx_remover.replace(f'{_asteriscos_}',r'[^"]{1,100}'.replace(',1',f',{_}'))
      # citações com asterisco antes - verifica aspas, parênteses, colchetes e chaves
      _rgx_remover = _rgx_remover.replace('*%',r'[^"]{1,100}["\[\]\(\){}\|]')
      # citações
      _rgx_remover = _rgx_remover.replace('%',r'["\[\]\(\){}\|]')
      # curinga composto *## significa até o fim da linha
      _rgx_remover = _rgx_remover.replace('*##',r'.*[^\r\n]')
      # curinga composto *# significa até o fim da palavra 
      _rgx_remover = _rgx_remover.replace('*#','[a-z0-9]*[^a-z0-9]{1,10}')
      # curingas normais 
      _rgx_remover = _rgx_remover.replace('*','.{0,100}')
      _rgx_remover = _rgx_remover.replace('?','[a-z0-9]?')
      _rgx_remover = _rgx_remover.replace('&','[a-z0-9]')
      _rgx_remover = _rgx_remover.replace('#','[^a-z0-9]{1,10}')
      # print('REMOVER: ', _rgx_remover)
      return re.compile(_rgx_remover)

  # caso não tenha início e fim, volta o texto completo
  # caso tenha apenas início, volta o texto até o final
  # caso tenha penas o fim, volta o texto até o fim
  # só serão aceitos caracteres a-z0-9 ou os símbolos [._-] do regex. 
  # o símbolo ? pode ser usado ao final do delimitador indicando que ele é opcional
  RE_LIMPAR_DELIMITADORES_RECORTE = re.compile(r'[^a-z0-9\.\_\-\#\$ ]')
  @classmethod 
  def recortar_texto(cls, texto, inicio, fim, texto_original, recursivo = False):
      if not texto:
         return '',''
      if not f'{inicio}{fim}':
         return texto, texto_original
      _proximo_texto = None
      _proximo_original = None
      # >>>  "#" é o "\n" e "$"" é fim de palavra "\b"
      # uso do ¨ para não ocorrer dupla substituição
      _inicio = str(inicio) if str(inicio)[-1:] != '?' else str(inicio)[:-1]
      _fim = str(fim) if str(fim)[-1:] != '?' else str(fim)[:-1]
      _ini_opcional = str(inicio)[-1:] == '?' 
      _fim_opcional = str(fim)[-1:] == '?' 
      # limpa caracteres estranhos
      _inicio = cls.RE_LIMPAR_DELIMITADORES_RECORTE.sub('', _inicio)
      _fim = cls.RE_LIMPAR_DELIMITADORES_RECORTE.sub('', _fim)
      # converte para regex
      _inicio = _inicio.replace('#', r'(^|¨|\n|\r)').replace('$',r'(\b|¨|^)').replace('¨','$')
      _fim = _fim.replace('#', r'(^|¨|\n|\r)').replace('$',r'(\b|¨|^)').replace('¨','$')
      _novo = texto
      _novo_original = texto_original or texto
      _tem_ini, _tem_fim = False, False
      #print(f'Início: |{_inicio}|', '\t', f'Fim: |{_fim}|', _ini_opcional, _fim_opcional)
      # início e fim podem ser opcionais colocando ? no final do termo
      if inicio:
         _search = re.search(_inicio, _novo, flags=re.IGNORECASE)
         if _search:
            _novo = _novo[_search.start():]
            _novo_original = _novo_original[_search.start():]
            _tem_ini = True
         elif _ini_opcional:
            # início opcional, não corta
            #print('Início opcional: ', _inicio)
            pass
         else:
            #print('Início não encontrado: ', _inicio)
            _novo = ''
            _novo_original = ''
      # se tem fim, tem que achar o fim
      if fim:
         _search = re.search(_fim, _novo, flags=re.IGNORECASE)
         if _search:
            _proximo_texto = _novo[_search.end():]
            _proximo_original = _novo_original[_search.end():]
            _novo = _novo[:_search.end()]
            _novo_original = _novo_original[:_search.end()]
            _tem_fim = True
         elif _fim_opcional:
            # fim opcional, não corta
            #print('Fim opcional: ', _fim)
            pass
         else:
            _novo = ''
            _novo_original = ''
      # no caso de ser opcional o início e o final, na recursividade não pode ser mais opcional os dois juntos
      # pois traria o texto todo no caso de não ter mais delimitadores no resto do texto
      # então se não encontrar início ou fim na recursividade opcional, retorna vazio
      if recursivo and (not _tem_ini) and (not _tem_fim):
         return '',''
      # se achou, verifica se tem mais após o final (se for apenas início ou apenas fim, acaba na primeira passada)
      if _proximo_texto and inicio and fim:
         #print('Próximo texto: ', _proximo_texto.replace('\n','<br>'))
         _proximo_texto, _proximo_original = cls.recortar_texto(_proximo_texto, inicio, fim, _proximo_original, True)
         if _proximo_texto:
            return f'{_novo}\n{_proximo_texto}', f'{_novo_original}\n{_proximo_original}'
      #print('Retorno: ', _novo, _novo_original)
      return _novo, _novo_original

  # usado para retornar os trechos de critérios de remoção para análise ou apresentação na tela
  @classmethod
  def retornar_criterios_remocao(self, criterios):
      remocoes = self.RE_REMOVER.findall(criterios)
      return ' '.join(remocoes)

  @classmethod
  def padronizar_aspas(self, texto):
      if type(texto) is dict:
         return {k: self.padronizar_aspas(v) for k, v in texto.items()}
      elif type(texto) is list:
         return [self.padronizar_aspas(v) for v in texto]
      return self.RE_ASPAS_PADRONIZAR.sub('"',texto)
      #return str(texto).replace('“','"').replace('”','"').replace("'",'"') #pode causar problemas com apóstrofos

################################################################################
################################################################################
if __name__ == "__main__":
    print('##############################################')
    print('>> TESTE BÁSICOS - REGRAS ')
    pb=RegrasPesquisaBR()
    texto = 'Teste de texto removido e com trecho entre aspas "esse trecho tem que sair" ok'
    criterios = 'casa adj2 papel remover(removidos) remover(aspas) remover("*******")'
    print(pb.remover_texto_criterio(texto = texto, criterios = criterios))

    regras = ['']
