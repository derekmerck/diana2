import logging
import attr
from .requester import Requester

@attr.s
class FigshareGateway(Requester):

    host = attr.ib(default="api.figshare.com")
    protocol = attr.ib(default="https")
    path = attr.ib(default="v2")
    port = attr.ib(default=443)

    def setup_auth_header(self):
        return {'Authorization': f'token {self.auth_tok}'}

    def account_info(self):
        resource = "account"
        return self._get(resource)

    # Article object API
    # ---------------------

    def articles(self, private=True):
        resource = "articles"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def get_article(self, item_id, private=True):
        resource = f"articles/{item_id}"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def find_articles(self, query=None, private=True):
        resource = f"articles/search"
        if private:
            resource = "account/" + resource
        return self._post(resource, json=query)

    def create_article(self, data, private=True):
        pass

    def delete_article(self, article_id, private=True):
        pass

    # File object API
    # ---------------------

    def files(self, article_id, private=True):
        resource = f"articles/{article_id}/files"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def get_file(self, article_id, file_id, private=True):
        resource = f"articles/{article_id}/files/{file_id}"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def upload_file(self, article_id, data, private=True):
        resource = f"articles/{article_id}/files"
        if private:
            resource = "account/" + resource

        file_id = self._post(resource)

        logger = logging.getLogger(self.name)
        logger.debug(f"Created new file_id: {file_id}")

        resource = f"articles/{article_id}/files/{file_id}"
        if private:
            resource = "account/" + resource

        return self._post(resource, data=data)

    def delete_file(self, article_id, file_id, private=True):
        resource = f"articles/{article_id}/files/{file_id}"
        if private:
            resource = "account/" + resource
        return self._delete(resource)

    # Collection object API
    # ---------------------

    def collections(self, private=True):
        resource = "collections"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def get_collection(self, item_id, private=True):
        resource = f"collections/{item_id}"
        if private:
            resource = "account/" + resource
        return self._get(resource)

    def find_collections(self, query=None, private=True):
        resource = f"collections/search"
        if private:
            resource = "account/" + resource
        return self._post(resource, json=query)

    def create_collection(self, data, private=True):
        pass

    def delete_collection(self, item_id, private=True):
        pass
