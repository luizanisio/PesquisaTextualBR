#from copy import deepcopy
#from random import random, shuffle
#from pesquisabr import PesquisaBR
#from pesquisabr import PesquisaBRTestes, TESTES_COMPLETOS, TESTES_TEXTOS, TEXTO_BASE, TESTES_CRITERIOS, TESTES_GRIFAR, TESTES_CABECALHO_RODAPE
from pesquisabr.pesquisabr import PesquisaBR
from pesquisabr import RegrasPesquisaBR, UtilExtracaoRe
import json

TESTE_SRV = False

def teste_remover():
    texto_original = ['antes nada inicio texto Acentuação teste fim depois nada', 
                      'antes b inicio100 teste TAMBÉM ACENTUAÇÃO texto fim100 depois b']
    texto_original = {'a': '"teste entre aspas" antes nada inicio texto Acentuação nada123 teste fim depois nada', 
                      'b': 'antes b inicio100 "teste entre aspas" teste TAMBÉM ACENTUAÇÃO texto fim100 depois b'}
    criterios = 'r:teste.*texto recortar($inicio$;$fim$) recortar($inicio100$;$fim100$) remover(texto) remover(aspas)'
    teste_remover_tc(texto_original, criterios)

def teste_remover_aspas():
    #texto_original = 'início texto "trecho a ser removido entre aspas\' aspas  teste e trecho com "aspas completas d\'água " a\'a b\'b'
    #texto_original = [texto_original, texto_original, '']
    texto_original = 'blá blá blá inicio-teste 123 456 789'
    #criterios = 'texto adj teste recortar($texto$;$teste$)'
    criterios = 'r:a recortar($inicio teste$)'
    teste_remover_tc(texto_original, criterios)

def teste_remover_tc(texto_original, criterios):
    if TESTE_SRV:
        srv_teste_remover_tc(texto_original, criterios)
        return
    pb = RegrasPesquisaBR()
    texto = UtilExtracaoRe.processar_texto(texto_original)
    texto_p, criterio_p, texto_o = pb.remover_texto_criterio(texto = texto, criterios=criterios, texto_original=texto_original)
    if texto_p is None:
        print('- - SEM REMOÇÃO - -')
        texto_p, criterio_p, texto_o = texto, criterios, texto_original

    print('Texto_original (RAW)  : ', type(texto_original), texto_original)
    print('Texto_processado (RAW): ', type(texto), texto)
    print('Texto_original (corte)  : ', type(texto_o), texto_o)
    print('Texto_processado (corte): ', type(texto_p), texto_p)

    if criterio_p[:2].lower() == 'r:':
       criterio_p = criterio_p[2:]
       print('Critérios processados (regex): ', criterio_p)
       retorno = UtilExtracaoRe.extrair_regex(texto= texto_p, criterio=criterio_p, texto_original=texto_o)
    else:
       print('Critérios processados (pesquisabr): ', criterio_p)
       pb = PesquisaBR(texto = texto_p, criterios= criterio_p) 
       retorno = pb.retorno()
    print('Retorno: ', retorno)
    print()

def srv_teste_remover_tc(texto_original, criterios):
    pb = RegrasPesquisaBR()
    dados = pb.aplicar_criterios(texto=texto_original, criterios=criterios, detalhar = 1, extrair = 1, grifar = 1)
    for c,v in dados.items():
        print(f'{c} = ', f'|{v}|')
    print()

def teste_regras():
    regras = [{"grupo" : "grupo", "rotulo": "teste1", "regra": "r:texto.*teste recortar($inicio$;$fim$) remover(nada*3)"},
              {"grupo" : "grupo", "rotulo": "teste2", "regra": "r:teste.*texto recortar($inicio100$;$fim100$) remover(nada)"}]
    texto = ['antes nada inicio texto Acentuação teste fim depois nada', 
                      'antes b inicio100 teste TAMBÉM ACENTUAÇÃO texto fim100 depois b']
    texto = {'a': 'antes nada inicio texto Acentuação nada123 teste fim depois nada', 
                      'b': 'antes b inicio100 teste TAMBÉM ACENTUAÇÃO texto fim100 depois b'}
    pb = RegrasPesquisaBR(regras = regras)
    retorno = pb.aplicar_regras(texto, detalhar=True, extrair=True, primeiro_do_grupo=False)
                
    print('Retorno: ', json.dumps(retorno, indent=2, ensure_ascii=False))

