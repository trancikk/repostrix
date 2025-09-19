from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str
    dev_mode: bool = False

    class Config:
        env_file = ".env"

    def db_prop(self) -> str:
        return self.db_user + ":" + self.db_password + "@" + self.db_host + ":" + str(
            self.db_port) + "/" + self.db_name

    @property
    def db_async_url(self) -> str:
        return "postgresql+asyncpg://" + self.db_prop()

    @property
    def db_url(self) -> str:
        return "postgresql+psycopg2://" + self.db_prop()


settings = Settings()
