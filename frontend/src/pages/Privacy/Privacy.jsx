import { useEffect, useState } from "react";
import { getPrivacidade } from "../../services/api";

function Privacy() {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    getPrivacidade().then(setDados).catch((error) => setErro(error.message));
  }, []);

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Privacidade e LGPD</h1>
          <p>Diretrizes de tratamento de dados previstas para o projeto acadêmico</p>
        </div>
      </header>

      {erro && <div className="error-box">{erro}</div>}

      <article className="panel privacy-panel">
        <h2>Uso de dados no EDU-Infra Analytics</h2>
        <p>
          O sistema foi projetado para trabalhar principalmente com dados técnicos de laboratórios e computadores.
          Para controle de acesso, a versão atual utiliza apenas informações básicas do usuário do sistema.
        </p>

        <div className="privacy-cards">
          <div><strong>Finalidade</strong><span>{dados?.finalidade || "Diagnóstico da infraestrutura tecnológica escolar."}</span></div>
          <div><strong>Dados pessoais previstos</strong><span>{dados?.dados_pessoais_previstos?.join(", ") || "nome, e-mail e perfil de acesso"}</span></div>
          <div><strong>Dados sensíveis</strong><span>{dados?.dados_sensiveis_previstos ? "Previstos" : "Não previstos nesta versão"}</span></div>
        </div>

        <h2>Princípios aplicados</h2>
        <p>Minimização de dados, controle de acesso por perfil, senhas armazenadas com hash, autenticação por token e registro de ações relevantes em auditoria.</p>

        <div className="business-rule-note">
          <strong>Importante:</strong> {dados?.observacao || "Em implantação real, a instituição deverá definir base legal, retenção e canal de atendimento aos titulares."}
        </div>
      </article>
    </>
  );
}

export default Privacy;
