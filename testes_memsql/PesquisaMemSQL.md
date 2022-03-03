# Pesquisa textual em documentos Python + MemSQL
Essa é uma proposta de pesquisa textual combinando a classe Python PesquisaBR com os recursos nativos do MemSQL, formando a classe python PesquisaBRMemSQL, permitindo busca em campos textuais e critérios de proximidade textual. O objetivo é refinar pesquisas textuais básicas do MemSQL com operadores de proximidade.

### Estão disponíveis nesse repositório:
<ul>
  <li>Classe python <b>PesquisaBRMemSQL()</b>: classe responsável por fazer um link entre a classe que constrói e avalia os critérios avançados, e os critérios básicos de pesquisa do MemSQL</br>
  <li>Classe python <b>PesquisaBR</b>(https://github.com/luizanisio/PesquisaTextualBR) que recebe um documento e um critério de pesquisa e retorna a avaliação.</li>
  <li>Testes da classe que permitem validar todos os critérios e funcionalidades implementadas</li>
  <li>Conversor de pesquisas com critérios avançados para critérios simples AND OR NOT aceitos pelo MemSQL</li>
  <li>Scripts de criaçãod e tabelas e funções utilizadas pela classe PesquisaBrMemSQL()</li>
</ul>

### Objetos de banco de dados:
<ul>
  <li>Tabela <b>tipo_documento_cfg</b>: permite configurar tipos/domínios de documentos de tabelas que estão em outras bases do MemSQL para que o componente saiba de onde buscar os textos para fazer as análises.</li>
  <li>Tabela <b>sessao_pesquisa</b>: tabela que consolida uma pesquisa realizada. É criado um registro com o nome da sessão de pesquisa (a aplicação pode criar um nome qualquer único) para referenciar a pesquisa realizada. Algumas queries são construídas e executadas com os critérios de pesquisa do MemSQL para fazer uma <i>pré pesquisa</i> que depois é refinada pela classe PesquisaBR com seus critérios de proximidade.</li>
  <li>Tabela <b>sessao_pesquisa_doc</b>: tabela que consolida a lista de ids ou sequenciais de documentos que correspondem aos critérios de pesquisa. Pode-se incluir uma lista de ids e solicitar que a pesquisa seja refinada pelos critérios ou fazer uma pesquisa na base toda.</li>
  <li>Tabela <b>mapa_pesquisa</b>: tabela que guarda um cache do mapa do documento a ser analisado. Esse mapa é criado quando um documento vai ser analisado pela classe PesquisaBR, para acelerar novas pesquisas, o mapa é recuperado já pronto. Existe um controle de validade do mapa de acordo com a data de atualização do documento original.</li>
  <li>Tabela <b>cache_pesquisa</b>: tabela responsável por guardar um cache de comparação entre um critério de pesquisa e um documento. Caso um mesmo critério seja rodado repetidas vezes, o cache com o resultado é carregado e a análise não precisa ser realizada novamente. Existe um controle de validade do cache de análise do documento de acordo com a data de atualização do documento original.</li>
  <li>Função <b>f_pre_processar_texto(texto)</b>: Essa função é responsável pelo pré-processamento de textos diretamente no banco com o mesmo pré-processamento da classe PesquisaBR. A ideia é permitir uma ingestão de dados diretamente no banco de dados sem a necessidade de chamada de uma api. Vários exemplos serão colocados aqui para demonstrar o uso da função e/ou da classe diretamente.</li>
</ul>

### Recursos da classe <b>PesquisaBRMemSQL()</b>:
<ul>
   <li>Conexão com o banco MemSQL: realizada por arquivo de configuração, é necessário que o usuário tenha acesso de escrita às tabelas do schema <b>pesquisabr</b>, e apenas leitura às tabelas com os textos originais.</li>
   <li>Limpeza automática do cache: ao instanciar a classe, ela conecta com o MemSQL e realiza limpeza dos cacher de mapas e comparações não utilizados por mais de 180 dias. Esse parêmtro pode ser configurado.
   <li>Método pesquisar: recebe como parâmteros o nome da sessão de pesquisa que será construída, o tipo de documento/domínio que será analisado e os critérios de pesquisa aceitos pela classe PesquisaBR. Pode-se realizar uma nova pesquisa, unir uma pesquisa existente com mais resultados de outros critérios de pesquisa ou filtrar documentos já incluídos na sessão de pesquisa.</li>
   <li>Método pesquisar(sessao, tipo_documento, criterios, tipo: nova/união/filtro): recebe como parâmteros o nome da sessão de pesquisa que será construída, o tipo de documento/domínio que será analisado e os critérios de pesquisa aceitos pela classe PesquisaBR. Pode-se realizar uma nova pesquisa, unir uma pesquisa existente com mais resultados de outros critérios de pesquisa ou filtrar documentos já incluídos na sessão de pesquisa.</li>
   <li>Método retorno(sessao): recebe como parâmteros o nome da sessão de pesquisa e retorna os ids que foram aceitos pelo critério de pesquisa, bem como um resumo de quantos documentos foram incluídos pela pré-pesquisa do MemSQL, quantos foram removidos e quantos foram aceitos após o refinamento da pesquisa.</li>
</ul>

### *** em breve...
<ul>
  <li>Serviço python para responder solicitações de pesquisa combinando as classes PesquisaBR e PesquisaBRMemSQL.</li>
  <li>Scripts de exeplo para ingestão de dados e testes</li>
</ul>