def teste_regras2():
    regras = [
    {"grupo" : "grupo", "rotulo": "teste4", "regra": "teste texto recortes cabecalho rodape nao aspas nao trecho nao aaa nao bbb  remover(aspas) remover(aaa) remover(bbb)", "qtd_cabecalho":0, "qtd_rodape":0},
    {"grupo" : "grupo", "rotulo": "teste5", "regra": "teste texto recortes cabecalho rodape nao aspas nao aaa nao bbb  remover(aspas) remover(aaa) remover(bbb)", "qtd_cabecalho":50, "qtd_rodape":50},
    {"grupo" : "grupo", "rotulo": "teste44", "regra": "teste texto recortes cabecalho rodape nao aspas nao trecho nao aaa nao bbb  remover(aspas) remover(aaa) remover(bbb)", "qtd_cabecalho":0, "qtd_rodape":0},
    {"grupo" : "grupo", "rotulo": "teste55", "regra": "teste texto recortes cabecalho rodape nao aspas nao aaa nao bbb  remover(aspas) remover(aaa) remover(bbb)", "qtd_cabecalho":50, "qtd_rodape":50}
    ]
    texto = "teste de texto 'trecho aspas' aaa bbb com recortes de cabecalho e rodape"
    pb = RegrasPesquisaBR(regras = regras)
    retorno = pb.aplicar_regras(texto, detalhar=True, extrair=True, primeiro_do_grupo=False)
                
    print('Retorno: ', json.dumps(retorno, indent=2, ensure_ascii=False))

def teste_recortar():
    texto_o = 'antes b inicio100 teste TAMBÉM ACENTUAÇÃO texto fim100 depois b'
    texto = UtilExtracaoRe.processar_texto(texto_o)
    novo, novo_o = RegrasPesquisaBR.recortar_texto(texto,'inicio100','fim100', texto_o)
    print('Novo : ', novo)
    print('Orig.: ', novo_o)

def teste_ordinal():
    texto= "juizo de 1º grau  "
    criterio= 'juízo adj3 "1º" adj3 grau'
    print('Texto original: ', texto)
    print('Processado: ', UtilExtracaoRe.processar_texto(texto) )
    pb = PesquisaBR(texto = texto, criterios=criterio)
    pbr = RegrasPesquisaBR()
    print('Tokens_texto: ', ' '.join(pb.tokens_texto) )
    print('Texto aspas: ', pbr.padronizar_aspas(texto) )
    print('Extração: ', UtilExtracaoRe.processar_texto(texto) )
    t,c,__ = pbr.remover_texto_criterio(UtilExtracaoRe.processar_texto(texto), f'{criterio} remover(nada) recortar(de;grau)', texto)
    print('Removido: ', t)
    pb.print_resumo()    

def teste_recortar_vazio():
    texto = ['','esse texto será recortado e ficará vazio', 'esse também',' e mais esse','']
    criterios = 'nada$ nad? $nada ?ada recortar(#titulo#)'
    pbr = RegrasPesquisaBR()
    t, c , _ = pbr.remover_texto_criterio(UtilExtracaoRe.processar_texto(texto), criterios, texto)
    pb = PesquisaBR(texto=t, criterios=c)
    pb.print_resumo()

def teste_posicao_pagina():
    texto = ['pagina primeira','pagina segunda', 'pagina terceira da lista','pagina quarta da lista',' pagina final']
    texto = {'a':'pagina primeira','b':'pagina segunda', 'c':'pagina terceira da lista','d':'pagina quarta da lista','e':' pagina final'}
    #texto = '\n'.join(texto)
    criterios = 'pagina adj3 lista nao final'
    pb = PesquisaBR(texto=texto, criterios=criterios)
    pb.print_resumo()
    analises = pb.analisar_mapa_pesquisa(retornar_analises=True)
    print('Análises: ', analises)
    extracoes = []
    grifado = pb.grifar_criterios(texto, extracoes = extracoes)
    print('Grifado: ', grifado)
    print('Extracoes: ', extracoes)


if __name__ == "__main__":
    print('##############################################')
    print('>> TESTE BÁSICOS - REGRAS ')

    #teste_regras2()
    #teste_remover()
    #TESTE_SRV = True
    #teste_remover_aspas()
    #teste_recortar()
    #teste_ordinal()
    #teste_recortar_vazio()
    teste_posicao_pagina()





