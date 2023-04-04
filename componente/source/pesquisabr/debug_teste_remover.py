from pesquisabr import RegrasPesquisaBR, PesquisaBR

rpbr = RegrasPesquisaBR()
pbr = PesquisaBR()
texto = None
texto_p = None
criterios = None
texto_r, criterios_r = None, None
criterios_remocoes = None

def teste1():
    global texto, texto_p, criterios, criterios_r, texto_r
    texto = 'teste de remoção curingas removidos com sucesso "aspas removidas" \n fim da linha'
    texto_p = pbr.processar_texto(texto)
    criterios = 'teste remover(teste) remover(remocao) remover(curin*#)'
    texto_r, criterios_r = rpbr.remover_texto_criterio(texto_p, criterios)

def teste2():
    global texto, texto_p, criterios, criterios_r, texto_r
    texto = 'esse é um teste de receita de pao e bolo com remoção'
    texto_p = pbr.processar_texto(texto)
    criterios = 'receita OU pao OU bolo remover(de receit*#) remover(e bolo) remover(de pao)'
    texto_r, criterios_r = rpbr.remover_texto_criterio(texto_p, criterios)

def teste3():
    global texto, texto_p, criterios, criterios_r, texto_r, criterios_remocoes
    texto = 'teste entre aspas "usando" "testando"'
    texto_p = pbr.processar_texto(texto)
    criterios = 'usando testando remover("usando") remover("tes*ndo")'
    texto_r, criterios_r = rpbr.remover_texto_criterio(texto_p, criterios)
    criterios_remocoes = rpbr.retornar_criterios_remocao(criterios)

def teste4():
    global texto, texto_p, criterios, criterios_r, texto_r, criterios_remocoes
    texto = 'casa termo1 termo2 termo3 termo4 de papel'
    texto_p = pbr.processar_texto(texto)
    criterios = 'casa adj2 papel termo1 termo2 termo3 termo4 remover(termo&)'
    texto_r, criterios_r = rpbr.remover_texto_criterio(texto_p, criterios)
    criterios_remocoes = rpbr.retornar_criterios_remocao(criterios)

teste4()    

print('Texto: ', texto)
print('Critérios: ', criterios)
print('Texto removido: ', texto_r)
print('Critérios removidos: ', criterios_r)
print('Remoções: ', criterios_remocoes)
print('Remover aspas? ', rpbr.RE_REMOVER_ASPAS.search(criterios))

