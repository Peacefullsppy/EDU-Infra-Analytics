# Segurança e LGPD — escopo do protótipo

Medidas implementadas:

- senhas não são armazenadas em texto puro;
- hash de senha com Argon2;
- autenticação por JWT;
- perfis de acesso;
- auditoria de ações relevantes;
- `.env` ignorado pelo Git;
- minimização dos dados pessoais previstos.

Limites da versão acadêmica:

- ainda não há recuperação de senha;
- ainda não há gestão completa de usuários;
- ainda não há política institucional de retenção configurável;
- HTTPS depende do ambiente de implantação;
- base legal e identificação formal do controlador precisam ser definidas pela instituição em uso real.
