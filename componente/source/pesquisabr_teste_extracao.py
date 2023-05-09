from pesquisabr import UtilExtracaoRe

texto = '<OAB>'
#novo = UtilExtracaoRe.__processar_prontos_funcao__(texto)
novo = UtilExtracaoRe.preparar_regex_pronto(texto)
print('Texto:', texto)
print('Novo :', novo)
