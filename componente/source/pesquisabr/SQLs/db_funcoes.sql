DELIMITER //  
# recebe um termo ou um texto, singulariza e remove pronomes oblíquos
CREATE OR REPLACE FUNCTION pesquisabr.f_pre_processar_texto(texto longtext, usar_quebra_br boolean default false) RETURNS longtext AS
  DECLARE 
	  _txt longtext;
  BEGIN
    /* quebra de linha*/
    _txt = REGEXP_REPLACE(lower(texto),"(<\\s*\\/?\\s*[bB][rR]\\s*\\/?\\s*>)",'\n','g');

	/*acentos - usar [áâ...] não funcionou corretamente*/
	_txt = REGEXP_REPLACE(_txt,'á|â|ä|à|ã', 'a', 'g');     
	_txt = REGEXP_REPLACE(_txt,'é|ê|ë|è', 'e', 'g');
	_txt = REGEXP_REPLACE(_txt,'í|ì|ï|î', 'i', 'g');
	_txt = REGEXP_REPLACE(_txt,'ó|ò|ô|õ|ö', 'o', 'g');
	_txt = REGEXP_REPLACE(_txt,'ñ', 'n', 'g');
	_txt = REGEXP_REPLACE(_txt,'ú|ù|û|ü', 'u', 'g');
	_txt = REGEXP_REPLACE(_txt,'ç', 'c', 'g');
    _txt = REGEXP_REPLACE(_txt,'§',' parágrafo ','g');
    _txt = REGEXP_REPLACE(_txt,'{|\\[','(','g');
    _txt = REGEXP_REPLACE(_txt,'}|\\]',')','g');
    /* aspas */
    _txt = REGEXP_REPLACE(_txt,"'|´|`|“|”",'"','g');

    /* separa números de outras palavras*/
    _txt=REGEXP_REPLACE(_txt,'([a-z])([0-9])|([0-9])([a-z])','\\1 \\2','g');
    /* números*/
	_txt=REGEXP_REPLACE(_txt,'([0-9])([\\.,]+)([0-9])','\\1\\3','g');
	_txt=REGEXP_REPLACE(_txt,'([0-9])([\\.,]+)(\\.,)','\\1\\3','g');

    /* ignora símbolos que sobrarem*/
	_txt=REGEXP_REPLACE(_txt,'([^a-z0-9\n])+',' ','g');

    /* limpa espaços*/
    _txt=REGEXP_REPLACE(_txt,' +',' ','g');

	/* plurais */
	_txt=REGEXP_REPLACE(_txt,'(^| |"|\n)(lei|pai)(s)( |$|"|\n)','\\1\\2\\4','g');
	_txt=REGEXP_REPLACE(_txt,'(oes|aes)( |$|"|\n)','ao\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(ais)( |$|"|\n)','al\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(eis)( |$|"|\n)','el\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(ois)( |$|"|\n)','ol\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(les)( |$|"|\n)','l\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(res)( |$|"|\n)','r\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(zes)( |$|"|\n)','z\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(is)( |$|"|\n)','il\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(ns)( |$|"|\n)','m\\2','g');
	_txt=REGEXP_REPLACE(_txt,'(a|e|i|o|u)(s)($| |"|\n)','\\1\\3','g');		

    if usar_quebra_br THEN
       _txt = REGEXP_REPLACE(_txt,'(\\n)|(\\r)','<br>','ig');
    end if;
    /* fim */
   	return trim(_txt);
  END //
DELIMITER ;	