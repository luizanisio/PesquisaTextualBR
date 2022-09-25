from pesquisabr import PesquisaBR
import re
from unicodedata import normalize

RE_TOKENS = re.compile(r'(\s)|([0-9]+)|([a-zA-Z]+)|(\n+)|(\W|.)')

texto = ' . / ~[]   qualquer coisa A casa de Papel é muito massa de legal de mais ! : "teste entre aspas" número 1.234,344 11/12/2012 § <br> legal '

pb = PesquisaBR(texto=texto)

# retorna o ajuste necessário para cada posição 
# o ajuste é o número que precisa ser deslocado para voltar ao normal
def processar_posicoes_regex(texto, regex, sub, posicoes):
    deslocamento_regex = 0
    for match in regex.finditer(texto):
        _ini, _fim = match.span() 
        _txt = texto[_ini:_fim]
        _sub = regex.sub(sub,_txt)
        deslocamento_inicio, deslocamento_fim = 0, 0
        if _sub.strip() != '':
            deslocamento_inicio = len(_sub) - len(_sub.lstrip())
            deslocamento_fim = len(_sub) - len(_sub.rstrip())
            diferenca_fim = _fim - _ini - len(_sub) + deslocamento_fim
        else:
            diferenca_fim = _fim - _ini - len(_sub)
        # dif é o quanto deve somar para ficar na posição original
        if deslocamento_inicio + diferenca_fim != 0:
            _ini -= deslocamento_regex
            _fim -= deslocamento_regex
            _novas = []
            for _ in posicoes:
                if _ >= _fim - diferenca_fim:
                    _novas.append(_ + diferenca_fim)
                elif _ >= _ini:
                    _novas.append(_ + deslocamento_inicio)
                else:
                    _novas.append(_)
            posicoes = _novas
            #posicoes = [_ + deslocamento_inicio if _ >= _ini else _  for _ in posicoes]
            #posicoes = [_ + diferenca_fim if _ >= _fim - diferenca_fim  else _  for _ in posicoes]
            print(f'[{_txt}] \t [{_sub}] \t ',match.span() , _ini, _fim, deslocamento_inicio, diferenca_fim, deslocamento_regex)
            deslocamento_regex += len(_txt) - len(_sub)

    _texto = regex.sub(sub, texto)
    # corrige as posições posteriores pois foram afetadas
    return _texto, posicoes

def processar_posicoes_tokens(texto):
    _texto = pb.RE_UNICODE.sub('', normalize("NFD", str(texto) )).lower()
    posicoes = [i for i in range(len(_texto))]
    # quebras de linha
    _texto, posicoes = processar_posicoes_regex(_texto, pb.RE_QUEBRA,' ', posicoes)
    # parágrafo
    _texto, posicoes = processar_posicoes_regex(texto, re.compile('§'),' paragrafo ', posicoes)
    # normalização de símbolos
    _texto = pb.normalizar_simbolos(_texto)
    # números
    _texto, posicoes = processar_posicoes_regex(_texto, pb.RE_NUMEROS,'\\1\\3', posicoes)
    _texto, posicoes = processar_posicoes_regex(_texto, pb.RE_NUMEROS_ESPACO,'\\1\\3', posicoes)
    # quebras de linha
    _texto, posicoes = processar_posicoes_regex(_texto, pb.RE_QUEBRA,' ', posicoes)

    print('Posições processado: ',' '.join( [str(i).ljust(3) for i in range(len(_texto))]) )
    print('Posições reais     : ', ' '.join( [str(i).ljust(3) for i in posicoes]) )
    print('Texto     : ', texto)
    print('Texto novo: ', _texto.replace('\n','|'))

    # quebra os tokens finais
    _tokens = []
    for match in pb.RE_TOKENS.finditer(_texto):
        _ini, _fim = match.span()
        _txt = _texto[_ini:_fim]
        if _txt not in ('?','$','',' '):
            # busca as correções dessa posição
            novo_ini = posicoes[_ini]
            novo_fim = posicoes[_fim]
            novo_txt = texto[novo_ini:novo_fim]
            novo_txt = f'"{novo_txt}"'.replace('\n','|').ljust(10)
            _txt = f'"{_txt}"'.replace('\n','|').ljust(10)
            _tokens.append((_txt, novo_txt, _ini, _fim, novo_ini, novo_fim))
            print(f'{_txt} \t {novo_txt} \t \t {_ini} \t {_fim} \t || \t {novo_ini} \t {novo_fim}')

RE_LETRAS = re.compile('[^a-z0-9\n§]')
def processar_texto_posicoes(texto):
    # se o texto for um dict de {'campo': texto}
    if type(texto) is dict:
      _textos = dict({})
      for c,t in texto.items():
        _textos[c] = processar_texto_posicoes(texto = t)
      return _textos

    # processa o regex substituindo ' ' por '~' para manter os tokens do mesmo tamanho
    def _processar_regex(texto, regex, sub, manter_espaco = False):
        _texto = str(texto)
        for match in regex.finditer(_texto):
            _ini, _fim = match.span() 
            _txt = texto[_ini:_fim]
            _sub = regex.sub(sub,_txt).rjust(len(_txt))
            if not manter_espaco:
                _sub = _sub.replace(' ','~')
            #print(_ini, _fim, _txt, _sub)
            _texto = _texto[:_ini] + _sub + _texto[_fim:]
        return _texto

    # quebras de linha são tratadas sempre como \n não há substituição com espaçamento
    _texto = pb.RE_UNICODE.sub('', normalize("NFD", str(texto) )).lower()
    _texto = pb.RE_QUEBRA.sub('\n',_texto) 
    # números
    _texto = _processar_regex(_texto, pb.RE_NUMEROS,'\\1\\3')
    _texto = _processar_regex(_texto, pb.RE_NUMEROS_ESPACO,'\\1\\3',manter_espaco=True)
    # juntar tokens com ~
    tokens = [ pb.singulariza(t.replace('~','')).ljust(len(t)).replace(' ','~') for t in _texto.split(' ')]
    return ' '.join(tokens)

