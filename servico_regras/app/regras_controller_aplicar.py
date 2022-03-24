###################################################################
# componente de pesquisa
from copy import deepcopy
from pesquisabr import PesquisaBR, RegrasPesquisaBR


###################################################################
from app_config import obj_regras_model
###################################################################
from regras_controller import regras_filtradas, regras_filtradas_cache, get_msg_resumo_regras, get_exemplo
from regras_util import lista_regras_corrigir_tags

###################################################################
###################################################################
# retorno dos dados do health
def get_dados_health():
    criterios = 'casas ADJ2 papeis PROX10 legal PROX10 seriado remover(teste)'
    texto = 'a casa teste teste de teste teste papel teste é teste um teste seriado muito legal'
    pbr = RegrasPesquisaBR()
    texto_r, criterios_r = pbr.remover_texto_criterio(texto, criterios)
    if texto_r:
        texto = texto_r 
        criterios = criterios_r
    pb = PesquisaBR(texto=texto, criterios=criterios, print_debug=False)
    if (pb.erros) or (not pb.retorno()):
       print('\n\n')
       print('=========================================================')
       print('=    ERRO NO CRITÉRIO DE PESQUISA DO HEALTH CHECK       =')
       pb.print_resumo() 
       print('=========================================================')
       print('\n\n')
       raise Exception(f'Health check - ERRO na avaliação do critério de pesquisa')
    print(f'\n===== HEALTH CHECK OK ({get_msg_resumo_regras()}) =====\n')
    return {'ok': True, 'criterios': pb.criterios, 'criterios_aon': pb.criterios_and_or_not, 'texto': pb.texto }

# exemplo: chaves_filtros = {'ano_regra' : 2001, 'tipo_regra': 'tipo1'}
#          filtros são as chaves do json de entrada do POST do serviço que não tem relação com as regras
# algumas chaves são de uso interno, então são ignoradas como filtros
CHAVES_NAO_FILTROS = {'texto', 'regra', 'detalhar',
                      'extrair','grifar','tags',
                      'primeiro_do_grupo', 'exemplo', 
                      'analisar-criterios', 'analisar-regras',
                      'regras_externas', 'rodando-testes'}
def get_chaves_filtros(dados):
    return {c: v for c, v in dados.items() if c.lower() not in CHAVES_NAO_FILTROS}


###################################################################
###################################################################
# pacote de dados para analisar regras carregadas
# chaves_filtros é um dict com chave:valor para filtrar 
# as regras que contenham o mesmo conjunto preenchido 
def analisar_regras(dados, front_end = False):
    obj_regras_model.conversao_entrada(dados, front_end = front_end, analisar_regras = True)
    # para o caso de lista de textos
    _texto = dados.get('texto', '')
    if type(_texto) is list:
       res = {}
       pagina = 0
       for txt in _texto:
           pagina += 1
           if txt.strip():
              _dados = deepcopy(dados)
              _dados['texto'] = txt
              _dados = analisar_regras(_dados, front_end=front_end)
              # inclui a página nas extrações e regras - iniciando de 1
              _extracoes = _dados.get('extracoes',[])
              for ex in _extracoes:
                  ex['pagina'] = pagina
              _regras = _dados.get('regras',[])
              for rg in _regras:
                  rg['pagina'] = pagina
              # dados numéricos - soma os resultados
              res['qtd_regras'] = res.get('qtd_regras',0) + _dados.get('qtd_regras',0)
              res['tempo'] = res.get('tempo',0) + _dados.get('tempo',0)
              # listas - concatena os resultados
              if 'extracoes' in _dados:
                 res['extracoes'] = res.get('extracoes',[]) + _extracoes
              if 'regras' in _dados:
                 res['regras'] = res.get('regras',[]) + _regras
              if 'rotulos' in _dados:
                 res['rotulos'] = res.get('rotulos',[]) + _dados['rotulos']
              # textos - cria uma lista das respostas
              if 'texto' in _dados or 'texto' in res:
                 res['texto'] = res.get('texto',[]) + [_dados.get('texto','')]
              if 'texto_analise' in _dados or 'texto_analise' in res:
                 res['texto_analise'] = res.get('texto_analise',[]) + [_dados.get('texto_analise')]
              if 'texto_regex' in _dados:
                 res['texto_regex'] = res.get('texto_regex',[]) + [_dados.get('texto_regex','')]
       res['front-end'] = front_end
       res['analisar-regras'] = True
       return res

    _texto = dados.get("texto","")
    _detalhar = str(dados.get("detalhar","")) not in ("","0","False")
    _extrair = str(dados.get("extrair","1")) not in ("","0","False")
    _tags = str(dados.get("tags",""))
    _primeiro_do_grupo = bool(dados.get("primeiro_do_grupo"))
    _carregar_exemplo = int(dados.get("exemplo",-1))
    if _carregar_exemplo>=0:
        exemplo = get_exemplo(_carregar_exemplo)
        if exemplo:
            _texto = exemplo['texto'] if exemplo.get('texto') else _texto

    pbr = RegrasPesquisaBR(regras=[], print_debug=False)
    # não envia as regras como parâmetro para o construtor para não reprocessar a ordenação, 
    # só para diminuir o tempo de processamento
    # filtra as regras com uma das tags e com todos os filtros preenchidos nas chaves
    # caso receba regras para análise, envia elas para os filtros mas sem cache
    chaves_filtros = get_chaves_filtros(dados)
    if 'regras_externas' in dados:
        # para o caso de regras externas, é necessário padronizar as tags e ordenar as regras
        regras_externas = lista_regras_corrigir_tags( pbr.ordenar_regras( dados.get('regras_externas') ) )
        #print('Regras externas rca: ', dados.get('regras_externas'))
        #print('Regras externas padronizadas: ', regras_externas)
        #print('Chaves: ', chaves_filtros)
        #print('tags: ', _tags)
        pbr.regras = regras_filtradas(_tags, chaves_filtros = tuple(chaves_filtros.items()), 
                                      regras_externas = regras_externas )
    else:
        pbr.regras = regras_filtradas_cache(_tags, chaves_filtros = tuple(chaves_filtros.items()))
    res = pbr.aplicar_regras(texto=_texto, detalhar=_detalhar, primeiro_do_grupo = _primeiro_do_grupo, extrair= _extrair)
    if _detalhar:
       res['texto_analise'] = _texto
    # para o conversor       
    res['front-end'] = front_end
    res['analisar-regras'] = True
    if dados.get('rodando-testes'):
       res['rodando-testes'] = True
    obj_regras_model.conversao_retorno(res)
    return res

