import sys
from typing import Optional

from keycloak.keycloak_openid import KeycloakOpenID
import requests

from app import config


class HorreumService:

    def __init__(self, configpath="horreum"):
        self.cfg = config.get_config()
        self.user = self.cfg.get(configpath + ".username")
        self.password = self.cfg.get(configpath + ".password")
        self.url = self.cfg.get(configpath + ".url")
        try:
            kc = requests.get(f"{self.url}/api/config/keycloak")
            kc.raise_for_status()
        except Exception as e:
            print(f"Failed {str(e)!r}", file=sys.stderr)
            raise
        keycloak = kc.json()
        self.keycloak = KeycloakOpenID(
            keycloak["url"],
            client_id=keycloak["clientId"],
            realm_name=keycloak["realm"],
        )

    def get(
        self, path: str, queries: Optional[dict[str, str]] = None
    ) -> requests.Response:
        token = self.keycloak.token(username=self.user, password=self.password)[
            "access_token"
        ]
        return requests.get(
            f"{self.url}/api/{path}",
            params=queries,
            headers={"authorization": f"Bearer {token}"},
        )
