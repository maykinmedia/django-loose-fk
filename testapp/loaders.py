from django_loose_fk.loaders import BaseLoader


class DummyLoader(BaseLoader):
    @staticmethod
    def fetch_object(url: str) -> dict:
        return {"url": url, "name": "dummy"}
