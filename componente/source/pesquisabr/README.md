# Pesquisa textual em documentos
- Essa é uma proposta de <b>pesquisa textual</b> implementada com recursos em **python puro** com o uso de dicionário de **sinônimos** e **distância entre termos** pesquisados. <br>
- Uma aplicação muito útil dos critérios de pesquisa, alé de encontrar textos, é identificar **rótulos** que são aplicáveis a um texto ao testar um conjunto de regras pré-definidas com seus rótulos correspondentes, simulando um **classificador multilabel** só que no lugar do modelo, tem-se um conjunto de regras textuais. Daí pode-se identificar fluxos automáticos para sistemas, definir alertas, etc.

Mais informações: https://github.com/luizanisio/PesquisaTextualBR
<br>
-PS: pesquisabr_memsql.py, util_memsql.py e util.py são necessário apenas quando o componente é utilizado com o banco de dados memsql - em fase experimental ainda
- https://github.com/luizanisio/PesquisaElasticFacil contém uma proposta de conversão de critérios de pesquisa para consulta nativa do ElasticSearch