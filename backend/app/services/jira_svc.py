from atlassian import Jira

from app import config


class JiraService:

    def __init__(self, configpath="jira"):
        self.cfg = config.get_config()
        self.url = self.cfg.get(configpath+'.url')
        self.pat = self.cfg.get(configpath+'.access_token')
        self.svc = Jira(
            url=self.url,
            access_token=self.pat
        )
