import os
import json
ARQ_CONFIG = './config.json'
CONFIG = {}
TEMPO_CACHE_SEGUNDOS = 0

###################################################################
# configurações do serviço
def carregar_config():
    global CONFIG, TEMPO_CACHE_SEGUNDOS
    _config = {}
    if os.path.isfile(ARQ_CONFIG):
        with open(ARQ_CONFIG,mode='r') as f:
            _config = f.read().replace('\n',' ').strip()
            if _config and _config[0]=='{' and _config[-1]=='}':
                _config = json.loads(_config)
    # correções do tempo de refresh das regras - em segundos
    # mínimo 10s
    _config['tempo_regras'] = _config.get('tempo_regras', 600)
    if (type(_config['tempo_regras']) != int) or (_config['tempo_regras']<10):
        _config['tempo_regras'] = 10
    # atualização da configuração
    CONFIG = _config

    TEMPO_CACHE_SEGUNDOS = CONFIG.get('tempo_regras',0)
    TEMPO_CACHE_SEGUNDOS = 10* 60 if TEMPO_CACHE_SEGUNDOS < 1 else TEMPO_CACHE_SEGUNDOS

carregar_config()

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

