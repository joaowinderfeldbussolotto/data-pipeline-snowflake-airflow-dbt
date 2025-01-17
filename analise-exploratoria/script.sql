select cidade, count(1) from vendedores v
join concessionarias c on c.id_concessionarias = v.id_concessionarias 
join cidades cid on cid.id_cidades = c.id_cidades 
group by cidade
order by 2 desc

--Descrição: Liste todos os veículos com tipo 'SUV Compacta' e valor inferior a 30.000,00.

SELECT nome, tipo, valor
FROM veiculos
WHERE tipo = 'SUV Compacta' AND valor < 30000.00;

--Descrição: Exiba o nome dos clientes e o nome das concessionárias onde realizaram suas compras.

select c.cliente, string_agg(con.concessionaria, ', ') as concessionarias
from clientes c
join concessionarias con on con.id_concessionarias = c.id_concessionarias 
group by c.cliente
order by 1 

--Descrição: Conte quantos vendedores existem em cada concessionária.

select con.concessionaria, count(*) as quantidade_vendedores
from concessionarias con
join vendedores v on v.id_concessionarias = con.id_concessionarias 
group by con.concessionaria 
order by 2 desc

--Descrição: Encontre os veículos mais caros vendidos em cada tipo de veículo.

SELECT tipo, MAX(valor) AS valor_maximo
FROM veiculos
GROUP BY tipo;

--Descrição: Liste o nome do cliente, o veículo comprado e o valor pago, para todas as vendas.

select cli.cliente, v.nome, ven.valor_pago
from clientes cli
join vendas ven on ven.id_clientes = cli.id_clientes 
join veiculos v on v.id_veiculos = ven.id_veiculos 


--Descrição: Identifique as concessionárias que venderam mais de 5 veículos.

select concessionaria, count(id_vendas)
from concessionarias c 
join vendas v on v.id_concessionarias = c.id_concessionarias
group by concessionaria 
HAVING(count(id_vendas)) > 5
order by 2 desc


--Descrição: Liste os três veículos mais caros disponíveis.


select * from veiculos v 
order by v.valor desc
limit 3


--Descrição: Selecione todos os veículos adicionados no último mês.
SELECT nome, data_inclusao
FROM veiculos
WHERE data_inclusao > CURRENT_TIMESTAMP - INTERVAL '1 month';


--Descrição: Liste todas as cidades e qualquer concessionária nelas, se houver.

select ci.cidade, string_agg(con.concessionaria, ', ') 
from cidades ci
left join concessionarias con on con.id_cidades = ci.id_cidades 
group by ci.cidade 


--Descrição: Encontre clientes que compraram veículos 'SUV Premium Híbrida' ou veículos com valor acima de 60.000,00.


SELECT cl.cliente, v.nome AS veiculo, v.valor
FROM vendas vd
JOIN veiculos v ON vd.id_veiculos = v.id_veiculos
JOIN clientes cl ON vd.id_clientes = cl.id_clientes
WHERE v.tipo = 'SUV Premium Híbrida' OR v.valor > 60000.00;