import os

from typer.testing import CliRunner

from infrahub.git_credential.askpass import app

runner = CliRunner(mix_stderr=False)


def test_askpass_username(helper, mock_core_schema_01, mock_repositories_query):
    config_file = os.path.join(helper.get_fixtures_dir(), "config_files", "infrahub_testing_01.toml")

    input_data = "Username for 'https://github.com/opsmill/infrahub-demo-edge.git'"

    result = runner.invoke(app=app, args=["--config-file", str(config_file), input_data])
    assert not result.stderr
    assert result.stdout == "myusername\n"
    assert result.exit_code == 0


def test_askpass_password(helper, mock_core_schema_01, mock_repositories_query):
    config_file = os.path.join(helper.get_fixtures_dir(), "config_files", "infrahub_testing_01.toml")

    input_data = "Password for 'https://username@github.com/opsmill/infrahub-demo-edge.git'"

    result = runner.invoke(app=app, args=["--config-file", str(config_file), input_data])
    assert not result.stderr
    assert result.stdout == "mypassword\n"
    assert result.exit_code == 0
