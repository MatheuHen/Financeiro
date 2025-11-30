BEGIN TRANSACTION;
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM seq WHERE n < 100
)
INSERT INTO api_pessoas (nome, documento, tipo, ativo, created_at, updated_at)
SELECT 'Fornecedor ' || n, printf('%02d.%03d.%03d/%04d-%02d', n%99+1, n*13%999, n*17%999, n*19%9999, n*23%99), 'FORNECEDOR', 1, datetime('now'), datetime('now') FROM seq;

WITH RECURSIVE seq2(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM seq2 WHERE n < 100
)
INSERT INTO api_pessoas (nome, documento, tipo, ativo, created_at, updated_at)
SELECT 'Cliente ' || n, printf('%03d.%03d.%03d-%02d', n*7%999, n*11%999, n*13%999, n*17%99), 'FATURADO', 1, datetime('now'), datetime('now') FROM seq2;

INSERT INTO api_classificacao (descricao, tipo, ativo, created_at, updated_at)
VALUES
 ('INSUMOS AGRÍCOLAS', 'DESPESA', 1, datetime('now'), datetime('now')),
 ('MANUTENÇÃO E OPERAÇÃO', 'DESPESA', 1, datetime('now'), datetime('now')),
 ('RECURSOS HUMANOS', 'DESPESA', 1, datetime('now'), datetime('now')),
 ('SERVIÇOS OPERACIONAIS', 'DESPESA', 1, datetime('now'), datetime('now')),
 ('INFRAESTRUTURA E UTILIDADES', 'DESPESA', 1, datetime('now'), datetime('now')),
 ('ADMINISTRATIVAS', 'DESPESA', 1, datetime('now'), datetime('now')),
 ('SEGUROS E PROTEÇÃO', 'DESPESA', 1, datetime('now'), datetime('now')),
 ('IMPOSTOS E TAXAS', 'DESPESA', 1, datetime('now'), datetime('now')),
 ('VENDAS', 'RECEITA', 1, datetime('now'), datetime('now'));

WITH RECURSIVE seqm(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM seqm WHERE n < 50
)
INSERT INTO api_movimentocontas (
  fornecedor_id, faturado_id, classificacao_id, numero_nf, serie_nf, data_emissao, valor_total, quantidade_parcelas, ativo, created_at, updated_at
) SELECT 
  (SELECT id FROM api_pessoas WHERE tipo='FORNECEDOR' ORDER BY id LIMIT 1 OFFSET (n%100)),
  (SELECT id FROM api_pessoas WHERE tipo='FATURADO' ORDER BY id LIMIT 1 OFFSET (n%100)),
  (SELECT id FROM api_classificacao ORDER BY id LIMIT 1 OFFSET (n%9)),
  printf('%06d', n),
  printf('%03d', n%999),
  date('now','-'||(n%365)||' days'),
  (n*100.0),
  (n%5)+1,
  1,
  datetime('now'),
  datetime('now')
FROM seqm;

WITH RECURSIVE seqp(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM seqp WHERE n < 150
)
INSERT INTO api_parcelascontas (
  movimento_id, numero_parcela, data_vencimento, valor_parcela, ativo, created_at, updated_at
) SELECT 
  (SELECT id FROM api_movimentocontas ORDER BY id LIMIT 1 OFFSET (n%50)),
  (n%5)+1,
  date('now','+'||(n%120)||' days'),
  ((n%5)+1)*50.0,
  1,
  datetime('now'),
  datetime('now')
FROM seqp;
COMMIT;
