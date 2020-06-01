create database pesquisabr;
create user usr_pesquisabr IDENTIFIED BY 'pesquisabr2020';
grant all on pesquisabr.* to usr_pesquisabr;

drop table pesquisabr.tipo_documento_cfg; 
CREATE TABLE pesquisabr.tipo_documento_cfg (
  tipo_documento varchar(100) NOT NULL COMMENT 'nome do tipo documento',
  dthr timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'data de inclusão na tabela',
  tabela varchar(100) NOT NULL COMMENT 'nome da tabela criada no memsql para pesquisa textual com database ex: minhabase.textos ',
  campo_texto varchar(100) NOT NULL COMMENT 'nome do campo que contém o texto original',
  campo_score varchar(100) NOT NULL COMMENT 'nome do campo score na tabela - opcional - o score é somado ao score da pesquisa ',
  campo_id varchar(100) NULL COMMENT 'nome do campo id da tabela - do tipo varchar - campo_id ou campo_seq devem estar preenchidos',
  campo_seq varchar(100) NULL COMMENT 'nome do campo seq da tabela - do tipo int - campo_id ou campo_seq devem estar preenchidos',
  campo_data varchar(100) NOT NULL COMMENT 'nome do campo que contém a data de controle de alteração do texto',
  ind_substituir_texto bool not null default False COMMENT 'True indica que ao gerar o mapa de pesquisa, o texto é atualizado para o texto pré processado',
  PRIMARY KEY (tipo_documento),
  KEY (tipo_documento),
  SHARD KEY (tipo_documento)
  );


drop table pesquisabr.sessao_pesquisa;
CREATE TABLE pesquisabr.sessao_pesquisa (
  sessao varchar(100) NOT NULL COMMENT 'nome da sessão de pesquisa',
  tipo_documento varchar(100) not null COMMENT 'tipo do documento',
  dthr timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'data de inclusão na tabela',
  ind_status char(1) DEFAULT 'N' COMMENT 'status do filtro N novo, I iniciado, F finalizado, M executando Match, P pré-filtrado',
  dthr_status timestamp default null COMMENT 'data e hora do último status - serve para medir performance e fazer um call back',
  qtd_pesquisa_rapida int default 0 not null COMMENT 'quantidade de documentos iniciais na sessão ou incluídos pela pré pesquisa AON',
  qtd_doc_removidos int default 0 not null COMMENT 'quantidade de documentos removidos pelos filtros - serve para medir performance e fazer um call back',
  qtd_doc_aceitos int default 0 not null COMMENT 'quantidade de documentos que atendem à pesquisa - serve para medir performance e fazer um call back',
  PRIMARY KEY (sessao),
  KEY (sessao, dthr),
  SHARD KEY (sessao)
  );

drop table pesquisabr.sessao_pesquisa_doc;
CREATE TABLE pesquisabr.sessao_pesquisa_doc (
  sessao varchar(100) NOT NULL COMMENT 'nome da sessão de pesquisa' ,
  id_documento varchar(100) not null COMMENT 'id do documento - id ou seq devem ser preenchidos com a chave original do documento',
  seq_documento int not null COMMENT 'seq do documento - id ou seq devem ser preenchidos com a chave original do documento',
  score float DEFAULT 0 COMMENT 'score da pesquisa + score do documento',
  dthr timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'data de inclusão na tabela' ,
  ind_status char(1) DEFAULT 'N' COMMENT 'status do filtro N novo, I iniciado, F finalizado, M executando Match, P pré-filtrado',
  dthr_status timestamp default null COMMENT 'data e hora do último status - serve para medir performance e fazer um call back',
  KEY (sessao),
  KEY (sessao, dthr),
  SHARD KEY (sessao)
  );

drop table pesquisabr.mapa_pesquisa;
CREATE TABLE pesquisabr.mapa_pesquisa (
    tipo_documento varchar(100) NULL COMMENT 'nome do tipo documento',
    id_documento varchar(100) NULL COMMENT 'id do documento',
    seq_documento int NOT NULL COMMENT 'seq do documento',
    mapa json COMMENT 'mapa do documento',
    tamanho_mapa int comment 'tamanho do mapa de pesquisa',
    tamanho_texto int comment 'tamanho do texto original',
    dthr timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'data de inclusão na tabela' ,
    dthr_utilizacao timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'data da última utilizacao do mapa' ,
    KEY (id_documento, tipo_documento, seq_documento) USING CLUSTERED COLUMNSTORE
  );

drop table pesquisabr.cache_pesquisa;
CREATE TABLE pesquisabr.cache_pesquisa (
    tipo_documento varchar(100) NULL COMMENT 'nome do tipo documento',
    id_documento varchar(100) NULL COMMENT 'id do documento',
    seq_documento int NOT NULL COMMENT 'seq do documento',
    ind_status char(1) COMMENT 'status da comparação do critério com o documento',
    hash_criterios char(40) not null COMMENT 'hash do critério de pesquisa',
    dthr timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'data de inclusão na tabela' ,
    dthr_utilizacao timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'data da última utilização' ,
    KEY (id_documento, tipo_documento, seq_documento, hash_criterios) USING CLUSTERED COLUMNSTORE
  );

######### tabela de exemplo para armazenar documentos texto puro ou mapas de documentos 
drop table pesquisabr.documentos_diversos;
CREATE TABLE pesquisabr.documentos_diversos (
    seq bigint(11) NOT NULL AUTO_INCREMENT,
    dominio_documento varchar(100) NULL COMMENT 'dominio do documento - agrupador',
    id_documento varchar(100) NULL COMMENT 'id do documento',
    seq_documento int NOT NULL COMMENT 'seq do documento',
    texto longtext COMMENT 'conteúdo pré-processado do documento',
    ind_json_campos bool default false COMMENT ' True indica que o conteúdo do texto é um json com campos separados',
    tamanho_texto int comment 'tamanho do texto original',
    score float not null default 0 comment 'score padrão do documento a ser somado com o score da pesquisa',
    dthr timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'data de inclusão na tabela' ,
    KEY (seq) USING CLUSTERED COLUMNSTORE,
    FULLTEXT KEY (texto)
  );


select * from pesquisabr.sessao_pesquisa;  
select * from pesquisabr.sessao_pesquisa_doc;  