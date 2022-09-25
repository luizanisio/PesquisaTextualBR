## palavras repetidas
select * from pesquisabr.palavras p where palavra in (
select palavra from pesquisabr.palavras p 
group by palavra having count(1)>1
) order by palavra, origem  

## lista de singulares
select group_concat('"',palavra,'"' order by palavra) from pesquisabr.palavras p where e_singular order by palavra 

## existe em outra origem
select * from pesquisabr.palavras p where p.origem ='LISTA'
and exists(select 1 from pesquisabr.palavras p2 where p2.palavra=p.palavra and p2.origem<>'LISTA')

