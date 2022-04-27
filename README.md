# Pesquisa textual em documentos
Essa é uma proposta de [**pesquisa textual**](#a-pesquisa-textual-avan%C3%A7ada) implementada em **python puro** com o uso de dicionário de **sinônimos** e **distância entre termos** pesquisados. <br>
- É uma pesquisa que tenta ir além do que pesquisas comuns fazem, pois não tem o objetivo de trazer grandes volumes de resultados, mas **resultados precisos**. <br>
- Implementada em **python** para uso em pesquisa textual avançada com foco no **Português**, permitindo busca em campos textuais e critérios de proximidade textual.<br>
- O objetivo é refinar pesquisas textuais com frameworks comuns de mercado (MemSQL/SingleStore, ElasticSearch) em volume muito grande de dados, ou pode ser usada para pesquisa completa em textos carregados de arquivos ou em memória. Pode-se também realizar uma análise em tempo real avaliando se determinados critérios são atendidos dentro do texto (regras de texto para mudança de fluxo de trabalho).<br>
- Essa ideia não é nova, conheci ao longo dos últimos 20 anos vários sistemas que faziam algo parecido. Não há pretensão em competir com qualquer um desses produtos, mas ter algo simples e operacional para quem tiver interesse em personalizar uma busca textual da forma que precisar.<br>
- Uma aplicação muito útil dos critérios de pesquisa, alé de encontrar textos, é identificar **rótulos** que são aplicáveis a um texto ao testar um conjunto de regras pré-definidas com seus rótulos correspondentes, simulando um **classificador multilabel** só que no lugar do modelo, tem-se um conjunto de regras textuais. Daí pode-se identificar fluxos automáticos para sistemas, definir alertas, etc.
- O uso do componente é exemplificado no [serviço de regras](./servico_regras), clique para baixar e testar.

## Estão disponíveis nesse repositório:

- Classe python [**PesquisaBR**](./componente) que recebe um documento e um critério de pesquisa e retorna o resultado da avaliação.<br>
- Classe python [**RegrasPesquisaBR**](./componente) que recebe um conjunto de regras e seus rótulos e aplica as regras em um documento, identificando que rótulos são aplicáveis a ele. Simula um modelo multilabel mas com regras no lugar de um modelo treinado.<br>
- [**Serviço avaliador de regras**](./servico_regras): Um exemplo simples de serviço que simula um classificador multilabel que funciona por regras no lugar de um modelo treinado.<br>
- [**Testes da classe**](./componente) código que permitem validar todos os critérios e funcionalidades implementadas<br>
- <b>Conversor de pesquisas</b> método que converte critérios avançados para critérios simples `AND` `OR` `NOT` aceitos pelo MemSQL<br>
- Classe experimental [**PesquisaBRMemSQL**](./testes_memsql/PesquisaMemSQL.md) : classe que permite combinar a análise de pesquisa da classe PesquisaBR com o poder de pesquisa textual nativo do [MemSQL](https://www.memsql.com/). Agora o MemSQL chama-se [SingleStore](https://www.singlestore.com/). Veja também a classe [**PesquisaElasticFacil**](https://github.com/luizanisio/PesquisaElasticFacil) que converte os critérios avançados de proximidade de termos em pesquisa nativa do ElasticSearch.<br>

- Manual com os [**operadores de pesquisa**](#conectores-ou-operadores-de-pesquisa)

## Uso simples da classe:

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

## Uso simples da classe de regras:
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

## Extraindo dados
```py
dados = RegrasPesquisaBR.aplicar_criterios(texto = "esse teste é simples 123,45 123.123 simples",
                                           detalhar =1, extrair = 1, grifar = 1, 
                                           criterios = "r:(esse)|(teste)|(simples)")
print(dados)
```
Console
```bat
{ "criterios":"(esse)|(teste)|(simples)",
  "criterios_analise":"r:(esse)|(teste)|(simples)",
  "extracao":[{"fim":4,"inicio":0,"texto":"esse"},{"fim":10,"inicio":5,"texto":"teste"},
              {"fim":20,"inicio":13,"texto":"simples"},{"fim":43,"inicio":36,"texto":"simples"}],   
  "retorno": True,
  "texto": "esse teste e simples 123,45 123.123 simples",
  "texto_grifado": "<mark>esse</mark> <mark>teste</mark> e <mark>simples</mark> 123,45 123.123 <mark>simples</mark>"
}
```

### Testes básicos da classe
Estão disponíveis diversos textos e pesquisas que são testados para garantir o funcionamento da classe durante o desenvolvimento.
```bat
python pesquisabr_testes.py
```

## Sobre a pesquisa textual avançada

Implementei aqui um conjunto de operadores de pesquisa por proximidade dos termos e outros operadores para refinamento de pesquisa. Esses tipos de operadores tornam-se importantes para refinar pesquisas em grande volume de dados, onde não é importante trazer muito resultado, mas um resultado o mais próximo possível do que é procurado. Ferramentas comuns de busca como <b>ElasticSearch</b> e o próprio <b>MemSQL</b> não trazem nativamente esses tipos de operadores. O ElasticSearch tem o operador `slop` que trabalha com proximidade de termos, a classe [**PesquisaElasticFacil**](https://github.com/luizanisio/PesquisaElasticFacil) permite converter parte dos critérios de pesquisa em pesquisas nativas do elastic.
<p> Esse tipo de pesquisa permite o uso de dicionário de sinônimos em qualquer língua, inclusive o uso de recursos fonéticos. O texto de entrada é pré-processado para evitar não encontrar termos com grafia incorreta de acentos ou termos no singular/plural, bem como números com pontuação ou sem. Por padrão o texto é pesquisado no singular, removendo pronomes oblíquos, mas é possível localizar o termo real usando aspas (exceto acentos que sempre são desconsiderados).
<p> A pesquisa também permite localizar termos pelo dicionário de sinônimos. Ao pesquisar a palavra "genitor", o sistema pesquisa também "pai". A tabela de sinônimos é flexível e facilmente atualizável, permitindo incluir termos em outras línguas se desejado. O uso de sinônimos pode ser ativado ou desativado a cada pesquisa. Ao pesquisar termos entre aspas, o sinônimo é desativado para o termo ou conjunto de termos entre aspas enquanto os outros termos podem ser pesquisados com o uso dos sinônimos.

<p> O pré-processamento envolve:
<ul>
  <li> retirada de <b>acentos</b> </li>
  <li> redução a um <b>pseudosingular</b> ou <b>singular estimado</b>: não é um português perfeito, mas uma singularização para a máquina localizar termos com maior flexibilidade</li>
</ul>

### Conectores ou operadores de pesquisa

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

### Curingas

<ul>
  <li> <b>$</b>: permite o uso de partes do termo no critério de pesquisa. Por exemplo: cas$ vai encontrar casa, casinha, casamento...</li>  
  <li> <b>?</b>: permite a existência ou não de um caracter no lugar do símbolo "?". Por exemplo: cas? vai encontrar cas, casa, caso, case... Pode estar no meio do termo tamém: ca?a vai encontrar caa, casa, cata, cala ... </li>  
</ul>

### Operador especial remover(....)

Esse operador foi criado para remover trechos do texto antes da análise da regra, para o caso de existirem trechos conhecidos que podem resultar em faso positivo para a regra, como cabeçalhos, citações, dentre outros. Pode-se usar quantos `remover(...)` forem necessários dentro do critério de pesquisa.<br>

Como usar o operador `remover(texto)`:
- `$` ou * - de 0 a 100 caracteres quaisquer
- `?` - um caractere de letra ou número opcional
- `&` - um caractere de letra ou número obrigatório
- `#` - um a 10 caracteres que não sejam letra nem número (pontuação, início ou final de texto, espaço, etc)
- `*#` - caracteres até um símbolo (pontuação, início ou final de texto, espaço, etc)
- `*##` - caracteres até uma quebra de linha
- `%` - aspas, parênteses, chaves ou colchetes (citações/explicações em geral)
- `"` - aspas normal

<b>Exemplos de uso do remover:</b>
- <b>remover(aspas)</b>: remove todo o conteúdo do texto entre aspas ou parênteses, com o objetivo de remoção de citações<br>
- <b>remover(termo1 termo2 termo3)</b>: remove o trecho do texto `termo1 termo2 termo3` conforme está escrito dentro dos parênteses do remover(...)<br>
- <b>remover(termo&)</b>: remove qualquer trecho que contenha termo seguido de um número ou letra obrigatória<br>
- <b>remover(termo?)</b>: remove qualquer trecho que contenha termo podendo ou não estar seguido de um número ou letra<br>
- <b>remover(contab*#)</b>: remove todo o texto iniciado por `contab` até encontrar o final da palavra<br>
- <b>remover(conforme exemplos*##)</b>: remove todo o texto iniciado por `conforme exemplos` até encontrar uma quebra de linha<br>

<b>Exemplos de uso dentro dos critérios de pesquisa:</b>
- `casa adj2 papel remover(termo1) remover(teste)'
- Ao ser aplicado o critério no texto `o seriado casa termo1 de teste papel`, a avaliação será verdadeira já que os termos `termo1` e `teste` serão removidos antes da análise.

### Operador especial recortar(....)

Esse operador foi criado para recortar o texto (manter o texto) entre dois termos ou conjuntos de termos. Pode-se usar quantos `recortar(...)` forem necessários dentro do critério de pesquisa. Os trechos recortados serão concatenados com `\n`<br>

Como usar o operador `recortar(texto)`:
- `$` - início/fim de palavra ou texto
- `#` - quebra de linha ou início/fim de texto

<b>Exemplos de uso do recortar:</b>
- <b>recortar(#resumo#;#metodologia#)</b>: mantém apenas o texto entre `\nresumo\n` e `\nmetodologia\n`<br>
- <b>recortar(#formulario$;)</b>: mantém apenas o texto após `\nformulario` até o final do texto`<br>
- <b>recortar(;#resumo#)</b>: mantém apenas o texto do início até o texto `\nresumo\n`<br>

<b>Exemplos de uso dentro dos critérios de pesquisa:</b>
- `seriado casa adj2 papel recortar($inicio$;$fim$)'
- Ao ser aplicado o critério no texto `o seriado inicio casa de papel fim qualquer coisa`, a avaliação será falsa já que o texto analisado será `inicio casa de papel fim`.

### Exemplo de configuração de sinônimos

* ao encontrar um termo no texto analisado, os sinônimos são mapeados como se fossem esse termo
** sinônimos compostos são analisados apenas para termos entre aspas nos critérios de pesquisa
<ul>
  <li> <b>Sinônimos</b>: {'alegre': ['feliz','sorridente'], 'feliz':['alegre','sorridente'], 'sorridente':['alegre','feliz'], 'casa':['apartamento'] } </li>
  <li> <b>Sinônimos compostos</b>: {'casa_de_papel':['la casa de papel','a casa de papel'], "inss" : ['instituto nacional de seguridade social'], 'instituto_nacional_de_seguridade_social':['inss']}</li>
</ul>

Com esse mapeamento, se o critério de pesquisa estiver escrito `alegre` é o mesmo que pesquisar (alegre ou feliz ou sorridente). Se estiver escrito "alegre" entre aspas, os sinônimos não serão pesquisados.
Os sinônimos compostos possuem um comportamento peculiar, permitem o mapeamento de expressões, siglas, etc. Se o critério de pesquisa estiver escrito `"inss"` é o mesmo que pesquisar (inss ou "instituto nacional de seguridade social"). Mas se no critério de pesquisa estiver escrito `inss` sem aspas, somente será pesquisada a palavra `inss` ou sinônimos simples dela .

#### Exemplo de texto e texto com campos

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

## Usando a classe Python

Exemplos disponíveis no arquivo <b>testes_exemplos.py</b> e <b>testes_exemplos_sem_db.py</b>
Para uso da classe [PesquisaBRMemSQL](./testes_memsql) (experimental) é necessário ter instalado o <b>MemSQL</b> (pode ser o container de exemplo). E criar as tabelas e funções do database <b>pesquisabr</b>. Scripts disponívels: <b>db_funcoes.sql</b> e <b>db_tabelas.sql</b>

