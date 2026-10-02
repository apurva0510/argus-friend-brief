from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_loads_all_companies_from_snapshot():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py").run(timeout=10)

    assert not app.exception
    assert len(app.selectbox) == 1
    assert len(app.selectbox[0].options) == 53
    assert app.selectbox[0].value == "NVDA"
