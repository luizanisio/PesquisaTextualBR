<hr>

### Reestruturação (jan/2020)
- Aproveitando as férias e estou reestruturando em um componente instalável, em breve estará disponibilizado
- Estou ajustando também o uso com o memsql enquanto aplico os componentes em um projeto para produção
- O componente já pode ser usado com o serviço de regras, basta baixar a pasta **componente**
<hr>

# Pesquisa textual em documentos
Essa é uma proposta de <b>pesquisa textual</b> implementada com recursos em **python puro** com o uso de dicionário de **sinônimos** e **distância entre termos** pesquisados. <br>
- É uma pesquisa que tenta ir além do que pesquisas comuns fazem, pois não tem o objetivo de trazer grandes volumes de resultados, mas **resultados precisos**. <br>
- Implementada em **python** para uso em pesquisa textual avançada com foco no **Português**, permitindo busca em campos textuais e critérios de proximidade textual.<br>
- O objetivo é refinar pesquisas textuais com frameworks comuns de mercado (MemSQL/SingleStore, ElasticSearch) em volume muito grande de dados, ou pode ser usada para pesquisa completa em textos. Ou análise em tempo real se textos correspondem a critérios pré estabelecidos (regras de texto para mudança de fluxo de trabalho).<br>
- Essa ideia não é nova, conheci ao longo dos últimos 20 anos vários sistemas que faziam algo parecido. Não há pretensão em competir com qualquer um desses produtos, mas ter algo simples e operacional para quem tiver interesse em personalizar uma busca textual da forma que precisar.<br>
- Uma aplicação muito útil dos critérios de pesquisa, alé de encontrar textos, é identificar **rótulos** que são aplicáveis a um texto ao testar um conjunto de regras pré-definidas com seus rótulos correspondentes, simulando um **classificador multilabel** só que no lugar do modelo, tem-se um conjunto de regras textuais. Daí pode-se identificar fluxos automáticos para sistemas, definir alertas, etc.

### Estão disponíveis nesse repositório:
<ul>
  <li>Classe python <b>PesquisaBR()</b> que recebe um documento e um critério de pesquisa e retorna a avaliação.</li>
  <li>Classe python <b>RegrasPesquisaBR()</b> que recebe um conjunto de regras e seus rótulos e aplica as regras em um documento, identificando que rótulos são aplicáveis a ele. Simula um modelo multilabel mas com regras no lugar de um modelo de IA.</li>
  <li><b>Serviço avaliador de regras</b>: Um exemplo simples de serviço que simula um classificador multilabel que funciona por regras no lugar de um modelo treinado.</li>
  <li><b>Testes da classe</b> que permitem validar todos os critérios e funcionalidades implementadas</li>
  <li><b>Conversor de pesquisas</b> com critérios avançados para critérios simples AND OR NOT aceitos pelo MemSQL</li>
  <li>Classe <b>PesquisaBRMemSQL()</b>(https://github.com/luizanisio/PesquisaTextualBR/blob/master/PesquisaMemSQL.md): classe que permite combinar a análise de pesquisa da classe PesquisaBR com o poder de pesquisa textual nativo do MemSQL(https://www.memsql.com/). Agora o MemSQL chama-se SingleStore(https://www.singlestore.com/)</li>
</ul>

### Uso simples da classe:

```py
pb = PesquisaBR(texto = 'A casa de papel é um seriado muito legal', criterios='casa adj2 papel adj5 seriado')
print('Retorno: ', pb.retorno())

print(pb.print_resumo())
```
Console
```bat
Retorno:  True
RESUMO DA PESQUISA: retorno = True
 - texto: a casa de papel e um seriado muito legal
 - tokens: ['a', 'casa', 'de', 'papel', 'e', 'um', 'seriado', 'muito', 'legal']
 - tokens_unicos: {'papel', 'a', 'um', 'muito', 'de', 'e', 'seriado', 'legal', 'casa'}
 - criterios: ['casa', 'adj2', 'papel', 'adj5', 'seriado']
 - mapa: {'a': {'t': [0], 'p': [0], 'c': ['']}, 'casa': {'t': [1], 'p': [0], 'c': ['']}, 'de': {'t': [2], 'p': [0], 'c': ['']}, 'papel': {'t': [3], 'p': [0], 'c': ['']}, 'e': {'t': [4], 'p': [0], 'c': ['']}, 'um': {'t': [5], 'p': [0], 'c': ['']}, 'seriado': {'t': [6], 'p': [0], 'c': ['']}, 'muito': {'t': [7], 'p': [0], 'c': ['']}, 'legal': {'t': [8], 'p': [0], 'c': ['']}}
```

### Uso simples da classe de regras:
```py
regras = [{'grupo' : 'receitas_bolo', 'rotulo': 'Receita de Bolo', 'regra': 'receita ADJ10 bolo'},
          {'grupo' : 'receitas_bolo', 'rotulo': 'Receita de Bolo', 'regra': 'aprenda ADJ5 fazer ADJ10 bolo'},
          {'grupo' : 'receitas_pao', 'rotulo': 'Receita de Pão', 'regra': 'receita PROX15 pao'},
          {'grupo' : 'grupo teste', 'rotulo': 'teste', 'regra': 'teste'}]
# receita de bolo
texto = 'nessa receita você vai aprender a fazer bolos incríveis'
pbr = RegrasPesquisaBR(regras = regras, print_debug=False)
rotulos = pbr.aplicar_regras(texto = texto)
print(f'Rótulos encontrados para o texto: "{texto}" >> ', rotulos)
```
Console
```bat
Rótulos encontrados para o texto: "nessa receita você vai aprender a fazer bolos incríveis" >>  ['Receita de Bolo']
```


### Testes básicos da classe
Estão disponíveis diversos textos e pesquisas que são testados para garantir o funcionamento da classe durante o desenvolvimento.
```py
pb.testes()
```

Console (onde AON é a simplificação da pesquisa para AND OR NOR)
```bat
---------------------------------------
Teste: 0 - texto 123 uu aeiouaaocaeiouaaoc  ==> esperado True
   AON => texto AND 123 AND uu AND aeiouaaocaeiouaaoc
---------------------------------------
Teste: 1 - casa adj2 papel  ==> esperado True
   AON => casa AND papel
---------------------------------------
Teste: 2 - 'numero 123' prox3 interessante  ==> esperado True
   AON => "numero 123" AND interessante
---------------------------------------
Teste: 3 - casa adj6 seriado  ==> esperado True
   AON => casa AND seriado
   ```

### Pesquisa textual avançada

Implementei aqui um conjunto de operadores de pesquisa por proximidade dos termos e outros operadores para refinamento de pesquisa. Esses tipos de operadores tornam-se importantes para refinar pesquisas em grande volume de dados, onde não é importante trazer muito resultado, mas um resultado o mais próximo possível do que é procurado. Ferramentas comuns de busca como <b>ElasticSearch</b> e o próprio <b>MemSQL</b> não trazem nativamente esses tipos de operadores. 
<p>Essa ideia não é nova, conheci ao longo dos últimos 20 anos vários sistemas que faziam algo parecido. Não há pretensão em competir com qualquer um desses produtos, mas ter algo simples e operacional para quem tiver interesse em personalizar uma busca textual da forma que precisar. 
<p> Esse tipo de pesquisa permite o uso de dicionário de sinônimos em qualquer língua, inclusive o uso de recursos fonéticos. O texto de entrada é pré-processado para evitar não encontrar termos com grafia incorreta de acentos ou termos no singular/plural, bem como números com pontuação ou sem. Por padrão o texto é pesquisado no singular, removendo pronomes oblíquos, mas é possível localizar o termo real usando aspas (exceto acentos que sempre são desconsiderados).
<p> A pesquisa também permite localizar termos pelo dicionário de sinônimos. Ao pesquisar a palavra "genitor", o sistema pesquisa também "pai". A tabela de sinônimos é flexível e facilmente atualizável, permitindo incluir termos em outras línguas se desejado. O uso de sinônimos pode ser ativado ou desativado a cada pesquisa. Ao pesquisar termos entre aspas, o sinônimo é desativado para o termo ou conjunto de termos entre aspas enquanto os outros termos podem ser pesquisados com o uso dos sinônimos.

<p> O pré-processamento envolve:
<ul>
  <li> retirada de <b>acentos</b> </li>
  <li> redução a um <b>pseudosingular</b> ou <b>singular estimado</b>: não é um português perfeito, mas uma singularização para a máquina localizar termos com maior flexibilidade</li>
</ul>

#### Conectores ou operadores de pesquisa

Conectores ou operadores de pesquisa são termos especiais utilizados em sistemas de pesquisa para indicar a relação desejada entre os termos pesquisados. Por exemplo, se é desejado encontrar documentos com a palavra <i>casa</i> e a palavra <i>papel</i>, pode-se escrever o critério de pesquisa como <b>casa papel</b> ou pode-se escrever <b>casa E papel</b>. O operador <b>E</b> está subentendido quando nenhum operador é informado. Para usar termos que são iguais aos operadores, é necessário colocar o termo entre aspas. Ex.: <b>amor e ódio</b> deveria ser escrito como <b>amor "e" ódio</b> para garantir que os três termos existem no texto. Ou também <b>"amor e ódio"</b> para que os termos sejam exigidos nessa sequência, um seguido do outro.  
<ul>
  <li> <b>E</b>: conector padrão, exige a existência do termo no documento</li>
  <li> <b>NÃO</b>: nega a existência de um termo no documento </li>
  <li> <b>OU</b> entre termos: indica que um ou outro termo podem ser encontrados para satisfazer a pesquisa ex.: | "fazer" OU "feito" E casa | realiza uma pesquisa que encontre (fazer ou feito literalmente) e também (casa ou termos que no singular sejam escritos como casa)</li>
  <li> <b>OU</b> com parênteses: permite realizar pesquisas mais complexas. Ex.: | (casa ADJ5 papel) ou (casa ADJ5 moeda) |. Nesse caso a pesquisa poderia ser simplificada como | casa ADJ5 papel ou moeda |</li>
  <li> <b>ADJ</b>n: permite localizar termos que estejam até n termos a frente do primeiro termo. Ex.: | casa ADJ3 papel | vai localizar textos que contenham "casa de papel", "casa papel", "casa feita de papel", mas não localizaria "casa feita de muito papel". </li>
  <li> <b>ADJC</b>n: equivalente ao <b>ADJ</b> padrão, mas obriga que os dois termos estejam presentes no mesmo parágrafo. Não necessariamente a mesma sentença, mas o mesmo parágrafo considerando a quebra <b>/n</b> no texto </li>
  <li> <b>PROX</b>n: semelhante ao <b>ADJ</b>, mas localiza termos posteriores ou anteriores ao primeiro termo pesquisado. Ex.: | casa PROX3 papel | vai localizar textos que contenham "casa de papel", "papel na casa", "papel colado na casa", "casa feita de papel", mas não localizaria "casa feita de muito papel" ou "papel desenhado e colado na casa".</li>
  <li> <b>PROXC</b>n: equivalente ao <b>PROX</b> padrão, mas obriga que os dois termos estejam presentes no mesmo parágrafo. Não necessariamente a mesma sentença, mas o mesmo parágrafo considerando a quebra <b>/n</b> no texto </li>
  <li> <b>COM</b>n: obriga que os dois termos pesquisados estejam presentes em um mesmo parágrafo, independente da distância e da ordem. Ex.: | casa COM papel | avalia se o texto contém "casa" e papel em um mesmo parágrafo, em qualquer ordem e distância. Opcionalmente pode-se informar o número de parágrafos. COM1 avalia se os termos estão no mesmo parágrafo, COM2 avalia no parágrafo e o seguinte, e assim por diante. </li>
  <li> <b>MESMO</b>: os documentos podem ser indexados com um tipo único, ou com tipos independentes como, por exemplo: resumo, dados textuais complementares e o texto original. O operador MESMO permite que o documento seja encontrado apenas se os termos pesquisados estiverem em um mesmo tipo do documento. Sem o operador MESMO, o texto será localizado se tiver um termo em um tipo (resumo por exemplo) e outro termo em outro tipo (índice remissivo, por exemplo). O operador MESMO funciona apenas como substituição do operador <b>E</b>, pois os operdores ADJ, ADJC, PROX, PROXC e COM subentendem o uso do operador MESMO por usarem recrusos de distância entre termos. Ex.: | casa MESMO papel | vai localizar textos que contenham "casa" E "papel" no mesmo tipo de documento, caso o termo "casa" esteja no resumo e "papel" esteja no índice, o texto não será localizado.</li>  
</ul>

#### Curingas

<ul>
  <li> <b>$</b>: permite o uso de partes do termo no critério de pesquisa. Por exemplo: cas$ vai encontrar casa, casinha, casamento...</li>  
  <li> <b>?</b>: permite a existência ou não te um caracter no lugar do símbolo "?". Por exemplo: cas? vai encontrar cas, casa, caso, case... Pode estar no meio do termo tamém: ca?a vai encontrar caa, casa, cata, cala ... </li>  
</ul>

#### Exemplo de configuração de sinônimos

* ao encontrar um termo no texto analisado, os sinônimos são mapeados como se fossem esse termo
** sinônimos compostos são analisados apenas para termos entre aspas nos critérios de pesquisa
<ul>
  <li> <b>Sinônimos</b>: {'alegre': ['feliz','sorridente'], 'feliz':['alegre','sorridente'], 'sorridente':['alegre','feliz'], 'casa':['apartamento'] } </li>
  <li> <b>Sinônimos compostos</b>: {'casa_de_papel':['la casa de papel','a casa de papel'], "inss" : ['instituto nacional de seguridade social'], 'instituto_nacional_de_seguridade_social':['inss']}</li>
</ul>

Com esse mapeamento, se o critério de pesquisa estiver escrito "alegre" é o mesmo que pesquisar (alegre ou feliz ou sorridente). Se estiver escrito "alegre" entre aspas, os sinônimos não serão pesquisados.
Os sinônimos compostos possuem um comportamento peculiar, permitem o mapeamento de expressões, siglas, etc. Se o critério de pesquisa estiver escrito "inss" é o mesmo que pesquisar (inss ou "instituto nacional de seguridade social"). Mas se no critério de pesquisa estiver escrito inss sem aspas, somente será pesquisada a palavra inss.

#### Exemplo de textos, texto com campos

* esses textos serão usados mais abaixo
<ul>
  <li> <b>Texto único</b>: A casa de papel é um seriado muito interessante</li>
  <li> <b>Texto composto</b>: {'texto' : 'A casa de papel é um seriado muito interessante', 'tipo' : 'seriado', 'ano': '2017', 'comentario': 'seriado muito bom'} </li>
</ul>

#### Exemplo de pesquisas simples

* o operador E é padrão para pesquisas sem operadores entre termos
* ao pesquisar "papeis", a pesquisa vai localizar no texto o termo "papel", pois o texto estará singularizado e o critério de pesquisa também
<ul>
  <li> <b>Termos simples</b>: casa papel</li>
  <li> <b>Termos simples com curingas</b>: casa? E papeis</li>
  <li> <b>Termos simples com operadores</b>: casa E papel E seriado</li>
  <li> <b>Termos simples com operadores e parênteses</b>: (casa E papel) ou (papel E seriado)</li>
  <li> <b>Termos literias</b>: "casa de papel" E seriado</li>
  <li> <b>Termos próximos</b>: casa ADJ2 papel ADJ5 seriado</li>
  <li> <b>Termos próximos em qualquer ordem</b>: papel PROX2 casa ADJ10 seriado</li>
  <li> <b>Termos no mesmo parágrafo</b>: papel PROX2 casa COM seriado</li>
</ul>

#### Exemplo de pesquisas em campos

* operadores especiais alteram o comportamento da pesquisa. Ao colocar um termo no critério de pesquisa seguido de .nomo_campo., o critério será analisado apenas no campo informado.
** um conjunto de critérios pode ser analisado no campo colocando (termo1 E termo2).nome_campo.
** combinações mais complexas podem ser feitas em conjuntos de critérios (termo1.campo1. E termo2 E termo3).campo2. - operadores de campos internos serão avaliados no lugar dos externos quando existirem.
<ul>
  <li> <b>critérios por campo</b>: (papel PROX2 casa).texto. E 2017.ano=.</li>
  <li> <b>campo ANO>=2017</b>: papel PROX2 casa E 2017.ano>=.</li>
  <li> <b>critérios por campo</b>: (papel PROX2 casa).texto. E 2017.ano=.</li>
  <li> <b>critérios por campo (escrita alternativa)</b>: (papel PROX2 casa).texto. E @ano=2017 </li>
  <li> <b>critérios por campos diferentes</b>: (papel PROX2 casa).texto. E 2017.ano=. E "muito bom".comentario.</li>
</ul>

#### Exemplo de pesquisas simples com sinônimos

* palavras simples são analisadas como se fossem seus sinônimos. Os sinônimos simples são desativados em termos entre aspas.
* os sinônimos compostos são analisados apenas em palavras entre aspas no critério de pesquisa
<ul>
  <li> <b>apartamento = casa</b>: papel PROX2 apartamento ADJ10 seriado</li>
  <li> <b>Sinônimos</b>: papel PROX2 apartamento ADJ10 seriado</li>
</ul>

### Usando a classe Python

Exemplos disponíveis no arquivo <b>testes_exemplos.py</b> e <b>testes_exemplos_sem_db.py</b>
Para uso da classe <b>PesquisaBRMemSQL</b> é necessário ter instalado o <b>MemSQL</b> (pode ser o container de exemplo). E criar as tabelas e funções do database <b>pesquisabr</b>. Scripts disponívels <b>db_funcoes.sql</b> e <b>db_tabelas.sql</b>

### Serviço para avaliar textos e retornar os rótulos deles com base em regras pré-definidas

Esse é um serviço simples de exemplo do uso da classe de avaliação de regras para gerar um classificador multilabel por regras.<br>
O arquivo *regras.json* contém uma lista de regras de exemplo. As regras podem estar em um banco de dados que o serviço carrega ao subir, ou em um arquivo texto mesmo. Depois basta chamar o serviço passando o texto que ele retorna os rótulos aplicáveis com base nas regras carregadas.
A responsabilidade do serviço é rotular o texto recebido, comportando-se como um classificador multilabel por regras.<br>
Opcionalmente pode-se informar ao serviço que regras devem ser testadas, passando uma **tag** ou conjunto de tags ou o nome do grupo da regra.<br>
É possível usar **regex** no lugar dos critérios textuais para regras mais refinadas. Para isso, basta registrar a regra com **r:** no início da regra. Ex.: *r:oficio \\d+* <br>
O serviço de exemplo está na subpasta: **servico_regras** da pasta do projeto (https://github.com/luizanisio/PesquisaTextualBR/tree/master/projeto_e_exemplos/servico_regras).

### Uso simples do serviço:
- POST: http://localhost:8000/analisar_criterio
```json
{"texto": "esse é um texto legal", "criterio": " texto PROX10 legal", "detalhar": "1"}
```
Retorno
```json
{ "criterios": "texto PROX10 legal", "criterios_aon": "texto AND legal", "retorno": true, "texto": "esse e um texto legal" }
```

- POST: http://localhost:8000/analisar_regras
```json
{"texto": "esse  texto tem umas receitas de pão e de bolos legais 123 456 um dois três com o oficio número 5.174", "detalhar":0}
```
Retorno
```json
{ "extracoes": [["oficio numero 5174"],[],["receita de pao"]], 
  "rotulos": ["oficio","Receita de Bolo","Receita de PÃ£o"] }
```

- POST: http://localhost:8000/analisar_regras
- o *detalhar=1* nesse exeplo retorna a regra identificada por cada rótulo e o texto processado*
- a chave opcional *tags* pode ser usada para filtras e avaliar apenas regras que contenham uma das tags
- a chave opcional *grupo* pode ser usada para filtrar e avaliar apenas regras de um determinado grupo
```json
{"texto": "esse ofício 12 texto tem umas receitas de pão e de bolos legais 123 456 um dois são vários testes três com o oficio número 5.174", 
 "detalhar":0, "tags":"oficio"}
```
Retorno
```json
{ "extracoes": [ [ "12", "numero 5174" ] ],
    "rotulos": [ "oficio" ]  }
```

Regras desse exemplo (arquivo regras.json):
- as chaves tags, qtd_cabecalho e qtd_rodape são opcionais
- *regra*: é a regra usando os operadores de pesquisa textual, ou um regex. No caso de regex, a regra deve começar com r: regex desejado
- *rotulo*: é o rótulo do grupo que será retornado se a regra retornar true
- *qtd_cabecalho*: a regra é aplicada no início do texto até o caracter da posição informada
- *qtd_rodape*: a regra é aplicada no final do texto, do caracter da posição informada até o fim
- *qtd_cabecalho* e *qtd_rodape*: a regra é aplicada removento o miolo do texto de qtd_cabecalho até qtd_rodape
```json
{"regras": [
    {"grupo" : "receitas_bolo", "rotulo": "Receita de Bolo", "regra": "receita ADJ10 bolo", "tags": "receita bolo", "qtd_cabecalho":0, "qtd_rodape":0},
    {"grupo" : "receitas_bolo", "rotulo": "Receita de Bolo", "regra": "aprenda ADJ5 fazer ADJ10 bolo", "tags": "receita bolo", "qtd_cabecalho":0, "qtd_rodape":0},
    {"grupo" : "receitas_pao", "rotulo": "Receita de Pão", "regra": "receita PROX15 pao", "extracao": "(receita.*pao)|(pao.*receita)", "tags": "receita pao", "qtd_cabecalho":0, "qtd_rodape":0},
    {"grupo" : "grupo_teste", "rotulo": "teste", "regra": "teste", "extracao": "(\\d+)(\\Wum\\W|\\Wdois\\W|\\Wtres\\W)", "tags": "teste", "qtd_cabecalho":0, "qtd_rodape":0},
    {"grupo" : "grupo_regex", "rotulo": "teste regex", "regra": "r:teste|testar?", "extracao": "", "tags": "teste", "qtd_cabecalho":0, "qtd_rodape":0},
    {"grupo" : "grupo_oficio", "rotulo": "oficio", "regra": "r:oficio (n.{1,10})?\\d+", "extracao": "(?<=oficio\\W)(?:n|numero|num|nro)?(?:\\s*\\d+)(?=$|\\W)" , "tags": "teste oficio", "qtd_cabecalho":20, "qtd_rodape":20}
 ]
}
```
