import pytest
from pydantic import ValidationError

from app.schemas import ComputadorCreate, LaboratorioCreate, LoginRequest


@pytest.mark.unit
class TestComputadorCreate:
    def test_deve_aceitar_computador_valido(self):
        # Arrange / Act
        computador = ComputadorCreate(
            hostname="LAB01-PC01",
            ip="192.168.1.101",
            laboratorio_id=1,
            status="online",
            cpu=35,
            ram=48,
            disco=60,
        )

        # Assert
        assert computador.hostname == "LAB01-PC01"
        assert computador.laboratorio_id == 1
        assert computador.status == "online"

    def test_deve_rejeitar_laboratorio_id_zero(self):
        # Arrange / Act
        with pytest.raises(ValidationError) as exc:
            ComputadorCreate(
                hostname="LAB01-PC01",
                ip="192.168.1.101",
                laboratorio_id=0,
            )

        # Assert
        assert "greater than 0" in str(exc.value)
        assert exc.value.errors()[0]["loc"] == ("laboratorio_id",)

    @pytest.mark.parametrize("valor_limite", [0, 100])
    def test_deve_aceitar_metricas_nos_limites_permitidos(self, valor_limite):
        # Arrange / Act
        computador = ComputadorCreate(
            hostname="LAB01-PC02",
            ip="192.168.1.102",
            laboratorio_id=1,
            cpu=valor_limite,
            ram=valor_limite,
            disco=valor_limite,
        )

        # Assert
        assert computador.cpu == valor_limite
        assert computador.ram == valor_limite
        assert computador.disco == valor_limite

    def test_deve_rejeitar_cpu_acima_de_cem(self):
        # Arrange / Act
        with pytest.raises(ValidationError) as exc:
            ComputadorCreate(
                hostname="LAB01-PC03",
                ip="192.168.1.103",
                laboratorio_id=1,
                cpu=101,
            )

        # Assert
        assert "less than or equal to 100" in str(exc.value)
        assert exc.value.errors()[0]["loc"] == ("cpu",)


@pytest.mark.unit
class TestLaboratorioCreate:
    def test_deve_aceitar_laboratorio_valido(self):
        # Arrange / Act
        laboratorio = LaboratorioCreate(
            nome="Laboratório de Redes",
            localizacao="Bloco A - Sala 12",
            status="ativo",
        )

        # Assert
        assert laboratorio.nome == "Laboratório de Redes"
        assert laboratorio.localizacao == "Bloco A - Sala 12"
        assert laboratorio.status == "ativo"

    def test_deve_rejeitar_nome_com_um_caractere(self):
        # Arrange / Act
        with pytest.raises(ValidationError) as exc:
            LaboratorioCreate(nome="A", localizacao="Bloco A")

        # Assert
        assert "at least 2 characters" in str(exc.value)
        assert exc.value.errors()[0]["loc"] == ("nome",)

    def test_deve_aceitar_tamanhos_maximos_definidos(self):
        # Arrange
        nome = "N" * 80
        localizacao = "L" * 120

        # Act
        laboratorio = LaboratorioCreate(nome=nome, localizacao=localizacao)

        # Assert
        assert len(laboratorio.nome) == 80
        assert len(laboratorio.localizacao) == 120


@pytest.mark.unit
class TestLoginRequest:
    def test_deve_aceitar_email_e_senha_validos(self):
        # Arrange / Act
        login = LoginRequest(email="admin@escola.edu", password="Senha123")

        # Assert
        assert login.email == "admin@escola.edu"
        assert login.password == "Senha123"

    def test_deve_rejeitar_email_em_formato_invalido(self):
        # Arrange / Act
        with pytest.raises(ValidationError) as exc:
            LoginRequest(email="email-invalido", password="Senha123")

        # Assert
        assert "valid email address" in str(exc.value)
        assert exc.value.errors()[0]["loc"] == ("email",)

    def test_deve_aceitar_senha_com_um_caractere_no_limite_minimo(self):
        # Arrange / Act
        login = LoginRequest(email="gestor@escola.edu", password="x")

        # Assert
        assert login.password == "x"
