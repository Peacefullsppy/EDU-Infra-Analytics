function Privacy({ onBack }) {
  return (
    <div className="legal-page">
      <div className="legal-card">
        <button className="text-button" type="button" onClick={onBack}>← Voltar</button>
        <h1>Política de Privacidade e Termo de Uso</h1>
        <p className="legal-version">EDU-Infra Analytics — versão 1.0</p>

        <section>
          <h2>1. Finalidade</h2>
          <p>
            O EDU-Infra Analytics é um projeto acadêmico destinado ao acompanhamento da infraestrutura
            tecnológica de ambientes educacionais. Os dados de usuários são tratados somente para
            autenticação, controle de acesso, segurança e auditoria das ações realizadas no sistema.
          </p>
        </section>

        <section>
          <h2>2. Dados pessoais tratados</h2>
          <p>
            Nesta versão são previstos apenas nome, e-mail e perfil de acesso dos usuários administrativos,
            técnicos ou gestores. O MVP não prevê coleta de dados pessoais sensíveis de alunos ou professores.
          </p>
        </section>

        <section>
          <h2>3. Logs de auditoria</h2>
          <p>
            O sistema registra ações relevantes, como login, consultas e cadastros, para permitir rastreabilidade
            e validação acadêmica. Os registros evitam armazenar senhas e não incluem o conteúdo das credenciais.
          </p>
        </section>

        <section>
          <h2>4. Segurança</h2>
          <p>
            As senhas são armazenadas somente em formato de hash. A autenticação utiliza token JWT e as áreas
            protegidas exigem sessão válida. Credenciais e chaves de conexão devem permanecer em arquivo
            <code>.env</code>, fora do repositório Git.
          </p>
        </section>

        <section>
          <h2>5. Princípios da LGPD</h2>
          <p>
            O projeto adota como referência os princípios de finalidade, necessidade, transparência, segurança
            e prevenção, buscando limitar o tratamento ao mínimo necessário para o funcionamento do sistema.
          </p>
        </section>

        <section>
          <h2>6. Implantação institucional</h2>
          <p>
            Em uma implantação real, a instituição responsável deverá definir formalmente o controlador dos dados,
            as bases legais aplicáveis, os prazos de retenção, o canal para exercício de direitos dos titulares e
            os procedimentos internos de resposta a incidentes.
          </p>
        </section>
      </div>
    </div>
  );
}

export default Privacy;
