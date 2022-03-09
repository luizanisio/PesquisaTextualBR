## Serviço para avaliar textos e retornar os rótulos deles com base em regras pré-definidas
Serviço simples que permite testar um conjunto de regras pré-definidas com seus rótulos correspondentes, simulando um **classificador multilabel** só que no lugar do modelo, tem-se um conjunto de regras textuais. Daí pode-se identificar fluxos automáticos para sistemas, definir alertas, etc.
- O componente pode ser usado baixando a pasta [**componente**](./componente) e instalando o componente, depois baixando o exemplo do serviço na pasta [**app**](./app)<br>

- Esse é um serviço simples de exemplo do uso da classe de avaliação de regras para gerar um classificador multilabel por regras.
- O arquivo *regras.json* contém uma lista de regras de exemplo. As regras podem estar em um banco de dados que o serviço carrega ao subir, ou em um arquivo texto mesmo. Depois basta chamar o serviço passando o texto que ele retorna os rótulos aplicáveis com base nas regras carregadas.
- A responsabilidade do serviço é rotular o texto recebido, comportando-se como um classificador multilabel por regras.
- Opcionalmente pode-se informar ao serviço que regras devem ser testadas, passando uma **tag** ou conjunto de tags ou o nome do grupo da regra ou outros tipos de filtros.
- É possível usar **regex** no lugar dos critérios textuais para regras mais refinadas. Para isso, basta registrar a regra com **r:** no início da regra. Ex.: *r:oficio \\d+*
- No caso de regex, existem expressões prontas para facilitar o uso como CPF, CNPJ e podem ser personalizadas. Para usar uma expressão pronta, basta criar a regra *r:<CPF>|<CNPJ>* por exemplo. O conjunto de expressões prontas está em UtilExtracaoRe().PRONTOS {"CPF" : "...", ...}

- O serviço de exemplo está nesta pasta, basta baixá-lo.

- exemplo da tela de critérios
![tela do serviço de exemplo - critérios](./imgs/tela_srv01.png?raw=true "tela do serviço de exemplo - critérios")
- exemplo da tela de regras
![tela do serviço de exemplo - regras](./imgs/tela_srv02.png?raw=true "tela do serviço de exemplo - regras")

**Exemplos de regras:**
- casa adj2 papel remover(aspas) remover(casa do papel)
- oficio adj5 remetido remover(de oficio)

### Uso simples do serviço de exemplo:
- POST: http://localhost:8000/analisar_criterio
```json
{"texto": "esse é um texto legal", "criterio": " texto PROX10 legal", "detalhar": 1, "grifar":1}
```
Retorno
```json
{    "criterios": "texto PROX10 legal",
    "criterios_analise": " texto PROX10 legal",
    "criterios_aon": "texto AND legal",
    "retorno": true,
    "tempo": 0.001,
    "texto": "esse e um texto legal",
    "texto_analise": "esse é um texto legal",
    "texto_grifado": "esse é um <mark>texto</mark> <mark>legal</mark>"}
```

- POST: http://localhost:8000/analisar_regras
```json
{"texto": "esse  texto tem umas receitas de pão e de bolos legais 123 456 um dois três com o oficio número 5.174", "detalhar": 0 }
```
Retorno
```json
{    "extracoes": [{"fim": 41,"inicio": 22,"texto": "oficio numero 5.174"}],
    "rotulos": ["oficio","Receita de Bolo","Receita de Pao"],
    "tempo": 0.003
}
```

- POST: http://localhost:8000/analisar_regras
- o *detalhar=1* nesse exeplo retorna a regra identificada por cada rótulo e o texto processado
- a chave opcional *tags* pode ser usada para filtrar e avaliar apenas regras que contenham uma das tags configuradas
- a chave opcional *grupo* pode ser usada para filtrar e avaliar apenas regras de um determinado grupo
- qualquer chave criada no arquivo de regras pode ser usada para filtras o grupo de regras que será aplicado
```json
{"texto": "esse ofício 12 texto tem umas receitas de pão e de bolos legais 123 456 um dois são vários testes três com o oficio número 5.174", 
 "detalhar":0, "tags":"oficio"}
```
Retorno
```json
{ "extracoes": [{"fim": 14,"inicio": 5,"texto": "oficio 12"},
                {"fim": 41,"inicio": 22,"texto": "oficio numero 5.174"}],
    "rotulos": ["oficio"],
    "tempo": 0.001
}
```

