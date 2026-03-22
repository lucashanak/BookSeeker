from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class DownloadRequest(BaseModel):
    title: str
    indexer: str = ""
    download_url: str = ""
    magnet_url: str = ""
    size: int = 0
    seeders: int = 0


class SettingsUpdate(BaseModel):
    prowlarr_url: str = ""
    prowlarr_api_key: str = ""
    qbit_url: str = ""
    abs_url: str = ""


class CreateUserRequest(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class ChangePasswordRequest(BaseModel):
    new_password: str
