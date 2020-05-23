import re
from unicodedata import normalize
import copy as cp

############################################
############################################
class PesquisaBR():
  RE_QUEBRA = re.compile('(<\s*\/?\s*[bB][rR]\s*\/?\s*>)')
  # campos são analisados como um token .campo. após um termo ou um conjunto entre parênteses
  RE_TOKENS_CRITERIOS = re.compile(r'(\s)|(adjc?\d* |proxc?\d* |com\d* )|(\.[a-z0-9<>=]+\.)|([0-9]+)|([a-zA-Z\$\?~]+)|(\n+)|(\W|.)')
  RE_TOKENS = re.compile(r'(\s)|([0-9]+)|([a-zA-Z]+)|(\n+)|(\W|.)')
  RE_IGNORAR_CRITERIOS = re.compile(r'([^a-z0-9\.\)\(\$\?~"\n])+')
  RE_IGNORAR = re.compile(r'([^a-z0-9\n])+')
  RE_PARENTESES_ABRE = re.compile(r'{|\[')
  RE_PARENTESES_FECHA = re.compile(r'}|\]')
  RE_ASPAS = re.compile(r"'" + '|"|´|`|“|”')
  RE_NUMEROS = re.compile(r'([0-9])([\.,]+)([0-9])')

  SINONIMOS = {'alegre': ['feliz','sorridente'], 'feliz':['alegre','sorridente'], 'sorridente':['alegre','feliz'] }
  SINONIMOS_COMPOSTOS = {'casa_de_papel':['la casa de papel','a casa de papel'], "inss" : ['instituto nacional de seguridade social'], 'instituto_nacional_de_seguridade_social':['inss']}

  ################################################################################
  # critérios = True - permite símbolos usados nos operadores
  # o texto é limpo e tokenizado
  # a singularização ocorre na tokenização - o mapa é gerado com termos no singular
  # os sinônimos são consultados em tempo de pesquisa, não afetam a tokenização nem o mapa
  ################################################################################
  def __init__(self, texto: str ='', criterios: str = '', mapa_texto: dict = None, print_debug = False):
    self.print_debug = print_debug
    self.novo_texto(texto=texto, atualizar_pesquisa = False)
    # caso não tenha recebido um texto, verifica se veio um mapa
    # se vier um texto e um mapa, ignora o mapa
    if len(self.tokens_texto) == 0 and mapa_texto:
       self.novo_mapa_texto(mapa_texto, atualizar_pesquisa = False)
    self.novo_criterio(criterios = criterios)

  ################################################################################
  # retorna o match final da pesquisa
  ################################################################################
  def retorno(self):
     return self.analisar_mapa_pesquisa()

  ################################################################################
  # reinicia as variáveis por mudança dos critérios
  ################################################################################
  def limpar_saida_criterios(self):
    self.tokens_criterios =  []     # crotérios de pesquisa tokenizados mas não analisados
    self.erros = ''                 # texto com mensagens de erro
    self.mapa_criterios = []        # mapa com os critérios de pesquisa
    self.criterios = ''             # texto com os critérios de pesquisa já analisados
    self.criterios_and_or_not = ''  # texto com critérios simples de pesquisa - exemplo MemSQL
    self.mapa_pesquisa = []         # mapa de pesquisa consolidado entre critérios de pesquisa e texto 

  ################################################################################
  # atualzia o mapa cruzando dados dos critérios e do texto
  # o mapa é a base da execução da pesquisa
  ################################################################################
  def atualizar_mapa_pesquisa(self):
    if len(self.erros) > 0:
      self.mapa_pesquisa =[]
    else:
      self.mapa_pesquisa = self.mapa_pesquisa_criterios(mapa_texto = self.mapa_texto, mapa_criterios = self.mapa_criterios)

  ################################################################################
  # recebe um texto novo e prepara o mapa de pesquisa
  ################################################################################
  def novo_texto(self, texto:str, atualizar_pesquisa = True):
    self.texto = self.processar_texto(texto)
    self.tokens_texto = self.processar_tokens(texto=self.texto, criterios=False, processar=False)
    self.tokens_texto_unicos = self.processar_tokens_unicos(tokens = self.tokens_texto)
    self.mapa_texto = self.processar_mapa(self.tokens_texto)
    if atualizar_pesquisa:
      self.atualizar_mapa_pesquisa()

  ################################################################################
  # recebe um mapa de texto pronto (pode ter sido guardado no banco, por exemplo)
  # não há necessidade do texto se o mapa for recebido pronto
  # cria o mapa de tokens para buscas em campos
  ################################################################################
  CAMPO_UNICO_SIMULADO = 'xXxXx'
  def novo_mapa_texto(self, mapa_texto, atualizar_pesquisa = True):
      self.texto = '' # não há necessidade do texto, apenas do mapa
      self.tokens_texto = [] # não há necessidade de guardar os tokens se não teve texto
      # para permitir a pesquisa de campos é necessário 
      # reconstruir a lista de tokens únicos pelo mapa      
      _mapa = json.loads(mapa_texto) if type(mapa_texto) is str else mapa_texto
      _campos = []
      _tokens_unicos = dict({})
      # constrói o dicionário de tokens únicos com {'CAMPO' : {token1, token2, ...}, .... }
      # mapa plano vira uma lista plana { 'token1','token2' }
      for txt, mp in mapa_texto.items():
          for _c in  mp.get('c',[]):
              _c = self.CAMPO_UNICO_SIMULADO if _c =='' else _c
              if _c not in _tokens_unicos.keys():
                 _tokens_unicos[_c] = [txt]
              else:
                 _tokens_unicos[_c].append(txt)
      # um set para ficar mais rápida a análise de termos da pesquisa
      _tokens_unicos = {cp:{_ for _ in tks} for cp, tks in _tokens_unicos.items()}
      # verifica se é campo único
      if len(_tokens_unicos.keys())==1 and self.CAMPO_UNICO_SIMULADO in _tokens_unicos.keys():
         _tokens_unicos = _tokens_unicos[self.CAMPO_UNICO_SIMULADO]
      # com o mapa, tokens e tokens únicos são iguais (não há necessidade de reconstrução fiel)
      self.tokens_texto_unicos = _tokens_unicos
      # guarda o mapa e prepara a pesquisa com mapa e critérios
      self.mapa_texto = _mapa
      # finaliza
      if atualizar_pesquisa:
         self.atualizar_mapa_pesquisa()

  ################################################################################
  # recebe um critério novo e recria o mapa de pesquisa
  ################################################################################
  def novo_criterio(self, criterios: str):
    self.limpar_saida_criterios()
    self.tokens_criterios =  self.processar_criterios(criterios)
    self.erros = self.analisar_erros_tokens_criterios(self.tokens_criterios)
    # continua se não houve erros de construção dos critérios
    if self.erros == '':
      self.mapa_criterios = self.processar_mapa_criterios(self.tokens_criterios)
      self.criterios = self.criterios_texto(self.mapa_criterios)
      #self.criterios_and_or_not = self.criterios_texto(self.mapa_criterios, and_or_not = True)
      self.criterios_and_or_not = self.converte_criterios_para_aon(self.criterios)
    self.atualizar_mapa_pesquisa()

  ################################################################################
  # cria uma lista rápida de análise de tokens únicos para pesquisas em campos
  ################################################################################
  def processar_tokens_unicos(self, tokens):
      # se o texto for um dict de {'campo': texto}
      if type(tokens) is dict:
        _tokens = dict({})
        for c,t in tokens.items():
          _tokens[c] = self.processar_tokens_unicos(tokens = t)
        return _tokens
      # permite uma pesquisa rápida nos valores dos tokens
      return {_ for _ in set(tokens)}

  #RE_SINGULAR_PRONOMES = re.compile(r'(-(ao|me|te|se|mos?|mas?|to|ta|lhos?|lhas?|nos?|nas?|vos?|lhes?|los?|las?|les?|iam?|ei|os?|as?))+$')
  RE_SINGULAR_OES = re.compile(r'(oes|aes)$')
  RE_SINGULAR_AIS = re.compile(r'(ais)$')
  RE_SINGULAR_EIS = re.compile(r'(eis)$')
  RE_SINGULAR_OIS = re.compile(r'(ois)$')
  RE_SINGULAR_LES = re.compile(r'(les)$')
  RE_SINGULAR_RES = re.compile(r'(res)$')
  RE_SINGULAR_ZES = re.compile(r'(zes)$')
  RE_SINGULAR_IS = re.compile(r'(is)$')
  RE_SINGULAR_NS = re.compile(r'(ns)$')
  RE_SINGULAR_S = re.compile(r'(a|e|i|o|u)(s)$')

  RE_OPERADOR = re.compile(r'^com\d*$|^e$|^ou$|^nao$|^adjc?\d*$|^proxc?\d*$|^mesmo$')
  OPERADORES_COM_NUMERO = {'ADJ','ADJC','PROX','PROXC','COM'}

  ################################################################################
  # singulariza termos - é uma pseudo singularização
  ################################################################################
  def singulariza(self,termo:str):
    # considera-se que está em lowercase
	  # considera-se que os acentos já foram removidos
	  # pronomes
    #_txt = self.RE_SINGULAR_PRONOMES.sub('',_txt)
    # plurais
    _txt = self.RE_SINGULAR_OES.sub('ao',termo)
    _txt = self.RE_SINGULAR_AIS.sub('al',_txt)
    _txt = self.RE_SINGULAR_EIS.sub('el',_txt)
    _txt = self.RE_SINGULAR_OIS.sub('ol',_txt)
    _txt = self.RE_SINGULAR_LES.sub('l',_txt)
    _txt = self.RE_SINGULAR_RES.sub('r',_txt)
    _txt = self.RE_SINGULAR_ZES.sub('z',_txt)
    _txt = self.RE_SINGULAR_IS.sub('il',_txt)
    _txt = self.RE_SINGULAR_NS.sub('m',_txt)
    _txt = self.RE_SINGULAR_S.sub('\\1',_txt)
    return _txt

  RE_UNICODE = re.compile("[\u0300-\u036f]")
  def normalizar_simbolos(self, texto):
      return self.RE_UNICODE.sub('', normalize("NFD", texto)).lower().replace('<br>','\n')

  ################################################################################
  # faz um pré processamento do texto para remover acentos e padronizar 
  # números e símbolos - é rodado nos critérios também
  ################################################################################
  def processar_texto(self, texto):
    # se o texto for um dict de {'campo': texto}
    if type(texto) is dict:
      _textos = dict({})
      for c,t in texto.items():
        _textos[c] = self.processar_texto(texto = t)
      return _textos
    # processamento para um texto   
    # numeral - tem que ser antes do lowercase
    #_txt = normalize("NFD", str(texto)).lower().replace('<br>','\n');
    _txt = self.normalizar_simbolos(texto)
    #_txt = deaccent(texto.lower()).replace('<br>','\n');
    # {} ou [] viram ()
    _txt = self.RE_PARENTESES_ABRE.sub('(',_txt)
    _txt = self.RE_PARENTESES_FECHA.sub(')',_txt)
    # unificar códigos de aspas
    _txt = self.RE_ASPAS.sub('"',_txt)
    # padronizar números 1.000.111,33 - tira os símbolos 
    _txt = self.RE_NUMEROS.sub('\\1\\3',_txt)
    # quebra de linha br 
    _txt = self.RE_QUEBRA.sub('\n',_txt)
    return _txt

  ################################################################################
  # acrescenta sinônimos compostos apenas a termos entre aspas
  # inclui um lista de OU para termos compostos dos sinônimos
  ################################################################################
  def incluir_sinonimos_compostos(self, criterios):
      if criterios.find('"') < 0:
         return criterios
      _res = str(criterios)
      for termo, sins in self.SINONIMOS_COMPOSTOS.items():
          _de = f'"{termo.replace("_"," ")}"'
          if _res.find(_de) >=0:
              sins = [sins] if type(sins) is str else sins
              _por = [f'"{p.strip()}"' for p in sins if len(p)>0]
              if len( _por) >0:
                _por = ' ou '.join(_por)
                _res = re.sub(f'({_de})', f'(\\1 ou {_por})', _res)
      if self.print_debug and _res!=criterios: print('incluir_sinonimos_compostos: ', _res)
      return _res

  ################################################################################
  # processa a lista de tokens que são válidos para análise
  # remove ruídos do texto e tem tratamento diferenciado se estiver rodando no 
  # texto ou nos critérios de pesquisa
  ################################################################################
  RE_NAO_LITERAL = re.compile(r'(nao\s+)(")(.*)(")')
  def processar_tokens(self, texto, criterios : bool, processar: bool):
    # tokens de dicionário 
    if type(texto) is dict:
      _tokens = dict({})
      for k, v in texto.items():
        k = k.upper() # campos são maiúsculos sempre
        _tokens[k] = self.processar_tokens(texto=v, criterios=criterios, processar=processar)
      return _tokens

    # tokens de texto
    if criterios:
      # prepara critérios nao "literal literal literal" para nao ("literal literal literal")
      _txt = texto.replace('*','$').replace("'",'"') if not processar else self.processar_texto(texto.replace('*','$').replace("'",'"'))
      _txt = self.incluir_sinonimos_compostos(_txt)
      _txt = self.RE_CAMPO_COMPARA_CONVERTE.sub('\\4.\\2\\3.',_txt) # converte @campo=123 para 123.campo=. e afins
      _txt = self.RE_NAO_LITERAL.sub('\\1(\\2\\3\\4)',_txt)
      if self.print_debug and len(texto)>0: print(f' - critério final: {_txt}')
      _txt_match = self.RE_TOKENS_CRITERIOS.findall(_txt)
    else:
      _txt_match = self.RE_TOKENS.findall(texto if not processar else self.processar_texto(texto))
    _tks = []
    _re_ignorar = self.RE_IGNORAR_CRITERIOS if criterios else self.RE_IGNORAR
    for w in _txt_match:
        # trim se não for a própria quebra - corrige tokenização de critérios
        _tks.extend([_w.strip() if _w !='\n' else _w for _w in w if len(_w)>0 and not _re_ignorar.match(_w)])
    # debug        
    if self.print_debug and len(texto)>0: 
       if criterios:
          _op = len( [_t for _t in _tks if self.RE_OPERADOR.match(_t) ] )
          _par = len( [_t for _t in _tks if _t in ('(',')') ] )
          print(f'processar_critérios: {len(_tks)-_op-_par} termos, {_par} parênteses e {_op} operadores nos critérios')
          print(f' - tokens critérios: {_tks}')
       else:
          print(f'processar_tokens: {len(_tks)} tokens no texto')
    # retorno
    return [self.singulariza(_t) for _t in _tks]

  ################################################################################
  # processamento dos tokens dos critérios de pesquisa
  ################################################################################
  def processar_criterios(self, criterios:str):
    return self.processar_tokens(texto=criterios, criterios=True, processar=True)

  ################################################################################
  # cria um mapa com os critérios de pesquisa
  # para cadada token: [ {'texto': 'termo1', operador: '', 'numero': 0, 'literal' : bool}},
  #                      {'texto': 'ADJ2', operador: 'ADJ', 'numero': 2, 'literal' : bool}}
  #                      {'texto': '(', operador: '', 'numero': 2, 'literal' : bool}}
  # entre dois termos, sem operadores, é inserido o operador E
  ################################################################################
  RE_NUMERO_OPERADOR = re.compile('([a-zA-Z]+)(\d*)')
  OPERADOR_MAPA_E = {'texto':'E', 'operador':'E', 'numero':0, 'literal': False}
  OPERADOR_MAPA_ADJ1 = {'texto':'ADJ1', 'operador':'ADJ', 'numero':1, 'literal': False}
  TERMO_MAPA_TRUE = {'texto':'', 'operador': None, 'numero':0, 'literal': False, 't':[0], 'p':[0], 'c':[''] }
  TERMO_MAPA_FALSE = {'texto':'', 'operador': None, 'numero':0, 'literal': False, 't':[], 'p':[], 'c':[] }
  RE_PONTO_CAMPO = re.compile(r'^\.[a-z0-9<>=]+\.$')
  RE_PONTO_CAMPO_NOME = re.compile(r'[<>=]+')  # é o contrário, para remover o que achar - sub('')
  RE_PONTO_CAMPO_COMP = re.compile(r'[A-Za-z0-9]+') # é o contrário, para remover o que achar  - sub('')
  RE_CAMPO_COMPARA_CONVERTE = re.compile(r'(@)([a-zA-Z0-9]+)([<>=]+)("?[a-zA-Z0-9 ]+"?|[a-zA-Z0-9]+)') # sub('\\4.\\2\\3.')
  def processar_mapa_criterios(self, tokens: list):
    mapa= []
    _lt = False
    _anterior_termo = False
    for i, tk in enumerate(tokens):
      _n = None
      _op = None
      if tk in ('"',"'"):
        _lt = not _lt
        continue
      if (not _lt) and self.RE_OPERADOR.search( tk ):
        _op = self.RE_NUMERO_OPERADOR.sub('\\1',tk).upper()
        _n = self.RE_NUMERO_OPERADOR.sub('\\2',tk)
        _n = 1 if _n=='' else int(_n)
        _anterior_termo = False
      elif (not _lt) and self.RE_PONTO_CAMPO.search( tk ):
        tk = tk.replace('.','')
        _op = 'CAMPO'
        #_anterior_termo = (mesmo do anterior pois o campo é um operador invisível)
      else:
        # entre dois termos, sem operadores, é inserido o operador E
        # parênteses não pode ser considerado um termo
        if (i>0) and _anterior_termo and tk != ')': 
           if not _lt: 
              mapa.append(self.OPERADOR_MAPA_E)
           else:
              mapa.append(self.OPERADOR_MAPA_ADJ1)
        _anterior_termo = (tk !='(')
      mapa.append({'texto':tk, 'operador':_op, 'numero':_n, 'literal': _lt})
    return mapa

  ################################################################################
  # cria um mapeamento do posicionamento de cada token
  # para cada token: {'token',  't': [lista de índices de token que ele aparece], 
  #                             'p': [lista parágrafos que ele aparece], 
  #                             'c' : [lista de campos que ele aparece]}
  ################################################################################
  def processar_mapa(self, tokens, campo: str = ''):
    # mapa para vários campos
    if type(tokens) == dict:
      _mapa = dict({})  # {'campo': mapa ....}
      for c,t in tokens.items():
          _mp = self.processar_mapa(tokens=t, campo =c)
          # agrupa o mapa do campo com o mapa geral
          for _k, _v in _mp.items():
            if not _mapa.get(_k):
              _mapa[_k] = _v
            else:
              _mapa[_k]['t'].extend(_v['t'])
              _mapa[_k]['p'].extend(_v['p'])
              _mapa[_k]['c'].extend(_v['c'])
      return _mapa
    # mapa para um campo
    mapa = dict({})  # termo ntermo npar e campo
    np = 0
    nt = 0
    for tk in tokens:
        if tk == '\n':
          np += 1
          continue
        dic_t = mapa.get(tk,{})
        dic_nt = dic_t.get('t',[]) # posições dos tokens
        dic_np = dic_t.get('p',[]) # posições dos parágrafos
        dic_cp = dic_t.get('c',[]) # campos dos tokens
        dic_nt.append(nt)
        dic_np.append(np)
        dic_cp.append(campo)
        mapa[tk]= {'t' : dic_nt, 'p': dic_np, 'c': dic_cp}
        nt += 1
    return mapa    

  ################################################################################
  # analisa erros na estrutura dos critérios de pesquisa
  # aspas incompletas, parênteses e operadores
  ################################################################################
  def analisar_erros_tokens_criterios(self, tokens_criterios: list):
    _ok = 0
    _aspas = False
    for _c in self.tokens_criterios:
      if _c in ('(',')') and _aspas:
        return 'Aspas incompletas seguidas de parênteses'
      if _c == '(':
        _ok += 1
      elif _c == ')':
        _ok += -1
      elif _c in ('"',"'"):
        _aspas = not _aspas
      if _ok == -1:
        return 'Parênteses fechado sem ter sido aberto'
    if _ok >0:
      return 'Parênteses aberto e não fechado'
    if _aspas:
      return 'Aspas abertas e não fechadas'
    # analise operadores sem termos para avaliar
    _anterior_parenteses_a = False
    _anterior_operador = False
    _atual_operador = False
    _aspas = False
    for i,_c in enumerate(self.tokens_criterios):
      _atual_operador = (not _aspas) and self.RE_OPERADOR.search(_c)
      if _c in ('"',"'"):
         _aspas = not _aspas
      elif i==0 and _c != 'nao' and _atual_operador:
        return 'Critérios de pesquisa não podem começar com operadores diferentes de NÃO'
      if _anterior_parenteses_a and _c != 'nao' and _atual_operador:
        return 'Critérios de pesquisa não podem começar com operadores diferentes de NÃO depois de parênteses'
      elif _anterior_operador and _c == ')':
        return 'Critérios de pesquisa não podem terminar com operadores antes de parênteses'
      elif _anterior_operador and _atual_operador:
        return 'Critérios de pesquisa não podem conter operadores seguidos'
      elif i == len(self.tokens_criterios)-1 and _atual_operador:
        return 'Critérios de pesquisa não podem terminar com operadores'
      _anterior_parenteses_a = _c == '('        
      _anterior_operador = _atual_operador
    return ''

  ################################################################################
  # cria uma pesquisa simplificada com operadores AND OR NOT 
  # pode ser usada em pesquisa textual como o MEMSQL ou adaptada para o elasticsearch
  # com isso os critérios mais complexos (ADJ, PROX, etc) são analisados apenas
  # nos textos com mais probabilidade de terem o que é pesquisado
  ################################################################################
  RE_AON_OPERADORES_PARA_AND = re.compile(r'( ADJC?\d* | PROXC?\d* | COM\d* )|( E )')
  RE_AON_OPERADORES_PARA_OR = re.compile(r'( OU )')
  RE_AON_OPERADORES_PARA_NOT = re.compile(r'( NAO )')
  RE_AON_LIMPAR_FILTRO_PARENTESES = re.compile(r'(AND )?(OR )?(NOT )?(\(.+\))(\.)([a-zA-Z0-9]+)(>=?|<=?|<>)(\.)')
  RE_AON_LIMPAR_FILTRO = re.compile(r'(AND )?(OR )?(NOT )?([a-zA-Z0-9]+)(\.)([a-zA-Z0-9]+)(>=?|<=?|<>)(\.)')
  RE_AON_LIMPAR_FILTRO_ASPAS = re.compile(r'(AND )?(OR )?(NOT )?"([a-zA-Z0-9 ]+)"(\.)([a-zA-Z0-9]+)(>=?|<=?|<>)(\.)')
  RE_AON_LIMPAR_FILTROS_CAMPO = re.compile(r'(\.)([a-zA-Z0-9]+)(=?)(\.)')
  RE_AON_LIMPAR_FILTROS_CAMPO_ASPAS = re.compile(r'"(\.)([a-zA-Z0-9]+)(=?)(\.)')
  RE_AON_PARENTESES_VAZIOS = re.compile(r'\(\s*\)')
  RE_AON_OPERADOR_REPETIDO = re.compile(r'(\s+AND|\s+OR|\s+NOT)+')
  RE_AON_ESPACOS = re.compile(r'\s+')
  def converte_criterios_para_aon(self, criterios:str):
      _txt = self.RE_AON_OPERADORES_PARA_AND.sub(' AND ',criterios)  # ADJ PROX COM e E para AND
      _txt = self.RE_AON_OPERADORES_PARA_OR.sub(' OR ',_txt)     # OU para OR
      _txt = self.RE_AON_OPERADORES_PARA_NOT.sub(' NOT ',_txt)   # NAO para NOT
      _txt = self.RE_AON_LIMPAR_FILTRO_PARENTESES.sub('',_txt)   # filtro de um grupo
      _txt = self.RE_AON_LIMPAR_FILTRO_ASPAS.sub('',_txt)   # filtro de um literal
      _txt = self.RE_AON_LIMPAR_FILTRO.sub('',_txt)         # filtro de um termo
      _txt = self.RE_AON_LIMPAR_FILTROS_CAMPO_ASPAS.sub('"',_txt)  # referências ao campo do filtro
      _txt = self.RE_AON_LIMPAR_FILTROS_CAMPO.sub('',_txt)  # referências ao campo do filtro
      while self.RE_AON_PARENTESES_VAZIOS.search(_txt):
            _txt = self.RE_AON_PARENTESES_VAZIOS.sub('',_txt)
      _txt = self.RE_AON_OPERADOR_REPETIDO.sub('\\1',_txt)  # OPERADORES REPETIDOS mantém o último
      _txt = self.RE_AON_ESPACOS.sub(' ',_txt)
      if self.print_debug: print(f'converte_criterios_para_aon: [{criterios}] => [{_txt}]'  )
      return _txt.strip()

  ################################################################################
  # converte o mapa de critérios de pesquisa em texto
  ################################################################################
  RE_ADJ_AND_OU_NOT = re.compile('"\s*ADJ1\s*"')
  # para o filtro simples AND OR NOT, filtros de campo >, <, <> devem ser ignorados pois não são avaliáveis nessas pesquisas
  def criterios_texto(self, mapa_criterios: list):
    _texto = []
    _aspas = False
    for cr in mapa_criterios:
        _t = ''
        # finaliza aspas anteriores
        if _aspas and not cr.get('literal'):
          _texto[-1] = _texto[-1] + '"'
          _aspas = False
        # texto com o tratamento de aspas/literal 
        if not cr.get('operador'):
           # inicia ou continua aspas
           if cr.get('literal'):
             if not _aspas:
                _t += '"'
                _aspas = True
           _t += cr.get('texto','')
        # operadores   
        else:
           _o = cr.get('operador','').upper()
           if _o == 'CAMPO':
               _o = f'.{cr.get("texto")}.'
               _o = _o.upper()
           _t += _o
           if _o in self.OPERADORES_COM_NUMERO:
             _t += str(cr.get('numero',1))
        _texto.append(_t)
    # finaliza as últimas aspas se for necessário
    if _aspas:
      _texto[-1] = _texto[-1] + '"'
    _txt = ' '.join(_texto)
    # corrige os ADJ1 com literais
    # corrige os filtros de campos pois ficam com espaço entre tokens
    return self.RE_ADJ_AND_OU_NOT.sub(' ',_txt).replace(' .','.')

  ################################################################################
  # busca na lista de tokens do texto os 
  # termos que são compatíveis com os curingas
  ################################################################################
  RE_CURINGAS = re.compile(r'(\$)|(\?)')
  def termos_por_curinga(self,termo, tokens_texto):
    # tokens de dicionário 
    if type(tokens_texto) is dict:
      _tokens = []
      for k, v in tokens_texto.items():
        _tokens += self.termos_por_curinga(termo = termo, tokens_texto = v)
      return _tokens

    # tokens por lista
    _find = termo.get('texto','') if type(termo) is dict else str(termo)
    if (not self.RE_CURINGAS.search(_find)) or (len(self.RE_CURINGAS.sub('',_find)) == 0):
        return []
    _find = _find.replace('$',r'.*').replace('?','.?').strip()
    _find_re = re.compile(str(_find))
    _termos = [t for t in tokens_texto if _find_re.search(t) ]
    if self.print_debug: print(f'Termos por curinga: [{_find}] ', ' '.join(_termos))
    return _termos

  ################################################################################
  # cria um mapa com os critérios da pesquisa convertidos em posicionamentos do texto incluindo possíveis dicionários
  # é o cruzamento dos critérios de pesquisa com o que existe no texto. 
  # Pra depois avaliar os operadores desse resultado final dos operadores sobre esse mapa no método analisar_mapa_pesquisa
  # para cadada token: [ {'texto': 'termo1', operador: '', 'numero': 0, 'literal' : bool, 't' : [posiçõe dos tokens ], 'p': [parágrafos], 'c':'campos'},
  #                      {'texto': 'ADJ2', operador: 'ADJ', 'numero': 2, 'literal' : bool}}
  #                      {'texto': '(', operador: '', 'numero': 2, 'literal' : bool}}
  def mapa_pesquisa_criterios(self, mapa_texto:dict, mapa_criterios:list):
    _mapa = []
    for cr in mapa_criterios:
      if not cr.get('operador'):
        _mp = mapa_texto.get(cr['texto'])
        _sin = []
        if not cr.get('literal'):
           if (self.SINONIMOS is not None) and len(self.SINONIMOS)>0:
              _sin = self.SINONIMOS.get(cr['texto'],[])
           _curingas = self.termos_por_curinga(termo = cr['texto'], tokens_texto = self.tokens_texto_unicos)
           _sin = list(set(_sin + _curingas))
           if self.print_debug and len(_sin)>0: print(' - sinônimos e curingas: ', _sin)
           #   _proximos = [t for t in ]
        # não encontrou o texto nem sinônimos
        if (_mp == None) and (len(_sin) == 0):
          _t, _p, _c = [],[],[]
        else: # une as listas de tudo que encontrou
          _sin = [mapa_texto.get(_s) for _s in _sin]
          _sin.append(_mp)
          _sin = [_s for _s in _sin if not _s is  None]
          _t = []
          _p = []
          _c = []
          for s in _sin:
            _t.extend(s['t'])
            _p.extend(s['p'])
            _c.extend(s['c'])
        # adiciona a lista de posições do termos e sinônimos
        cr['t'] = _t
        cr['p'] = _p
        cr['c'] = _c
      _mapa.append(cr)  
    # com o mapa plano, cria um mapa em árvore até que o mapa da folha não tenha parênteses dentro dele
    # exemplo:  [termo and (termo and termo and termo and (termo and termo) and termo and (termo and termo))]
    # vira:      termo and [termo and termo and termo and [termo and termo] and termo and [termo and termo]]
    _q = [0]
    def _lista_agrupada():
      if _q[0] > 200000:
        print('ERRO: Estouro de árvore - verifique os parênteses dos tokens dos critérios')
        return []
      _q[0] += 1
      _lst = []
      while len(_mapa)>0:
        if _mapa[0]['texto'] == '(':
            del _mapa[0]
            _lst.append( _lista_agrupada())
        elif _mapa[0]['texto'] == ')':
            del _mapa[0]
            break
        else:
          _lst.append(_mapa[0])
          del _mapa[0]
      return _lst
    _res = _lista_agrupada()
    # filtra os tokens com os operadores de campos
    # o filtro externo pode ser sobreposto por um filtro interno de campo
    # exemplo: (cadeira.campo1. casa apartamento).campo2. 
    #           cadeira será pesquisado no campo1 e casa e apartamento no campo2
    def _filtra_campos(lista:list, filtro:str='', filtro_valor = ''):
        _res_filtro = []
        for i, tk in enumerate(lista):
            if i < len(lista)-1 and self.e_operador_campo(lista[i+1]):
               _subfiltro = lista[i+1].get('texto')
               _subfiltro_valor = tk.get('texto') if type(tk) is dict else ''
            else:
              _subfiltro = filtro
              _subfiltro_valor = filtro_valor
            _subfiltro = _subfiltro.upper() # campos maiúsculos sempre
            if (type(tk) is list):
               _res_filtro.append( _filtra_campos(tk, _subfiltro, _subfiltro_valor) )
            elif self.e_operador_campo(tk):
               pass # é um operador de campo - ignora - (só filtra o anterior)
            elif _subfiltro !='':
               _subfiltro_nome = self.RE_PONTO_CAMPO_NOME.sub('',_subfiltro)
               _subfiltro_comp = self.RE_PONTO_CAMPO_COMP.sub('',_subfiltro)
               if _subfiltro_valor !='' and _subfiltro_comp !='':
                  # filtros com comparadores especiais
                  _res_filtro.append(self.buscar_termo_campo(_subfiltro_nome, _subfiltro_comp, _subfiltro_valor))
                  cf = []
                  tpc = []
               else:
                  # filtros com comparador = ou sem comparador
                  tpc = zip( tk.get('t',[]), tk.get('p',[]), tk.get('c',[]) ) 
                  cf = [c for c in tpc if c[2] == _subfiltro_nome]
                  if len(cf)>0:
                      # tem que ser lista pois na análise da pesquisa ocorre o agrupamento de termos
                      tk['t'], tk['p'], tk['c'] = zip(*cf)
                      tk['t'], tk['p'], tk['c'] = list(tk['t']), list(tk['p']), list(tk['c'])
                  else:
                      tk['t'], tk['p'], tk['c'] = [],[],[]
                  _res_filtro.append(tk)
               if self.print_debug: print(' - filtrar campos: ', _res_filtro, 'campos: ', list(tpc), ' filtrado:', cf, f' campo: {_subfiltro_nome} {_subfiltro_comp} {_subfiltro_valor}')
            else:
              _res_filtro.append(tk)
        return _res_filtro
    _res = _filtra_campos(_res)

    #retorno final
    if self.print_debug: print(' - mapa_pesquisa_criterios: ', _res)
    return _res

  ################################################################################
  # retorna os dados do objeto de pesquisa
  ################################################################################
  def dados(self):
    return self.__dict__.items()

  ################################################################################
  # imprime um resumo do objeto de pesquisa com o retorno da pesquisa realizada
  ################################################################################
  def print_resumo(self):
      print('RESUMO DA PESQUISA: retorno =', self.analisar_mapa_pesquisa())
      print(' - texto:', self.texto)
      print(' - tokens:', self.tokens_texto)
      print(' - tokens_unicos:', self.tokens_texto_unicos)
      print(' - criterios:', self.tokens_criterios)
      print(' - mapa:', self.mapa_texto)    

  ################################################################################
  # imprime todos os dados do objeto de pesquisa
  ################################################################################
  def print(self, realizar_pesquisa = True):
    def _print_mapa(mapa, idx=0):
      for _m in mapa:
        if type(_m) is dict:
          print(f'  |{"__" * (idx+1)} {_m}')
        else:
          _print_mapa(_m, idx + 1)
    for _k in self.__dict__.keys():
      if f'{_k}' != 'mapa_pesquisa':
         print(f'{_k}: ', self.__dict__[_k] )
      else:
        print('mapa_pesquisa: (árvore)')
        _print_mapa(self.mapa_pesquisa)
    if realizar_pesquisa:
       print('PESQUISA: ', self.analisar_mapa_pesquisa())

  ################################################################################
  # retorna se um token é um determinado tipo de critério, termo, etc
  ################################################################################
  def e_operador_nao(self, operador):
      return self.e_operador(operador) == 'NAO'
  def e_operador_e(self, operador):
      return self.e_operador(operador) == 'E'
  def e_operador_ou(self, operador):
      return self.e_operador(operador) == 'OU'
  def e_operador_adj(self, operador):
      return self.e_operador(operador) == 'ADJ'
  def e_operador_adjc(self, operador):
      return self.e_operador(operador) == 'ADJC'
  def e_operador_prox(self, operador):
      return self.e_operador(operador) == 'PROX'
  def e_operador_proxc(self, operador):
      return self.e_operador(operador) == 'PROXC'
  def e_operador_com(self, operador):
      return self.e_operador(operador) == 'COM'
  def e_operador_mesmo(self, operador):
      return self.e_operador(operador) == 'MESMO'
  def e_operador_campo(self, operador):
      return self.e_operador(operador) == 'CAMPO'
  def e_termo(self, operador):
      return type(operador) is dict and (not operador.get('operador'))
  def e_operador(self, operador):
      return type(operador) is dict and operador.get('operador')
  def termo_existe(self,termo):
      return self.e_termo(termo) and ( len( termo.get('t',[]) ) >0 )

  ################################################################################
  # procura nos tokens do campo específico um valor que corresponda ao critério
  # resolve a pesquisa de campos com =, >, <, <= e >=
  # como só serve para pesquisa em campso, retorna false se não tiver campo mapeado no texto
  ################################################################################
  def buscar_termo_campo(self, nome_campo, tipo_comparador, valor):
      if nome_campo=='' or tipo_comparador=='' or valor=='':
         if self.print_debug: print(f'buscar_termo_campo: comparação incompleta [{nome_campo}|{tipo_comparador}|{valor}] {type(self.tokens_texto_unicos)}')
         return self.TERMO_MAPA_FALSE
      # se o texto não é um dicionário com campos, qualquer comparação de campo é false
      if (not type(self.tokens_texto_unicos) is dict):
         return self.TERMO_MAPA_FALSE
      if tipo_comparador == '=':
         achou = valor in self.tokens_texto_unicos.get(nome_campo,[])
         _valor_achado = valor
      else:
         achou = False;
         _valor = int(valor) if str(valor).isnumeric() else valor
         for vlr in self.tokens_texto_unicos.get(nome_campo,[]):
              if (type(_valor) is int) and not str(vlr).isnumeric():
                 continue
              _vlr = int(vlr) if str(vlr).isnumeric() else vlr
              if (tipo_comparador =='>=' and _vlr >= _valor) or \
                  (tipo_comparador =='>' and _vlr > _valor) or \
                  (tipo_comparador =='<=' and _vlr <= _valor) or \
                  (tipo_comparador =='<' and _vlr < _valor) or \
                  (tipo_comparador =='<>' and _vlr != _valor):
                  achou = True
                  _valor_achado = vlr
                  break
      if self.print_debug: print(f'buscar_termo_campo: {nome_campo} {tipo_comparador} {valor}]  ==> {achou}')
      if achou:
         termo_true = cp.copy(self.TERMO_MAPA_TRUE)
         termo_true['texto'] = _valor_achado
      return termo_true if achou else self.TERMO_MAPA_FALSE

  ################################################################################
  # executa a pesquisa propriamente dita
  # precisa de critérios e texto analisados e mapeados
  #
  # com o mapa de pesquisa, os critérios são analisados recursivamente por conjunto de parênteses, retornando uma lista de combinações que deram match em cada análise
  # ao final, se existir um dict de termo que tem posições no texto, a pesquisa teve resultado positivo
  ################################################################################
  def analisar_mapa_pesquisa(self, mapa_pesquisa:list = None, retornar_analises = False):
    _analises = []
    if mapa_pesquisa is None:
        _mapa = cp.copy(self.mapa_pesquisa)
    else:
        _mapa = cp.copy(mapa_pesquisa)
    if len(_mapa) == 0:
        return False
    # une dois termos com suas posições para análise em conjunto
    # distancia positica (para frente) negativa (para tras e para frente) zero (não analisa)
    def _soma_termos(termo1,termo2, mesmo_paragrafo=False, mesmo_campo=False, distancia = 0, distancia_par = 1):
        _distancia_par = distancia_par -1 if distancia_par >1 else 0 # máximo de parágrafos analisados abaixo
        if distancia==0 and (not mesmo_paragrafo) and (not mesmo_campo): # operador OU, junta todas as posições
          if self.print_debug: print('---\n   ', termo1, termo2,' OU')
          _tsoma = termo1.get('t',[]) + termo2.get('t',[])
          _psoma = termo1.get('p',[]) + termo2.get('p',[])
          _csoma = termo1.get('c',[]) + termo2.get('c',[])
          _txt = termo1.get('texto','') + '|' + termo2.get('texto','')
        else:
          if self.print_debug: print('   --- soma termos: ', termo1, termo2,' (p c d dp:', mesmo_paragrafo, mesmo_campo, distancia,_distancia_par,')')
          _tsoma, _psoma, _csoma = [],[],[]
          _tpc1 = list( zip( termo1.get('t',[]), termo1.get('p',[]), termo1.get('c',[]) ) )
          _tpc2 = list( zip( termo2.get('t',[]), termo2.get('p',[]), termo2.get('c',[]) ) ) 
          _txt = ''
          #print('_tpc1: ', _tpc1, '  _tpc2: ', _tpc2) 
          for _t1 in _tpc1:
            for _t2 in _tpc2:
                #print(f't1 {_t1}  t2 {_t2}')
                if ( (not mesmo_paragrafo) or ( 0<= _t2[1] - _t1[1] <= _distancia_par) ) and \
                  ( (not mesmo_campo) or (_t1[2] == _t2[2]) ) and \
                  ( (distancia == 0) or (distancia>0 and 0 <= _t2[0] - _t1[0] <= distancia) or ( distancia<0 and distancia <= _t2[0] - _t1[0] <= -distancia) ):
                  # o segundo termos sempre é retornado no adj ou no prox
                  _tsoma.append(_t2[0])
                  _psoma.append(_t2[1])
                  _csoma.append(_t2[2])
                  # distância <0 é prox, junta os termos
                  if distancia < 0 : 
                      _tsoma.append(_t1[0])
                      _psoma.append(_t1[1])
                      _csoma.append(_t1[2])
          if len(_tsoma) > 0:
            _txt = (f"{termo1.get('texto','')}|" if distancia < 0 else '') +  termo2.get('texto','')
        _res = cp.copy(self.TERMO_MAPA_FALSE)
        _res['t'] = _tsoma
        _res['p'] = _psoma
        _res['c'] = _csoma
        _res['texto'] = _txt
        return _res
    # analisa o trio mais comum - termo OP termo
    def _analisa_trio(termo1, operador, termo2):
        if self.print_debug: print('---\n-Analisa ', termo1.get('texto'), operador.get('texto'), termo2.get('texto'))
        if self.e_operador_ou(operador):  # OU
          _res = _soma_termos(termo1,termo2)
        elif self.e_operador_e(operador): # E
          _res = termo2 if self.termo_existe(termo1) and self.termo_existe(termo2) else cp.copy(self.TERMO_MAPA_FALSE)
        elif self.e_operador_nao(operador): # NAO
          _res = cp.copy(self.TERMO_MAPA_TRUE) if self.termo_existe(termo1) and (not self.termo_existe(termo2)) else cp.copy(self.TERMO_MAPA_FALSE)
        elif self.e_operador_mesmo(operador): # MESMO
          _res = _soma_termos(termo1,termo2, mesmo_paragrafo = False, mesmo_campo=True)
        elif self.e_operador_com(operador): # COM
          _res = _soma_termos(termo1,termo2, mesmo_paragrafo = True, mesmo_campo=True, distancia_par = operador.get('numero',1) )
        elif self.e_operador_adj(operador): # ADJ
          _res = _soma_termos(termo1,termo2, mesmo_paragrafo = False, mesmo_campo=True, distancia = operador.get('numero',1))
        elif self.e_operador_adj(operador): # ADJC
          _res = _soma_termos(termo1,termo2, mesmo_paragrafo = True, mesmo_campo=True, distancia = operador.get('numero',1))
        elif self.e_operador_prox(operador): # PROX
          _res = _soma_termos(termo1,termo2, mesmo_paragrafo = False, mesmo_campo=True, distancia = -1 * operador.get('numero',1))
        elif self.e_operador_proxc(operador): # PROXC
          _res = _soma_termos(termo1,termo2, mesmo_paragrafo = True, mesmo_campo=True, distancia = -1 * operador.get('numero',1))
        else:
          _res = cp.copy(self.TERMO_MAPA_FALSE)
        if self.print_debug: print(f'   ==> {self.termo_existe(_res)}')
        return _res
    # rotina que será usada recursivamente na análise dos critérios
    def _analisa_lista(mp):
        if len(mp) == 0:
            return self.TERMO_MAPA_FALSE
        _para_analise = mp if retornar_analises else None
        while len(mp) > 1:
            # operador campo - ignora pois já foi tratado no mapa de critérios
            if self.e_operador_campo(mp):
               del mp[0]
            # analisa termo OP termo
            elif len(mp)>=3 and self.e_termo(mp[0]) and self.e_operador(mp[1]) and self.e_termo(mp[2]):
                 mp[0] = _analisa_trio(mp[0],mp[1],mp[2])
                 del mp[1] 
                 del mp[1] 
            # analisa NAO termo
            elif len(mp)>=2 and self.e_operador_nao(mp[0]) and self.e_termo(mp[1]):
                 mp[0] = cp.copy(self.TERMO_MAPA_FALSE) if self.termo_existe(mp[1]) else cp.copy(self.TERMO_MAPA_TRUE)
                 del mp[1] 
            # analisa termo termo => analisa termo E termo -- trata como erro no critério
            elif len(mp)>=2 and self.e_termo(mp[0]) and self.e_termo(mp[1]):
                 if self.print_debug: print(f'* Incluído operador automático E entre dois termos [{mp[0].get("texto")}] E [{mp[1].get("texto")}]')
                 mp[0] = _analisa_trio(mp[0],self.OPERADOR_MAPA_E,mp[1])
                 del mp[1] 
            # resolve operador operador (ignora o primeiro) -- trata como erro no critério
            elif len(mp)>=2 and self.e_operador(mp[0]) and self.e_operador(mp[1]):
                 del mp[0]
            # analisa termo OP OP - ignora o primeiro operador, trata como erro no critério
            elif len(mp)>=3 and self.e_termo(mp[0]) and self.e_operador(mp[1]) and self.e_operador(mp[2]):
                 del mp[1] 
        # adiciona o resultado das análises para debug
        if retornar_analises:
           _analises.append((mp[0], _para_analise))
        # retorna o termo que representa a análise realizada
        return mp[0]

    # reduz todas as lista a um termo que representa o resultado dela
    def _reduz_mapa(mp):
      # verifica se existe sublista
      _tem_sublista = [ None for _ in mp if type(_) is list ]
      # tendo sublista, reduz
      if len(_tem_sublista) > 0:
        _res = []
        for m in mp:
          if type(m) is list:
            _res.append(_reduz_mapa(m))
          else:
            _res.append(m)
        return _reduz_mapa(_res)
      # não tem sublista, analisa a lista plana - o que reduz a um termo representativo do resultado
      return _analisa_lista(mp)
    # reduz a lista de árvore em um lista plana com as sublistas resolvidas
    _termo = _reduz_mapa(_mapa)
    # faz a análise final da última lista plana
    #_termo = _analisa_lista(_mapa)
    # retorna cada análise da árvore se foi pedido
    if retornar_analises:
        # inclui ao final o termo representativo do resultado da pesquisa
        _analises.append(_termo) 
        return _analises
    # sobrando um termo e esse termo existindo no documento, retorna True
    if self.print_debug: print('-Fim Análise> ', self.termo_existe(_termo), _termo,'\n---')
    return self.termo_existe(_termo)

  ################################################################################
  # realiza testes internos e pode receber testes complementares
  # se um teste falhar, ativa o debug e realiza novamente o teste
  # para apresentar resultados da análise - interrompe os testes ao falhar um deles
  ################################################################################
  def testes(self, testes = None, somar_internos = True):
      # {"texto" : "", "criterio":, "resposta" : true/false}
      _testes = None
      if (testes is None) or (somar_internos):
          _texto = "a casa de papel é um seriado bem interessante numero123"
          _testes = [{'texto': 'áéíóúàâôçÁÉÍÓÚÀÂÔÇ Üü texto123', 'criterio':'texto 123 uu aeiouaaocaeiouaaoc', 'retorno': True},
                     {'texto': _texto, 'criterio': "casa adj2 papel", 'retorno' : True},
                     {'texto': _texto, 'criterio': "'numero 123' prox3 interessante", 'retorno' : True},
                     {'texto': _texto, 'criterio': "casa adj6 seriado", 'retorno' : True},
                     {'texto': _texto, 'criterio': "seriado prox3 papel", 'retorno' : True},
                     {'texto': _texto, 'criterio': "casa adj3 seriado", 'retorno' : False},
                     {'texto': _texto, 'criterio': "(casa prox4 seriado) ou (seriado adj1 interessante)", 'retorno' : False},
                     {'texto': _texto, 'criterio': "(casa prox4 seriado) ou (seriado adj1 interessante) ou uns", 'retorno' : True},
                     {'texto': _texto, 'criterio': "pape$ ou seria$", 'retorno' : True},
                     {'texto': {'a':_texto,'b': 'segundo'}, 'criterio': "(casa papel) e segund$", 'retorno' : True},
                     {'texto': 'esses textos \ntem\n os e literais para uns testes sorridente', 'criterio': "texto com literal", 'retorno' : False},
                     {'texto': 'esses textos \ntem\n os e literais para uns testes sorridente', 'criterio': "texto com2 literal", 'retorno' : False},
                     {'texto': 'esses textos \ntem\n os e literais para uns testes sorridente', 'criterio': "texto com3 literal", 'retorno' : True},
                     {'texto': {'a':_texto,'b': 'segundo'}, 'criterio': "(casa papel) com segund$", 'retorno' : False},
                     {'texto': {'a':_texto,'b': 'segundo'}, 'criterio': "(casa papel) e segund$.b.", 'retorno' : True},
                     {'texto': {'a':_texto,'b': 'segundo'}, 'criterio': "(casa papel).a. e segund$.b. e 'casa de papel'.a. (seriado segundo) ", 'retorno' : True},
                     {'texto': {'a':_texto,'b': 'segundo texto com o número 1234'}, 'criterio': "(casa papel) e segund$.b. e 1234.b>=. e 123.b>. e 12345.b<=. ", 'retorno' : True},
                     {'texto': {'a':_texto,'b': 'segundo texto com o número 1234'}, 'criterio': "(casa papel) e segund$.b. e 1234.b>=. e @b>'123' e @b<=12345 ", 'retorno' : True},
                     {'texto': {'a':_texto,'b': '12 123 1 13 1234'}, 'criterio': " (1235.b>. ou 1236.b>.) ou @b>'12345' ", 'retorno' : False},
                     {'texto': {'a':_texto,'b': 'a aa b '}, 'criterio': " (ddd.b>. ou bbbb.b>.) ou @b>'ccc' ", 'retorno' : False},
                     {'texto': "o instituto nacional de seguridade social fez um teste com texto literal", 'criterio' : 'texto com literais (teste OU testa) ("inss" ou "CaSa de pApél")', 'retorno': True}
                     ]
      fim_internos = len(_testes) if not (_testes is None) else -1
      if not (testes is None):
        _testes += testes
      self.print_debug = False
      for i, teste in enumerate(_testes):
          if i == fim_internos :
             print('---------------------------------------')
             print('------  FIM DOS TESTES INTERNOS -------')
          texto = teste['texto']
          criterio = teste['criterio']
          print('---------------------------------------')
          print(f'Teste: {i} - {criterio}  ==> esperado {teste["retorno"]}')
          self.novo_texto(texto)
          self.novo_criterio(criterio)
          if teste["retorno"]:
             print(f'   AON => {self.criterios_and_or_not}')
          retorno = None
          if self.erros =='':
             retorno = self.analisar_mapa_pesquisa()
          if self.erros!= '' or retorno != teste['retorno']:
             if self.erros != '':
                print('ERRO NOS CRITÉRIOS: ', self.erros)
             self.print_debug = True
             self.print()
             self.analisar_mapa_pesquisa()
             break
          # verifica a reconstrução da pesquisa apenas pelo mapa
          pbmapa = PesquisaBR(criterios=self.criterios, mapa_texto = self.mapa_texto)            
          retorno = pbmapa.analisar_mapa_pesquisa() if pbmapa.erros == '' else None
          if pbmapa.erros!= '' or retorno != teste['retorno']:
             print('ERRO AO REFAZAR A PESQUISA PELO MAPA')
             print(f' - Teste: {i} - {criterio}  ==> esperado {teste["retorno"]}')
             if pbmapa.erros != '':
                print(' -- ERRO NOS CRITÉRIOS: ', pbmapa.erros)
             pbmapa.print_debug = True
             pbmapa.print()
             pbmapa.analisar_mapa_pesquisa()
             break
          #verifica o AND OR NOT
          criterio_aon = re.sub(' AND ',' E ', str(self.criterios_and_or_not))
          criterio_aon = re.sub(' OR ',' OU ', criterio_aon)
          criterio_aon = re.sub(' NOT ',' NAO ', criterio_aon)
          if criterio_aon.strip() !='':
              if teste["retorno"]==1 or teste["retorno"] == True:
                  self.novo_criterio(criterio_aon)
                  if self.erros =='':
                    retorno = self.analisar_mapa_pesquisa()
                  if self.erros != '' or not retorno:
                    print('CRITÉRIO AND OR NOT - FALHA ESPERADO TRUE ***')
                    if self.erros != '':
                       print('ERRO NOS CRITÉRIOS: ', self.erros)
                    self.print_debug = True
                    self.print()
                    self.analisar_mapa_pesquisa()
                    break
          else:
              print(f'   AON => VAZIO *** ')


