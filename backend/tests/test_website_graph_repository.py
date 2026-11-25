from backend.app.repositories.website_graph_repository import WebsiteGraphRepository


def test_graph_repository_saves_links_and_analysis_payloads():
    state = {"websites": {}, "links": [], "analyses": []}
    repository = WebsiteGraphRepository("postgresql://fake", connect=lambda _: FakeConnection(state))

    repository.save_website("https://example.com/", {"title": "Example"})
    repository.save_link("https://example.com/", {"url": "https://fake.example/login", "role": "login"})
    repository.save_analysis("https://example.com/", {"category": "elevated_risk"})

    assert state["websites"]["https://example.com/"] == {"title": "Example"}
    assert state["links"][0]["role"] == "login"
    assert state["analyses"][0]["payload"]["category"] == "elevated_risk"


class FakeCursor:
    def __init__(self, state):
        self.state = state

    def execute(self, sql, params=None):
        if "CREATE TABLE" in sql:
            return
        if "INSERT INTO scamguard_websites" in sql:
            import json
            self.state["websites"][params[0]] = json.loads(params[1])
        elif "INSERT INTO scamguard_website_links" in sql:
            import json
            self.state["links"].append(json.loads(params[2]))
        elif "INSERT INTO scamguard_website_analyses" in sql:
            import json
            self.state["analyses"].append({"url": params[0], "payload": json.loads(params[1])})

    def close(self):
        pass


class FakeConnection:
    def __init__(self, state):
        self.cursor_instance = FakeCursor(state)

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass
