from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="CLOCKIFY_ETL",
    settings_files=["settings.toml", ".secrets.toml"],
)
