# SQL Practice

## Easy Level

### 1) View all documents

```sql
SELECT id, title, source, created_at
FROM documents
ORDER BY created_at DESC;
```

### 2) View all chunks for one document (filter by title)

```sql
SELECT c.chunk_index, c.content
FROM chunks c
JOIN documents d ON d.id = c.document_id
WHERE d.title = 'RAG Overview'
ORDER BY c.chunk_index;
```

### 3) Simple text search in chunks

```sql
SELECT d.title, c.chunk_index, c.content
FROM chunks c
JOIN documents d ON d.id = c.document_id
WHERE c.content ILIKE '%index%'
ORDER BY d.title, c.chunk_index;
```

### 4) Count chunks total

```sql
SELECT COUNT(*) AS total_chunks
FROM chunks;
```

---

## Intermediate Level

### 5) Join + aggregate: chunk count per document

```sql
SELECT d.title, d.source, COUNT(c.id) AS chunk_count
FROM documents d
LEFT JOIN chunks c ON c.document_id = d.id
GROUP BY d.title, d.source
ORDER BY chunk_count DESC, d.title;
```

### 6) HAVING: only documents with at least 4 chunks

```sql
SELECT d.title, COUNT(*) AS chunk_count
FROM documents d
JOIN chunks c ON c.document_id = d.id
GROUP BY d.title
HAVING COUNT(*) >= 4
ORDER BY chunk_count DESC, d.title;
```

### 7) Aggregate + ORDER BY: longest chunks overall (by character length)

```sql
SELECT d.title, c.chunk_index, LENGTH(c.content) AS content_len
FROM chunks c
JOIN documents d ON d.id = c.document_id
ORDER BY content_len DESC, d.title
LIMIT 10;
```

### 8) DISTINCT sources and document counts per source

```sql
SELECT source, COUNT(*) AS document_count
FROM documents
GROUP BY source
ORDER BY document_count DESC, source;
```

### 9) “Per-document summary”: min/max chunk index and chunk count

```sql
SELECT
  d.title,
  COUNT(c.id) AS chunk_count,
  MIN(c.chunk_index) AS min_chunk_index,
  MAX(c.chunk_index) AS max_chunk_index
FROM documents d
LEFT JOIN chunks c ON c.document_id = d.id
GROUP BY d.title
ORDER BY chunk_count DESC, d.title;
```

### 10) Find missing chunk indexes (gap detection pattern)

This helps teach data quality ideas.

```sql
SELECT d.title, c.chunk_index
FROM documents d
JOIN chunks c ON c.document_id = d.id
WHERE c.chunk_index < 0
   OR c.chunk_index IS NULL
ORDER BY d.title, c.chunk_index;
```

(With your seed data, this should return zero rows.)

---

## Advanced Level

### 11) Subquery: documents above average chunk count

```sql
SELECT title, chunk_count
FROM (
  SELECT d.id, d.title, COUNT(c.id) AS chunk_count
  FROM documents d
  LEFT JOIN chunks c ON c.document_id = d.id
  GROUP BY d.id, d.title
) x
WHERE chunk_count > (
  SELECT AVG(chunk_count)
  FROM (
    SELECT COUNT(*) AS chunk_count
    FROM chunks
    GROUP BY document_id
  ) y
)
ORDER BY chunk_count DESC, title;
```

### 12) Correlated subquery: for each document, show its longest chunk length

```sql
SELECT
  d.title,
  (
    SELECT MAX(LENGTH(c.content))
    FROM chunks c
    WHERE c.document_id = d.id
  ) AS longest_chunk_len
FROM documents d
ORDER BY longest_chunk_len DESC, d.title;
```

### 13) Subquery for filtering: documents that contain a keyword anywhere in chunks

```sql
SELECT d.id, d.title, d.source
FROM documents d
WHERE EXISTS (
  SELECT 1
  FROM chunks c
  WHERE c.document_id = d.id
    AND c.content ILIKE '%transaction%'
)
ORDER BY d.title;
```

### 14) CTE to make query readable: chunk counts + filter + sort

```sql
WITH chunk_counts AS (
  SELECT d.id, d.title, d.source, COUNT(c.id) AS chunk_count
  FROM documents d
  LEFT JOIN chunks c ON c.document_id = d.id
  GROUP BY d.id, d.title, d.source
)
SELECT *
FROM chunk_counts
WHERE chunk_count >= 4
ORDER BY chunk_count DESC, title;
```

### 15) CTE + “top N per group”: top 2 longest chunks per document

```sql
WITH ranked AS (
  SELECT
    d.title,
    c.chunk_index,
    c.content,
    LENGTH(c.content) AS content_len,
    ROW_NUMBER() OVER (
      PARTITION BY c.document_id
      ORDER BY LENGTH(c.content) DESC, c.chunk_index
    ) AS rn
  FROM documents d
  JOIN chunks c ON c.document_id = d.id
)
SELECT title, chunk_index, content_len, content
FROM ranked
WHERE rn <= 2
ORDER BY title, rn;
```

### 16) Window rank: rank documents by chunk count within each source

```sql
WITH counts AS (
  SELECT d.id, d.title, d.source, COUNT(c.id) AS chunk_count
  FROM documents d
  LEFT JOIN chunks c ON c.document_id = d.id
  GROUP BY d.id, d.title, d.source
)
SELECT
  title,
  source,
  chunk_count,
  DENSE_RANK() OVER (
    PARTITION BY source
    ORDER BY chunk_count DESC
  ) AS rank_within_source
FROM counts
ORDER BY source, rank_within_source, title;
```

### 17) Running total: chunks accumulated by document creation time

```sql
WITH counts AS (
  SELECT d.id, d.title, d.created_at, COUNT(c.id) AS chunk_count
  FROM documents d
  LEFT JOIN chunks c ON c.document_id = d.id
  GROUP BY d.id, d.title, d.created_at
)
SELECT
  title,
  created_at,
  chunk_count,
  SUM(chunk_count) OVER (
    ORDER BY created_at
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running_total_chunks
FROM counts
ORDER BY created_at;
```

### 18) Percent of total: each document’s share of all chunks

```sql
WITH counts AS (
  SELECT d.id, d.title, COUNT(c.id) AS chunk_count
  FROM documents d
  LEFT JOIN chunks c ON c.document_id = d.id
  GROUP BY d.id, d.title
),
tot AS (
  SELECT SUM(chunk_count) AS total_chunks
  FROM counts
)
SELECT
  c.title,
  c.chunk_count,
  ROUND(100.0 * c.chunk_count / t.total_chunks, 2) AS pct_of_total
FROM counts c
CROSS JOIN tot t
ORDER BY c.chunk_count DESC, c.title;
```

### 19) Window “previous row”: compare each chunk length to the previous chunk in the same document

```sql
SELECT
  d.title,
  c.chunk_index,
  LENGTH(c.content) AS content_len,
  LAG(LENGTH(c.content)) OVER (
    PARTITION BY c.document_id
    ORDER BY c.chunk_index
  ) AS prev_len,
  LENGTH(c.content) - LAG(LENGTH(c.content)) OVER (
    PARTITION BY c.document_id
    ORDER BY c.chunk_index
  ) AS delta_from_prev
FROM documents d
JOIN chunks c ON c.document_id = d.id
ORDER BY d.title, c.chunk_index;
```

---

## Optional “challenge” problems

* Find documents where chunk indexes are not contiguous (e.g., missing 2)
* Identify duplicate chunk content across different documents
* For each source, show the document with the most chunks (ties included)
* Write a query that returns one row per document with a single concatenated text field of all chunk content in order