if __name__ == "__main__":

    print('####################################')
    print('>> USO SIMPLES')
    print('------------------------------------')
    pb = PesquisaBR(texto = 'A casa de papel é um seriado muito legal', criterios='casa adj2 papel adj5 seriado')
    print(pb.print_resumo())

    print('####################################')
    print('>> TESTE BÁSICOS')
    print('------------------------------------')
    
    pb=PesquisaBR(print_debug=False)
    pb.testes()

    print('####################################')
    print('>> TESTE COMPLEMENTARES')
    print('------------------------------------')
    testes = [  {"texto":"	teste de texto agravo não provido ou sei lá	", "criterio":"	teste adj4 agravo	", "retorno":	1	},
                {"texto":"	a casa<br>grande	", "criterio":"	grande proxc10 casa	", "retorno":	0	},
                {"texto":"	nesse contexto, indefiro a liminar entre outras coisas mais, solicito e quero muito mais quaisquer informações	", "criterio":"	indefir$ adj4 liminar (solicit$ adj5 informações)	", "retorno":	0	},
                {"texto":"	confirmando que o dano moral que pode ser estético foi presumida a	", "criterio":"	'dano moral' adj5 estético não (presumido? ou presumida?)	", "retorno":	0	},
                {"texto":"	conforme encaminho esses autos para turma julgadora do juizo de retratacao	", "criterio":"	(encaminh$ ou remet$ ou remessa) adj2 (autos ou processo ou feito) adj2 Turma adj2 julgadora adj4 juízo adj2 retratação	", "retorno":	1	},
                {"texto":"	a casa de papel e um filme interessante	", "criterio":"	(casa ou apartamento) adj3 papel ou folha	", "retorno":	1	},
                {"texto":"	teste de texto agravo foi provido ou sei lá	", "criterio":"	agravo adj5 provido nao ('nao provido')	", "retorno":	1	},
                {"texto":"	a casa<br>grande	", "criterio":"	casa adjc10 grande	", "retorno":	0	},
                {"texto":"	as casas de papel um video interessante	", "criterio":"	(casa? ou apartamento?) adj3 papel ou folha ou papeis adj3 filme ou video adj2 interessante	", "retorno":	1	},
                {"texto":"	recurso quase especial dá-se um grande provimento no agravo em recurso especial	", "criterio":"	(RESP ou 'recurso especial') ou (Dá-se ou dou) adj4 provimento adj3 'agravo em recurso especial'	", "retorno":	1	},
                {"texto":"	a turma resolveu conceder um habeas corpus por meio desse oficio legal	", "criterio":"	(conceder adj2 'habeas corpus' adj4 'ofício')	", "retorno":	1	},
                {"texto":"	a casa de papel <br>o papel dele é interessante na série	", "criterio":"	casa COM papel COM serie	", "retorno":	0	},
                {"texto":"	a casa de papel é uma série muito interessante	", "criterio":"	casa COM papel COM serie COM interessante	", "retorno":	1	},
                {"texto":"	sendo assim, ou não, determino imediata remessa do processo feito neste órgão sempre julgador  do juízo de retratação	", "criterio":"	Determino adj4 (encaminhamento ou remessa) adj4 (autos ou processo ou feito) adj4 (órgão ou turma) adj2 julgador$ adj4 juízo adj2 retratação	", "retorno":	1	},
                {"texto":"	casas de da do papel	", "criterio":"	(casas ou apartamento) adj3 (papel ou folha ou papeis)	", "retorno":	0	},
                {"texto":"	a redução do estômago foi bem sucedida	", "criterio":"	(bariatrica ou obesidade ou gastroplastia) ou (redu$ adj2 estoma$)	", "retorno":	1	},
                {"texto":"	a turma resolveu conceder um habeas corpus por meio desse oficio legal	", "criterio":"	conceder adj2 'habeas corpus' adj4 'ofício'	", "retorno":	1	},
                {"texto":"	sendo assim, ou não, determino imediato encaminhamento dos autos deste processo ao órgão sempre julgador  do juízo de retratação	", "criterio":"	Determino adj4 (encaminhamento ou remessa) adj4 (autos ou processo ou feito) adj4 (órgão ou turma) adj2 julgador$ adj4 juízo adj2 retratação	", "retorno":	1	},
                {"texto":"	confirmando que o dano moral que pode ser estético foi assumido a	", "criterio":"	'dano moral' adj5 estético não (presumido? ou presumida?)	", "retorno":	1	},
                {"texto":"	teste de texto agravo não provido ou sei lá	", "criterio":"	agravo adj5 provido nao ('nao provido')	", "retorno":	0	},
                {"texto":"	a casa de ferro é um teste	", "criterio":"	casa ADJ1 de ADJ1 ferro e teste	", "retorno":	1	},
                {"texto":"	'sendo assim, ou não, determino imediata remessa do processo feito nesta fantástica turma sempre julgadora para o juízo de retratação'	", "criterio":"	Determino adj4 (encaminhamento ou remessa) adj4 (autos ou processo ou feito) adj4 (órgão ou turma) adj2 julgador$ adj4 juízo adj2 retratação	", "retorno":	1	},
                {"texto":"	nesse contexto, indefiro a liminar entre outras coisas mais, solicito muito mais informações	", "criterio":"	indefir$ adj4 liminar (solicit$ adj5 informações)	", "retorno":	1	},
                {"texto":"	ele fez uma bariatrica esse mês	", "criterio":"	(bariatrica ou obesidade ou gastroplastia) ou (redu$ adj2 estoma$)	", "retorno":	1	},
                {"texto":"	a b c d e f	", "criterio":"	(a adj b adj c) ou (c adj d)	", "retorno":	1	},
                {"texto":"	dano  bla material	", "criterio":"	(dano ou moral) adj2 (dano ou material)	", "retorno":	1	},
                {"texto":"	o apartamento de folha e um filme interessante	", "criterio":"	(casa ou apartamento) adj3 (papel ou folha) adj3 filme	", "retorno":	1	},
                {"texto": {"a":"esse é um teste com campos", "b":"esse outro teste com campos"}, "criterio": "(teste adj2 campos) e (outro com teste)" , "retorno":	1	},
                {"texto": {"a":"esse é o primeiro texto ", "b":"esse é o segundo texto"}, "criterio": "(primeiro com segundo)" , "retorno":	0	},
                {"texto": {"a":"esse é o primeiro texto ", "b":"esse é o segundo texto"}, "criterio": "(primeir? e segun$ e tex*)" , "retorno":	1	}]

    pb = PesquisaBR()
    pb.testes(testes = testes)

