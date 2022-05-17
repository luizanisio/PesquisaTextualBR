import re
from pesquisabr import PesquisaBR, RegrasPesquisaBR

REGEX_CORRIGE_TAGS = re.compile(r'[\-|,;#\s]+')
# vai retornar as tags separadas por expaço antes e depois de cada uma
def regras_corrigir_tags_re(tags_lista):
    return '' if not tags_lista else '( ' + REGEX_CORRIGE_TAGS.sub(' ', str(tags_lista)).strip().replace(' ',' )|( ') + ' )'

def regras_corrigir_tags(tags_lista):
    return '' if not tags_lista else ' ' + REGEX_CORRIGE_TAGS.sub(' ', str(tags_lista)).strip() + ' '

def lista_regras_corrigir_tags(regras):
    for r in regras:
        r['tags'] = regras_corrigir_tags(r.get('tags'))
    return regras

# compila a lista de tags para pesquisa
def regras_regex_tags(tags_pesquisa: str):
    if not tags_pesquisa:
        return None
    return re.compile(regras_corrigir_tags_re(tags_pesquisa)) if type(tags_pesquisa) is str else tags_pesquisa

# verifica se alguma tag desejada está na lista de tags existentes
# faz uma lista de OR nas desejadas e verifica na lista de existentes
def regras_contem_tags(tags_desejadas, tags_existe):
    # se nenhuma desejada for informada, retorna true
    if not tags_desejadas:
        return True
    # se nenhuma existente for informada, retorna false
    if not tags_existe:
        return False
    #print('Verificando tag: ', tags_desejadas, tags_existe, regras_regex_tags(tags_desejadas).search(tags_existe))
    return bool(regras_regex_tags(tags_desejadas).search(tags_existe))

# retorna true para regex válido em regras ou extrações
def regex_valido(txt_regex, rotulo, retornar_erro = False):
    erro = ''
    try:
        re.compile(str(txt_regex))
        #print(f'REGEX OK: rótulo "{rotulo}" - regex: {txt_regex}')
        if retornar_erro:
            return ''
        return True
    except re.error as msgerr:
        erro = str(msgerr)
        if retornar_erro: 
           return erro
    print(f'**ERRO: REGEX inválido: "{rotulo}"')
    print(f'        texto de regex: {txt_regex}')
    print(f'                 erro : {erro}')
    return False

# verifica se a regra é válida e ignora ela caso tenha algum erro na construção
def regra_valida(txt_regra, rotulo, retornar_erro = False):
    # retira os critérios de recortar e remover para validar a regra
    #pbr = RegrasPesquisaBR()
    #if pbr.RE_REMOVER.search(txt_regra):
    #    _txt_regra = pbr.RE_REMOVER.sub(' ',txt_regra).strip()
    #    print('REMOVIDO CRITÉRIO DE REMOÇÃO')
    #    print('\t ', txt_regra)
    #    print('\t ', _txt_regra)
    #else:
    #    _txt_regra = txt_regra
    _txt_regra = RegrasPesquisaBR.RE_REMOVER.sub(' ',txt_regra).strip()
    pb = PesquisaBR(texto='', criterios=_txt_regra)
    if pb.erros:
        if retornar_erro:
            return str(pb.erros)
        print(f'**ERRO: REGRA inválida: "{rotulo}"')
        print(f'        texto de regra: {txt_regra}')
        print(f'                 erro : {pb.erros}')
        return False
    #print(f'REGRA OK: rótulo "{rotulo}" com o texto de regra: {txt_regra}')
    if retornar_erro:
        return ''
    return True