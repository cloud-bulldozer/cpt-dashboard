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

    def jql(self, query: str, fields="*all", expand=None, validate_query=None):
        return self.svc.jql(
            jql=query,
            fields=fields,
            expand=expand,
            validate_query=validate_query
        )