def grifar_texto(texto, marcar_tokens = [], tag_ini='<mark>', tag_fim='</mark>'):
    # se o texto for um dict de {'campo': texto}
    if type(texto) is dict:
      _textos = dict({})
      for c,t in texto.items():
        _textos[c] = grifar_texto(texto = t, marcar_tokens=marcar_tokens, tag_ini=tag_ini, tag_fim=tag_fim)
      return _textos

    if (not texto) or len(marcar_tokens) == 0:
        return texto
    _texto_espacado = ' ' + pb.RE_QUEBRA.sub('\n',texto) + ' '
    _texto_processado = processar_texto_posicoes( _texto_espacado )
    posicoes = []
    print('Texto original: ', _texto_espacado.replace('\n','|'))
    print('Texto espaçado: ', _texto_processado.replace('\n','|'))
    print('Marcar os tokens: ', marcar_tokens)
    for t in marcar_tokens:
        if not t:
            continue
        _t = t.strip().replace(' ','[ ~]*').replace('?','[a-z0-9]{0,1}').replace('$','[a-z0-9]*')
        rg = f'~*{_t}~*'
        for match in re.finditer(rg,_texto_processado):
            posicoes.append(match.span())
        print('Regex: ', rg, ' encontrados: ', len(list(re.finditer(rg,_texto_processado))))
    posicoes.sort(key=lambda k:k[0])
    print('Posições: ', posicoes)
    pos = 0
    texto_final = ''
    for ini, fim in posicoes:
        texto_final += _texto_espacado[pos:ini] + tag_ini + _texto_espacado[ini:fim] + tag_fim
        pos = fim
    texto_final += _texto_espacado[pos:]        
    return texto_final.strip()

RE_CURINGAS_NO_TERMO = re.compile(r'[\$\?]')
def grifar_criterios(texto, criterios, tag_ini='<mark>', tag_fim='</mark>', sinonimos = []):
    # se o texto for um dict de {'campo': texto}
    if type(texto) is dict:
      _textos = dict({})
      for c,t in texto.items():
        _textos[c] = grifar_criterios(texto = t, criterios=criterios, tag_ini=tag_ini, tag_fim=tag_fim, sinonimos=sinonimos)
      return _textos

    if (not texto) or (not criterios):
        return texto
    pb = PesquisaBR(texto='', criterios=criterios)
    #print('critérios: ', pb.tokens_criterios)
    # cria uma lista de tokens simples e compostos
    tokens = []
    composto = []
    literal = False
    for tk in pb.tokens_criterios:
        if pb.RE_OPERADOR.search(tk):
            literal = False
            continue
        if tk == '"' and literal:
           if len(composto) > 0:
              tokens.append(' '.join(composto))
              composto = []
           literal = False
           continue
        elif tk == '"':
            literal = True
            continue
        if tk in {'(',')'}:
            continue
        if literal:
            composto.append(tk)
            continue
        tokens.append(tk)
        # busca os sinônimos se o termo não tiver curinga
        if (sinonimos != None) and (not RE_CURINGAS_NO_TERMO.search(tk) ):
            for t in sinonimos.get(tk,[]):
                if not t in tokens:
                    tokens.append(t)
    if len(composto) > 0:
        tokens.append(' '.join(composto))
    if ('paragrafo' in tokens) and ('§' not in tokens):
        tokens.append('§')
    elif ('§' in tokens) and ('paragrafo' not in tokens):
        tokens.append('paragrafo')
    return grifar_texto(texto, marcar_tokens=tokens, tag_ini=tag_ini, tag_fim=tag_fim)

texto = ' A "Casa de Papel" R$ 1.234,33 legais. <br> Um bla-ble-bli outros textos § 5, é muito legal alegre e feliz!'
#texto = 'papel § legal <br> nada'
#texto = 'legal <br> nada § e tudo 1.234,33 outro'
#texto = 'a <br> 1.234,33 outro'
#texto = 'texto § 5, é'
criterios='"casa de papel" E lega$ E alegr? E 123433'
pb = PesquisaBR(texto=texto, criterios=criterios)
texto_posicoes = pb.processar_texto_posicoes(texto)
#print('Texto        : ', texto.replace('\n','|'))
#print('Texto final  : ', texto_posicoes.replace('\n','|'))

texto_grifado =pb.grifar_criterios(texto)
print('==========================================================================')
print('Texto Marcado  : ', texto_grifado )

texto_grifado = pb.grifar_criterios({'texto1':texto, 'texto2':'muito legal e bom d+'})
print('==========================================================================')
print('Texto Marcado  : ', texto_grifado )

#processar_posicoes_tokens(texto)
exit()
#print(pb.tokens_texto)
texto = ' texto § legal'
texto = pb.normalizar_simbolos(texto)
REG = re.compile('§')
for match in REG.finditer(texto):
    _ini, _fim = match.span()
    _txt = texto[_ini:_fim]    
    _sub = REG.sub(' paragrafo ',_txt)
    print( f'{_ini} -> {_fim} :: {_txt} :: {_sub}')

pos = processar_posicoes_regex(texto, REG, ' paragrafo ', [])
print(pos)    