import setuptools
#
# Para gerar o dist, executar: 
#   python setup.py sdist 

setuptools.setup(
    name="pesquisabr",
    version= '1.0.3.3',
    author="Luiz Anísio",
    author_email="",
    description="Projeto para pesquisa textual",
    long_description='Pacote base para os projetos com pesquisa textual avançada',
    long_description_content_type="text/markdown",
    url="https://github.com/luizanisio/PesquisaTextualBR",
    packages = setuptools.find_packages(),
    package_data={'':['*.md','LICENCE','*.py','*.sql','../pesquisabr_testes.py'],},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: MIT License",
        "Operating System :: OS Independent",
    ],
)

### NOTAS DE VERSÕES 
''' 
 1.0.0.5  - singularização aprimorada com lista de palavras ignoradas no falso plural
          - melhoria dos testes para as singularizações
 1.0.0.6  - correção do ADJC (erro inserido em algum teste anterior ou refactoring)
          - melhoria dos testes para o ADJC
 1.0.0.7  - reorganização e melhoria na construção do pacote pesquisabr e submódulos
          - pode-se usar:
            - from pesquisabr import PesquisaBR, RegrasPesquisaBR
            - from pesquisabr import PesquisaBRTestes
 1.0.0.8  - testes com mapas de tokenização, preparando para a primeira versão de homologação
 1.0.0.9  - testes com operador COM 1,2 e 3
          - correção de termo único entre aspas na criação do critério AON
 1.0.0.10 - não (critério especial) para AON deve ser TRUE
          - teste não (palavra1 ADJC palavra2)  ==> teste 
          - not com operadores especiais não tem como ser avaliado no AON, então o maior filtro possível é
            retirar o grupo do NOT para que o AON retorne os dados para serem filtrados pelo python depois
 1.0.0.11 - funções para grifar o texto
          - grifar_texto - permite grifar um texto recebendo um conjunto de tokens processados
          - grifar_criterios - permite grifar um texto recebendo o critério de pesquisa usado
          - com a função, é possivel mostrar para o usuário os termos no texto encontrados durante a pesquisa
            na sua forma original presente no texto
1.0.0.12  - comentado log
1.0.0.13  - correção de critérios
          - termo "termo termo"  >> virava >> termo ADJ1 "termo termo" 
          - deveria ser >> termo E "termo termo"
1.0.0.14  - correção de critérios
            - "termo1" "termo2"  >> virava >> "termo1 termo1" 
              - deveria ser >> "termo1" E "termo2"
            - "solicite-$" >> "solicite$"
1.0.0.15  - remoção de trecho de texto pelo critério - apenas nas regras
            - remover(casa de papel) - remove o texto dentro dos parênteses antes de aplicar a regra
            - remover(aspas) - remove o texto entre aspas antes de aplicar as regras
1.0.0.16  - melhoria dos curingas do operador remover(...)
          - opção para retornar todos os rótulos de um grupo ou apenas o primeiro  
1.0.0.17  - pequenos ajustes operador remover(...)
          - organização da classe de regras e extrações
1.0.1.0   - diversos ajustes na extração e regras para receber textos como lista, dict e texto puro
          - criação de testes para as novas funcionalidades de extração
          - criação de testes para os tipos e estruturas de retornos esperados
1.0.1.1   - se for solicitado o detalhamento ao aplicar as regras, as extrações ficam dentro das regras que as geraram para melhor rastreabilidade
1.0.1.2   - processar lista de texto - assumir que cada item da lista se comporta como o início de um novo parágrafo, não como campo do dict
          - correção do grifar com termos compostos - criação de testes para termos compostos grifados
1.0.1.3   - retorno de erro com critérios analisados no dicionário para apresentação
          - correções ao grifar números com separadores de milhar e decimais
1.0.1.4   - dicionário padrão reduzido
1.0.1.5   - análise de regras - correção do remover( ) em conjunto com cabeçalhos e rodapés
          - novos testes para esse cenário
          - otimização da análise de regras - cache de trechos de textos para aproveitamento
1.0.1.6   - correção de grifos em termos colados em quebras de linha
1.0.1.7   - correção de quebras de linha nos grifos e testes
1.0.1.8   - correção de resultado de extração no regex - simplificação para lista de texto
1.0.1.9   - correção do operador remover com curinga * entre aspas: remover("*****")
1.0.2.0   - novos testes dos curingas de remoção
          - critério recortar() para recorte de textos
1.0.2.1   - correção retorno vazio do recortar
1.0.2.2   - recortar com início e fim opcionais usando ? ao final do delimitador. Ex: recortar(termo1;termo2?) ou recortar(termo1?;termo2?) ou recortar(termo1?;termo2)
1.0.2.3   - limpeza de símbolos diferentes de #$.-_ no delimitador do recortar()
1.0.2.4   - critérios de regex são processados para não terem acentos e ignorarem o case
          - retorno do critério de regex quando ocorre erro, para preencher a tela do serviço com o regex enviado, incluindo o tempo de processamento
          - retorno de marcação e extração conforme texto original (não mais o texto processado)
          - correção da remoção de trecho entre aspas em textos de listas e dicionários
1.0.2.5   - <TERMO> e <FIMTERMO> prontos no regex
1.0.2.6   - correção aspas simples diferenciado de apóstrofo
1.0.2.7   - correção remover e recortar com lista de textos incluindo textos vazios
1.0.2.8   - correção remover com texto \r no lugar de \n
1.0.2.9   - erro no pesquisar por termos com curingas quando o texto é lista e fica vazio por conta do recortar
          - erro ao enviar o texto como uma lista vazia ou um dict vazio
1.0.3.0   - uso da biblioteca regex no lugar da re para uso do timeout
1.0.3.1   - objeto UtilRegrasConfig global com configuração de timeout do regex e registro de regex que geraram timeout
            bem como log de regras lentas com base na configuração
1.0.3.2   - UtilExtracaoRe - ProntosProgramados - classe com regex prontos com funções programadas 
            <CPF:99999999999> <CNPJ:99999999999999> <OAB:UF12345> <NUM:123,55>
1.0.3.3   - UtilExtracaoRe - <OAB> genérica exige lista dos estados e não apenas duas letras.
 '''

''' TODO
 - regras de extração - na extração com recortar e remover, indicar a posição correta no texto original 
                        (avaliar se é necessário pois o texto recortado já é retornado)
                      - possibilidade de ter uma extração combinada por uma regra pesquisabr
 '''