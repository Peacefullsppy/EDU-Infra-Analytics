# Configuração do Supabase

1. Crie/abra o projeto no Supabase.
2. Clique em **Connect**.
3. Se sua rede for IPv4, escolha **Session pooler**.
4. Copie a connection string completa.
5. Substitua `[YOUR-PASSWORD]` pela senha real do banco, sem manter os colchetes.
6. Coloque a string em `backend/.env` na variável `DATABASE_URL`.
7. Execute `python -m app.seed`.

Formato esperado do Session pooler:

```text
postgresql://postgres.PROJECT_REF:SENHA@HOST_POOLER:5432/postgres
```

Se a senha tiver caracteres reservados de URL, use percent-encoding ou altere a senha para uma combinação segura que não cause ambiguidade na string de conexão.