###################################################################
###################################################################
# pacote de dados para analisar um texto e o critérios informados
# texto_analise é o texto original
# criterios_analise é o texto original de critérios ou os critérios processados
# criterios_ok = SIM / NÃO se os critérios foram atendidos
def analisar_criterios(dados, front_end = False):
    obj_regras_model.conversao_entrada(dados, front_end = front_end, analisar_criterios = True)
    _texto = dados.get("texto","")
    _texto = _texto if type(_texto) is dict or type(_texto) is list else str(_texto)
    _criterios = str(dados.get("criterios","")) or str(dados.get("criterio",""))
    _detalhar = str(dados.get("detalhar","")) not in ("","0","False")
    _grifar = str(dados.get("grifar","")) not in ("","0","False")
    _extrair = str(dados.get("extrair","1")) not in ("","0","False")
    _carregar_exemplo = int(dados.get("exemplo",-1))
    if _carregar_exemplo>=0:
        exemplo = get_exemplo(_carregar_exemplo)
        if exemplo:
            _texto = exemplo['texto'] if exemplo.get('texto') else _texto
            _criterios = exemplo['criterios'] if exemplo.get('criterios') else _criterios
    res = RegrasPesquisaBR.aplicar_criterios(texto = _texto, 
                                              criterios= _criterios,
                                              extrair= _extrair, 
                                              detalhar= _detalhar, 
                                              grifar= _grifar)
    if _detalhar:
       res['texto_analise'] = _texto 
    # para o conversor       
    res['front-end'] = front_end
    res['analisar-criterios'] = True
    if dados.get('rodando-testes'):
       res['rodando-testes'] = True
    obj_regras_model.conversao_retorno(res)
    return res

def analisar_criterio_remover_trechos(texto, criterios):
    if not (RegrasPesquisaBR.RE_REMOVER.search(criterios) or RegrasPesquisaBR.RE_REMOVER_ASPAS.search(criterios)):
        #print('nenhum critério especial')
        return texto, criterios
    # remoção de trechos e aspas - caso receba os critérios especiais
    # há um processamento extra de processamento do texto que pode ser otimizado futuramente
    rpbr = RegrasPesquisaBR()
    # verifica o número de aspas, se for ímpar, ignora a remoção de aspas.
    if (texto.count('"') % 2 == 1) or (texto.count("'") % 2 ==1):
        _texto = texto.replace('"',' ').replace("'",' ')
    else:
        _texto = texto
    # verifica se existe critério de remoção de aspas do texto original
    _texto_sem_aspas, _ = rpbr.remover_texto_aspas(_texto,criterios)
    _texto = _texto if _texto_sem_aspas is None else _texto_sem_aspas
    # remove trechos do texto processado
    pb = PesquisaBR(texto=_texto)
    _texto = pb.texto #' '.join(pb.tokens_texto)
    _texto_removido, _criterios_removido = rpbr.remover_texto_criterio(_texto, criterios)
    '''
    print('Remoção de trechos: ')
    print(f'\t critérios:  {criterios}')
    print(f'\t critérios com remoção: {_criterios_removido}')
    print(f'\t texto: ', texto)
    print(f'\t novo : ', _texto_removido)
    '''
    if _texto_removido or _criterios_removido:
        return _texto_removido, _criterios_removido
    return _texto, criterios

