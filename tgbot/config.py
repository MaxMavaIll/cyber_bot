from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str

    def dsn(self):
        return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"


@dataclass
class MintScanApi:
    base_url: str
    token: str


@dataclass
class Config:
    tg_bot: TgBot
    redis_config: RedisConfig
    misc: Miscellaneous
    mint_scan_api: MintScanApi


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
        ),
        redis_config=RedisConfig(
            host=env.str('REDIS_HOST'),
            port=env.int('REDIS_PORT'),
            db=env.int('REDIS_DB'),
            password=env.str('REDIS_PASSWORD')
        ),
        misc=Miscellaneous(),
        mint_scan_api=MintScanApi(
            base_url=env.str('MINT_SCAN_API_BASE_URL'),
            token=env.str('MINT_SCAN_API_TOKEN')
        )
    )