**Regras desse exemplo (arquivo regras.json):**
- a chave *tags*, *qtd_cabecalho*, *qtd_rodape* são opcionais
- *regra*: é a regra usando os operadores de pesquisa textual, ou um regex. No caso de regex, a regra deve começar com r: regex desejado
- *rotulo*: é o rótulo do grupo que será retornado se a regra retornar true
- *qtd_cabecalho*: a regra é aplicada no início do texto até o caracter da posição informada
- *qtd_rodape*: a regra é aplicada no final do texto, do caracter da posição informada até o fim
- *qtd_cabecalho* e *qtd_rodape*: a regra é aplicada removento o miolo do texto de qtd_cabecalho até qtd_rodape
- *ordem* é opcional, as regras são carregadas ordenadas pelo nome do grupo e depois por esse campo se existir. A ordenação afeta o retorno de rótulos únicos de grupos com o parâmetro `primeiro_do_grupo: True`, fazendo com que as outras regras do grupo sejam ignoradas quando a primeira for verdadeira, retornando apenas um rótulo por grupo.
```json
{"regras": [
    {"grupo" : "receitas_bolo", "rotulo": "Receita de Bolo", "regra": "receita ADJ10 bolo", "tags": "receita bolo", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "receita"},
    {"grupo" : "receitas_bolo", "rotulo": "Receita de Bolo", "regra": "aprenda ADJ5 fazer ADJ10 bolo", "tags": "receita bolo", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "receita"},
    {"grupo" : "receitas_pao", "rotulo": "Receita de Pao", "regra": "receita PROX15 pao", "tags": "receita pao", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "receita"},
    {"grupo" : "grupo_teste", "rotulo": "teste", "regra": "teste", "tags": "teste", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "grupo"},
    {"grupo" : "grupo_regex", "rotulo": "teste regex", "regra": "r:teste|testar?", "tags": "teste", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "grupo"},
    {"grupo" : "grupo_oficio", "rotulo": "oficio", "regra": "r:oficio\\s?(n.{0,10})?\\d+", "tags": "teste oficio", "qtd_cabecalho":20, "qtd_rodape":20, "filtro_tipo" : "grupo"},
    {"grupo" : "grupo_erro", "rotulo": "teste erro regra", "regra": "regra nao (nao" , "filtro_tipo" : "erro"},
    {"grupo" : "grupo_erro", "rotulo": "teste erro regex", "regra": "r: (?)" , "filtro_tipo" : "erro"},
    {"grupo" : "grupo_aspas_termo", "rotulo": "teste aspas termo", "regra": "usando nao testando remover('testando')" , "filtro_tipo" : "grupo"},
    {"grupo" : "grupo_aspas", "rotulo": "teste_aspas", "regra": "teste remover(aspas)" , "filtro_tipo" : "grupo"},
    {"grupo" : "grupo_multi", "rotulo": "multi2", "regra": "R:multi", "tags": "multi", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "multi", "ordem": 1},
    {"grupo" : "grupo_multi", "rotulo": "multi1", "regra": "multi", "tags": "multi", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "multi", "ordem": 0},
    {"grupo" : "grupo_multi", "rotulo": "multi3", "regra": "multi", "tags": "multi", "qtd_cabecalho":0, "qtd_rodape":0, "filtro_tipo" : "multi", "ordem": 3}
 ]
}
```

## Configurando o serviço
- Você pode ter uma base de dados em algum BD com as regras e o serviço carregar as regras dessa base. É mantido um cache de 5min para o serviço não ficar carregando as regras o tempo todo o que inviabilizaria um volume grande de acessos ao serviço.
- Abra o arquivo `app_config.py` 
    - Identifique no final do arquivo as configurações disponibilizadas
    - aponte o objeto `obj_regras_model` para o objeto desejado para carga de regras e conversão de dados de saída
    - crie novos padrões prontos de regex para serem aproveitados nas regras, como o exemplo abaixo para OAB.
```python
###################################################################################
# configurando novos padrões prontos de regex
from pesquisabr import UtilExtracaoRe
novos_prontos = {'OAB' : r'\b([a-z]{2}[\.\-,; ]?\d{2,7}|\d{2,7}[\.\-,; ]?[a-z]{2})\b'}
UtilExtracaoRe.PRONTOS.update(novos_prontos)

###################################################################################
# define o tipo de objeto de regras que será carregado
# pode-se criar um tipo personalizado carregando do banco ou de onde for necessário
from regras_model import RegrasModelArquivo
obj_regras_model = RegrasModelArquivo()
```    

- Abra o arquivo `regras_model.py`
    - verifique a classe `RegrasModelBase` que é usada para carregar as regras e converter os dados de saída do serviço, podendo ser personalizada conforme necessário
```python
class RegrasModelBase():
    # sobrescrever esse método para retornar uma lista de regras 
    # pode carregar do banco, do disco, de outro serviço, etc
    # [{"grupo" : "nome_grupo", "rotulo": "rotulo1", "regra": "critérios da regra", "tags": "receita bolo", "qtd_cabecalho":0, "qtd_rodape":0},]
    # incluir algum filtro com a chave filtro_tipo facilita testes na tela exemplo do serviço
    def get_regras_db(self):
        return []

    # pode-se transforar os dados de saída do serviço com base em alguma
    # regra específica do contexto da aplicação
    # pode-se tratar a chave regras com as regras aplicadas, a chave rótulos, etc
    def conversao_retorno(self, retorno: dict):
        pass 
...
    
class RegrasModelArquivo(RegrasModelBase):
    ARQ_REGRAS = './regras.json'   # arquivo texto no formato [{regra}, {regra}, {regra}]
    def get_regras_db(self):
        regras = []
        if os.path.isfile(self.ARQ_REGRAS):
            with open(self.ARQ_REGRAS,mode='r') as f:
                regras = f.read()
            regras = json.loads(regras.strip()) 
        regras = regras.get('regras',[])
        return RegrasPesquisaBR.ordenar_regras(regras)

    # converte os dados retornados pelo controller 
    def conversao_retorno(self, retorno: dict):
        # exemplo para injetar uma chave com os grupos retornados
        # poderia buscar outros dados no BD, em outro serviço, transformar dados, etc
        if 'regras' in retorno:
           regras = retorno['regras']
           grupos = []
           for r in regras:
               if r.get('grupo') and r.get('grupo') not in grupos:
                  grupos.append(r.get('grupo'))
           retorno['grupos'] = grupos
    
```    