def teste_criterios():
    pb=RegrasPesquisaBR()
    #texto = 'Teste de texto removido e com trecho entre aspas "esse trecho tem que sair" ok'
    texto = ''' AgRg no RECURSO EM HABEAS CORPUS Nº 162.417 - SP (2022/0082238-4)
RELATOR :   MINISTRO REYNALDO SOARES DA FONSECA
AGRAVANTE   :   L F T 
ADVOGADOS   :   EDUARDO MITHIO ERA  - SP300064 
        HERIO FELIPPE MOREIRA NAGOSHI  - SP312121 
AGRAVADO    :   MINISTÉRIO PÚBLICO DO ESTADO DE SÃO PAULOEMENTA
AGRAVO REGIMENTAL NO RECURSO ORDINÁRIO EM HABEAS CORPUS. DIVULGAÇÃO DE CENA DE SEXO OU DE PORNOGRAFIA COM O FIM DE VINGANÇA OU HUMILHAÇÃO (ART. 218-C, §1º, DO CP). ALEGAÇÃO DE FALTA DE JUSTA CAUSA PARA O EXERCÍCIO DA ATIVIDADE PERSECUTÓRIA. VÍCIOS NÃO CONSTATADOS. DENÚNCIA QUE ATENDE AOS REQUISITOS DO ART. 41 DO CPP. EXISTÊNCIA DE ELEMENTOS INDICATIVOS DE AUTORIA E DE MATERIALIDADE DO DELITO. AGRAVO REGIMENTAL NÃO PROVIDO.
1. O agravo regimental deve trazer argumentos suficientes para infirmar os fundamentos da decisão agravada, sob pena de vê-la mantida por seus próprios fundamentos.
2. O trancamento de ações penais ou inquéritos policiais pela via do habeas corpus somente é viável quando houver constatação, de plano, de inépcia da peça inaugural ou da atipicidade da conduta atribuída ao acusado ou, ainda, quando houver superveniência de causa extintiva da punibilidade ou ausência de elementos mínimos que demonstrem a autoria ou a materialidade do delito.
3. Neste caso, não se constata, de plano, nenhum vício apto a ensejar o encerramento da ação penal. Os autos trazem elementos que indicam ter sido o agravante o responsável pela divulgação de fotos íntimas da vítima, enviadas a ele durante o período em que mantiveram um relacionamento amoroso, em grupos de WhatsApp após o término do envolvimento.
4. Por ora, não é possível acolher a versão acusatória nem defensiva, sobretudo na estreita via do habeas corpus, cujo escopo não permite o exame aprofundado de fatos e provas, mas limita-se à apreciação de matéria pré-constituída e que não depende de dilação probatória.
5. Agravo regimental não provido.ACÓRDÃO
Visto, relatados e discutidos os autos em que são partes as acima indicadas, acordam os Ministros da Quinta Turma do Superior Tribunal de Justiça,  por unanimidade, negar provimento ao agravo regimental.  Os Srs. Ministros Ribeiro Dantas, Joel Ilan Paciornik, Jesuíno Rissato (Desembargador Convocado do TJDFT) e João Otávio de Noronha votaram com o Sr. Ministro Relator.Brasília (DF), 19 de abril de 2022(Data do Julgamento)
Ministro REYNALDO SOARES DA FONSECA 
Relator
AgRg no RECURSO EM HABEAS CORPUS Nº 162.417 - SP (2022/0082238-4)
RELATOR :   MINISTRO REYNALDO SOARES DA FONSECA
AGRAVANTE   :   L F T 
ADVOGADOS   :   EDUARDO MITHIO ERA  - SP300064 
        HERIO FELIPPE MOREIRA NAGOSHI  - SP312121 
AGRAVADO    :   MINISTÉRIO PÚBLICO DO ESTADO DE SÃO PAULOAgRg no RECURSO EM HABEAS CORPUS Nº 162.417 - SP (2022/0082238-4)VOTO
O EXMO. SR. MINISTRO REYNALDO SOARES DA FONSECA: 
O agravo regimental é tempestivo e preenche os demais requisitos formais exigidos pelo art. 1.021 do Código de Processo Civil e art. 258 do Regimento Interno do Superior Tribunal de Justiça. No entanto, não obstante os esforços do agravante, não constato elementos suficientes para reconsiderar a decisão, cujos fundamentos devem ser preservados.
Em primeiro lugar, constata-se a ausência de quaisquer argumentos ou alegações novas, distintas daquelas já expostas no recurso ordinário anteriormente apreciado, de modo a facultar a modificação da decisão aqui impugnada.
Esta Corte Superior de Justiça possui inúmeros julgados nesse sentido, que ilustro com os seguintes precedentes:
PROCESSO PENAL. AGRAVO REGIMENTAL DA DECISÃO QUE INDEFERIU O PEDIDO DE DESBLOQUEIO DE VALORES EM CONTA BANCÁRIA. IMPENHORABILIDADE NÃO DEMONSTRADA. AGRAVO REGIMENTAL DESPROVIDO.
I - O agravo regimental deve trazer novos argumentos capazes de alterar o entendimento anteriormente firmado, sob pena de ser mantida a decisão recorrida por seus próprios fundamentos.
(...)
Agravo regimental desprovido. (AgRg nos EmbAc 35/DF, Rel. Ministro FRANCISCO FALCÃO, Corte Especial, DJe 18/11/2021)
AGRAVO REGIMENTAL NO HABEAS CORPUS. AUSÊNCIA DE NOVOS ARGUMENTOS. DECISÃO MANTIDA POR SEUS PRÓPRIOS FUNDAMENTOS. AGRAVO REGIMENTAL DESPROVIDO.
1. "O agravo regimental deve trazer novos argumentos capazes de alterar o entendimento anteriormente firmado, sob pena de ser mantida a decisão vergastada por seus próprios fundamentos." (AgRg no RMS 60.369/SC, Rel. Ministro LEOPOLDO DE ARRUDA RAPOSO (DESEMBARGADOR CONVOCADO DO TJ/PE), QUINTA TURMA, julgado em 19/11/2019, DJe 26/11/2019).
2. Hipótese em que o agravante limita-se a reiterar mesma argumentação lançada nas razões do habeas corpus, sem apresentar qualquer fato novo tendente à modificação do julgado que, por tal razão, deve ser mantido por seus próprios fundamentos.
3. Agravo regimental desprovido. (AgRg no HC 671.106/SP, Rel. Ministro RIBEIRO DANTAS, Quinta Turma, DJe 9/8/2021)
AGRAVO REGIMENTAL NO HABEAS CORPUS. WRIT NÃO CONHECIDO. PENA RESTRITIVA DE DIREITOS. CUMPRIMENTO INTEGRAL. SANÇÃO DE MULTA. DÍVIDA DE VALOR. INADIMPLEMENTO. EXTINÇÃO DA PUNIBILIDADE INCABÍVEL. NOVOS ARGUMENTOS PARA DESCONSTITUIR O DECISUM UNIPESSOAL. AUSÊNCIA. INVIOLABILIDADE DO DOMICÍLIO. SUPRESSÃO DE INSTÂNCIA. AGRAVO NÃO PROVIDO.
1. No julgamento da ADI n. 3.150/DF, o Supremo Tribunal Federal atribuiu à multa penal a condição de dívida de valor e não lhe retirou o caráter de sanção penal, por força do disposto no art. 5º, XLVI, ?c?, da Constituição da República. A partir de então, a Terceira Seção desta Corte superou o entendimento outrora firmado no Recurso Especial representativo de controvérsia n. 1.519.777/SP, de modo que é incabível a extinção da punibilidade do agente até que a pena de multa seja adimplida.
2. É assente neste Tribunal Superior que o agravo regimental deve trazer novos argumentos ou documentos inéditos capazes de infirmar a decisão agravada, sob pena de manutenção do decisum pelos próprios fundamentos.
3. A tese de inviolabilidade do domicílio do réu não foi apreciada pela Corte estadual, razão por que a análise da questão por este Tribunal Superior ensejaria a indevida supressão de instância.
4. Agravo não provido. (AgRg no HC 668.497/SC, Rel. Ministro ROGERIO SCHIETTI CRUZ, Sexta Turma, DJe 22/10/2021)
Conforme já mencionado, busca-se o trancamento da ação penal movida contra o agravante, destinada a apurar sua participação no delito previsto o art. 218-C, §1º, do Código Penal.
Reiterando a excepcionalidade do trancamento de ações penais pela via do habeas corpus, destaco que, muito embora seja possível o controle de legalidade de processos penais e de procedimentos de investigação preliminares pela via mandamental, tal procedimento somente se mostra possível quando evidenciada ofensa aos requisitos da peça acusatória ou quando se constatar, de plano, a ocorrência de causa superveniente extintiva da punibilidade ou, ainda, quando não houver indícios mínimos de autoria ou prova da materialidade.
Neste caso, não obstante os reiterados esforços da defesa, a decisão deve ser mantida por seus próprios fundamentos, pois não se constata vício na peça acusatória, que atende, de maneira satisfatória, às exigências do já mencionado art. 41 do Código de Processo Penal. 
As instâncias antecedentes destacaram a existência de fortes indícios de autoria, coletados no curso das investigações. As teses defensivas estão relacionadas diretamente ao mérito da própria ação penal, que devem ser debatidas na arena adequada. 
De fato, as teses levantadas neste agravo regimental estão relacionadas ao cerne da controvérsia jurídica instaurada e depende de verticalizado exame do conjunto probatório carreado aos autos, cuja apreciação, neste momento e nesta via estreita de cognição, não é possível.
Ilustrativamente:
AGRAVO REGIMENTAL NO RECURSO ORDINÁRIO EM HABEAS CORPUS. PLEITO DE TRANCAMENTO DA AÇÃO PENAL. JUSTA CAUSA. REQUISITOS DO ART. 41 DO CPP. MATÉRIA A SER APRECIADA NA INSTRUÇÃO PROCESSUAL. REVOLVIMENTO FÁTICO-PROBATÓRIO NÃO REALIZADO NA ORIGEM. NO MAIS, NÃO ENFRENTAMENTO DOS FUNDAMENTOS DA DECISÃO AGRAVADA. SÚMULA 182/STJ. AGRAVO DESPROVIDO.
I - Nos termos da jurisprudência consolidada nesta eg. Corte Superior, cumpre ao agravante impugnar especificamente os fundamentos estabelecidos na decisão agravada.
II - In casu, há indícios necessários para a persecução penal, uma vez que o d. Ministério Público estadual, na narrativa constante da inicial acusatória, asseverou estar presente a justa causa à ação penal, de forma também a cumprir os requisitos do art. 41 do Código de Processo Penal, não sendo, portanto, o caso de trancamento prematuro da ação penal.
III - Vejamos alguns trechos da exordial acusatória(fls. 244-249):"(...) ao longo dos anos de 2014 a 2016, os denunciados, consciente e voluntariamente, em comunhão de ações e desígnios, associaram-se, de forma estável e duradoura, em Campo Grande, nesta Cidade, para o fim específico de cometerem crimes contra a Administração Pública no âmbito do Posto Regional de Polícia Técnico-Científica de Campo Grande, Órgão da Polícia Civil do Estado do Rio de Janeiro. O denunciado (...), médico legista da Polícia Civil deste Estado que atualmente exerce mandato de Vereador à Câmara Municipal do Rio de Janeiro, então na qualidade de Diretor Geral do Posto Regional de Polícia Técnico-Científica de Campo Grande, implantou um esquema criminoso no âmbito daquele órgão, valendo-se do cargo de direção que ocupava, em concurso com os demais denunciados, no qual exigia e recebia pagamentos ilícitos para que os cadáveres que davam entrada no aludido posto médico legal por morte natural, não violenta ou suspeita, fossem liberados e devidamente preparados para o funeral e consequente enterro. Para tanto, os denunciados (...) mantinham gestões junto às funerárias da região Santa Madalena, Fonseca, Flor de Campo Grande, Itaguaí e Rio Pax, bem como junto ao Hospital Municipal Pedro II, ao Hospital Rocha Faria, ao Hospital Albert Schweitzer e ao Hospital Estadual Eduardo Rabelo, com vistas a receberem os corpos de pessoas mortas por causas naturais, de modo a facilitarem, sob a aparência de suposta exigência de necropsia, a burocracia relativa aos atos de sepultamento, em troca de vantagem pecuniária indevida. (...) Desta forma, os denunciados transformaram o Posto Pericial de Campo Grande em lucrativa empresa de serviços funerários, inclusive, utilizando funcionários terceirizados, contratados pela Administração para manutenção e limpeza do prédio (...) Note-se que o Posto de Polícia Técnica de Campo Grande apresenta, estatisticamente, um número de atendimentos por morte natural extraordinariamente superior ao número de perícias por morte violenta, fato único dentre os 21 (vinte e um) órgãos semelhantes existentes na estrutura da Polícia Civil, incrementando-se nos últimos anos de 2015 e 2016 (...) igualmente utilizando-se da estrutura pública e das posições de direção por eles ocupadas, promovendo retaliações funcionais contra aqueles que não aderissem aos seus propósitos escusos."
IV - Conforme assentado no próprio acórdão de origem (fls. 75-103): "a imputação se dirigiu ao fato de que o referido delito estar-se-ia relacionado a sua função pública de perito médico legista e Diretor Geral do Posto Regional de Polícia Técnico-Científica de Campo Grande e não, como busca creditar os impetrantes, na função que ele exercia à época e que continua a exercer de vereador do Município do Rio de Janeiro, circunstância essa que apenas e tão somente o levou ao declínio de competência do 1º Grupo de Câmaras Criminais deste Egrégio Tribunal de Justiça para o Juízo de Direito da 26ª Vara Criminal da Comarca da Capital após o novo entendimento firmado pelo Excelso Supremo Tribunal Federal."
V - Assente nesta eg. Corte Superior que "o trancamento da ação penal em sede de habeas corpus é medida excepcional, somente se justificando se demonstrada, inequivocamente, a ausência de autoria ou materialidade, a atipicidade da conduta, a absoluta falta de provas, a ocorrência de causa extintiva da punibilidade ou a violação dos requisitos legais exigidos para a exordial acusatória, o que não se verificou na espécie" (HC n. 359.990/SP, Sexta Turma, Relª. Minª. Maria Thereza de Assis Moura, DJe de 16/9/2016).
VI - Diante de todo o exposto, embora as memoráveis considerações tecidas pela d. Defesa do agravante, não houve qualquer equívoco na decisão impugnada, na medida em que, além de inexistir qualquer causa de trancamento da ação penal comprovada de plano, sem a necessária incursão fático-probatória, as questões apresentadas dizem respeito diretamente ao mérito da ação penal e serão analisadas durante a instrução processual.
VII - No mais, a d. Defesa limitou-se a reprisar os argumentos do recurso ordinário em habeas corpus, o que atrai a Súmula n. 182 desta eg. Corte Superior de Justiça, segundo a qual é inviável o agravo regimental que não impugna especificamente os fundamentos da decisão agravada.
Agravo regimental desprovido. (AgRg no RHC 148.958/RJ, Rel. Ministro JESUÍNO RISSATO ? Desembargador convocado do TJDFT, Quinta Turma, DJe 16/12/2021)
PROCESSO PENAL. AGRAVO REGIMENTAL DA DECISÃO QUE NEGOU PROVIMENTO AO RECURSO ORDINÁRIO. TRANCAMENTO DA AÇÃO PENAL. TESE DE INÉPCIA DA DENÚNCIA. DENÚNCIA FORMALMENTE APTA. DESCRIÇÃO SUFICIENTEMENTE PORMENORIZADA. CRIME DE AUTORIA COLETIVA. JUSTA CAUSA. PROVA DE MATERIALIDADE. INDÍCIOS SUFICIENTES DE AUTORIA. COLABORAÇÃO PREMIADA. ELEMENTOS AUTÔNOMOS DE CORROBORAÇÃO. REVOLVIMENTO DE FATOS E PROVAS. INVIÁVEL. AGRAVO REGIMENTAL DESPROVIDO.
I - O agravo regimental deve trazer novos argumentos capazes de alterar o entendimento anteriormente firmado, sob pena de ser mantida a r. decisão vergastada por seus próprios fundamentos.
II - O trancamento da ação penal constitui medida de exceção que se justifica apenas quando estiverem comprovadas, de plano e sem necessidade de exame aprofundado de fatos e provas, a inépcia da exordial acusatória, a atipicidade da conduta, a presença de excludente de ilicitude ou de causa de extinção de punibilidade ou a ausência de indícios mínimos de autoria ou de prova de materialidade.
III - Justa causa para a ação penal condenatória é o suporte probatório mínimo ou o conjunto de elementos de fato e de direito que evidenciam a probabilidade de confirmar-se a hipótese acusatória deduzida em juízo. Constitui, assim, uma plausibilidade do direito de punir, extraída dos elementos objetivos coligidos nos autos, os quais devem demonstrar satisfatoriamente a prova de materialidade e os indícios de que o denunciado foi o autor de conduta típica, ilícita (antijurídica) e culpável.
IV - A denúncia deve descrever de modo suficientemente claro, concreto e particularizado os fatos imputados, em uma dimensão que, ao mesmo tempo, demonstre a plausibilidade e verossimilhança da tese acusatória e permita ao acusado defender-se efetivamente das imputações, em prestígio aos princípios da ampla defesa e do contraditório. Contudo não se pode exigir que deva narrar exaustivamente todos os elementos que importam à apreciação da res in judicio deducta, os quais, fundamentalmente, só poderão ser conhecidos no curso da instrução processual.
V - Nos crimes de autoria coletiva, conquanto não se possa exigir a descrição pormenorizada da conduta de cada denunciado, é necessário que a peça acusatória estabeleça, de modo objetivo e direto, a mínima relação entre o denunciado e os crimes que lhe são imputados.
O entendimento decorre tanto da aplicação imediata do art. 41 do CPP como dos princípios constitucionais da ampla defesa, do contraditório, da individualização das penas e da pessoalidade.
VI - Na Ação Penal 5068162-95.2019.4.04.7000, imputa-se a Cesar Luiz de Godoy Pereira a prática de crimes de corrupção ativa e lavagem de capitais. Narra-se que o agravante, no período compreendido entre 2/12/2008 e 29/4/2012, na condição de proprietário da empresa Alusa Engenharia Ltda., pagou vantagens ilícitas no total de R$ 5.954.380, 81 a Paulo Roberto Costa, então Diretor de Abastecimento da Petrobras, a fim de que, em contrapartida, fosse-lhe garantida a celebração de quatro contratos de obras e serviços entre a sua empresa e a estatal relacionados ao Complexo Petroquímico do Rio de Janeiro (COMPERJ) e à Refinaria Abreu e Lima (RNEST). Para a efetivação dos pagamentos, teriam sido empregadas empresas de fachada para emissão de cheques e simulação de contratos de mútuo.
VII - A denúncia descreve de modo suficientemente pormenorizado diversos atos praticados por Paulo Roberto Costa, na condição de Diretor de Abastecimento da Petrobras ao tempo dos fatos, que em tese configuram crimes de corrupção passiva aos quais se vinculariam os crimes de corrupção ativa atribuídos ao recorrente. Esses atos, que se inseriam nas atribuições cometidas a Paulo Roberto Costa, teriam, em seu conjunto, viabilizado a celebração dos quatros contratos de obras e serviços cuja ilegalidade se sustenta.
VIII - Com relação à justa causa para a ação penal, os elementos de informação que lastrearam a peça acusatória não se resumiram a declarações de colaboradores premiados e a documentos produzidos unilateralmente por estes. Ao contrário, consistiram também de planilhas eletrônicas apreendidas por meio de mandados de busca e apreensão, de relatórios de visitas na Petrobras, que evidenciam contatos frequentes entre o agravante e Paulo Roberto Costa, dos contratos celebrados entre a Alusa Engenharia e a MR Pragmática e a Bas Consultoria, de notas fiscais e comprovantes de pagamentos, entre outros elementos.
IX - O exame das teses veiculadas pelo agravante, no sentido e na profundidade que pretende, absolutamente excede os limites da cognição do habeas corpus, que não admite dilação probatória. O provimento jurisdicional por que a Defesa pugna nesta via é de natureza tal que só pode ser alcançado ao término da instrução processual, por ocasião da sentença, pois exigiria apreciação abrangente e aprofundada do vasto acervo de elementos de cognição que instruem os autos da ação penal na origem.
X - O exame de eventuais questões concernentes à materialidade e à autoria delitiva, no quanto excederem os limites objetivos da cognição sumária, própria à apreciação desta ação mandamental, não dispensa aprofundado revolvimento fático-probatório da matéria reunida nos autos até o presente momento. Impõe-se, assim, que sua discussão seja reservada à instrução processual, seu âmbito natural.
Agravo regimental desprovido. (AgRg no RHC 137.951/PR, Rel. Ministro FELIX FISCHER, Quinta Turma, DJe 9/4/2021)
RECURSO EM HABEAS CORPUS. CRIME DE FRAUDE À LICITAÇÃO. LAVAGEM OU OCULTAÇÃO DE BENS, VALORES E DINHEIRO. PEDIDO DE TRANCAMENTO DA AÇÃO PENAL POR INÉPCIA DA INICIAL. INDICAÇÃO DE FATOS CONCRETOS. POSSIBILIDADE DE EXERCÍCIO PLENO DO DIRIETO DE DEFESA. AUSÊNCIA DE INÉPCIA. PROSSEGUIMENTO DA AÇÃO PENAL. AUSÊNCIA DE CONSTRANGIMENTO ILEGAL.
1. No que concerne ao pedido de trancamento da ação penal, destaque-se que a providência perseguida somente é possível, na via estreita do habeas corpus, em caráter excepcional, quando se comprovar, de plano, a inépcia da denúncia, a atipicidade da conduta, a incidência de causa de extinção da punibilidade ou a ausência de indícios de autoria ou de prova da materialidade do delito [...] (AgRg no RHC n. 122.377/RJ, Ministro Reynaldo Soares da Fonseca, Quinta Turma, DJe 21/9/2020).
2. As questões de ordem probatória, nesta fase de recebimento da denúncia, são analisadas sob o filtro da justa causa. E, nesse ponto, o habeas corpus não se apresenta como via adequada ao trancamento da ação penal, quando o pleito se baseia em falta de justa causa (ausência de suporte probatório mínimo à acusação), não relevada, primo oculi. Intento que demanda revolvimento fático-probatório, não condizente com a via restrita do writ.
3. A Constituição Federal fixa o rol de competências do Superior Tribunal de Justiça no art. 105, de modo que o conhecimento de matérias não debatidas em habeas corpus na origem subverte a estrutura constitucional, acarretando supressão de instância, caso conhecidas na via eleita neste Tribunal Superior.
4. Recurso em habeas corpus parcialmente conhecido e, nessa extensão, improvido. Agravo Regimental n. 955.055/2021 prejudicado. (RHC 135.474/SP, Rel. Ministro SEBASTIÃO REIS JÚNIOR, Sexta Turma, DJe 21/2/2022)
Diante do exposto, nego provimento a este agravo regimental.
É como voto.
Ministro REYNALDO SOARES DA FONSECA
Relator
Números Origem:  15034318820198260361  19212019  22347317220218260000
EM MESA JULGADO: 19/04/2022
    SEGREDO DE JUSTIÇA
Relator
Exmo. Sr. Ministro  REYNALDO SOARES DA FONSECA
Presidente da Sessão
Exmo. Sr. Ministro JOEL ILAN PACIORNIK
Subprocurador-Geral da República
Exmo. Sr. Dr. MÁRIO FERREIRA LEITE 
Secretário
Me. MARCELO PEREIRA CRUVINEL
AUTUAÇÃO
RECORRENTE  :   L F T 
ADVOGADOS   :   EDUARDO MITHIO ERA  - SP300064 
        HERIO FELIPPE MOREIRA NAGOSHI  - SP312121 
RECORRIDO   :   MINISTÉRIO PÚBLICO DO ESTADO DE SÃO PAULO 
ASSUNTO: DIREITO PENAL - Crimes contra a Dignidade Sexual
AGRAVO REGIMENTAL
AGRAVANTE   :   L F T 
ADVOGADOS   :   EDUARDO MITHIO ERA  - SP300064 
        HERIO FELIPPE MOREIRA NAGOSHI  - SP312121 
AGRAVADO    :   MINISTÉRIO PÚBLICO DO ESTADO DE SÃO PAULO 
CERTIDÃO
Certifico que a egrégia QUINTA TURMA, ao apreciar o processo em epígrafe na sessão realizada nesta data, proferiu a seguinte decisão:
"A Turma, por unanimidade, negou provimento ao agravo regimental."
Os Srs. Ministros Ribeiro Dantas, Joel Ilan Paciornik, Jesuíno Rissato (Desembargador Convocado do TJDFT) e João Otávio de Noronha votaram com o Sr. Ministro Relator.
'''

    '''    criterios = 'sair remover("*********************"  "*********************"  "*********")'
        texto = texto[-500:]
        texto_r, criterio_r = pb.remover_texto_criterio(texto = texto, criterios = criterios)
        print('Texto removido: ', texto_r)
        print('Critério removido: ', criterio_r)
        '''

    '''
    texto_original = 'teste de inicio E um texto com acentuação e CASE fim teste final'
    texto = UtilExtracaoRe.processar_texto(texto_original)
    texto_p, texto_o = pb.recortar_texto(texto = texto, inicio = 'inicio', fim = 'fim',texto_original = texto_original)
    print('Texto_processado: ', texto_p)
    print('Texto_original  : ', texto_o)
    print()

    criterios = 'teste remover(texto*case)'
    texto_original = 'teste de inicio E um texto com acentuação e CASE fim teste final Outra Acentuação mantida'
    texto = UtilExtracaoRe.processar_texto(texto_original)
    texto_p, criterio_p, texto_o = pb.remover_texto_criterio(texto = texto, criterios=criterios,texto_original = texto_original)
    print('Texto_processado: ', texto_p)
    print('Texto_original  : ', texto_o)
    print('Critérios processados: ', criterio_p)
    print()

    texto_p, criterio_p, texto_o = pb.remover_texto_criterio(texto = texto, criterios=criterios)
    print('Texto_processado: ', texto_p)
    print('Texto_original  : ', texto_o)
    print('Critérios processados: ', criterio_p)
    print()
    '''
 
