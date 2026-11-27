# Copyright (c) 2026 Thorben Meier. MIT License.
"""Das Panel für Hardware-Test und Modellwahl baut sich auf und schaltet Modelle um (ohne LM Studio)."""

from types import SimpleNamespace

import pytest

ctk = pytest.importorskip("customtkinter")

from services import hardware_probe, llm_service, local_benchmark, local_server, model_catalog  # noqa: E402
from services.model_catalog import Measurement  # noqa: E402


@pytest.fixture
def root():
    try:
        r = ctk.CTk()
    except Exception as e:                       # kein Bildschirm
        pytest.skip(f"keine Oberfläche: {e}")
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture(autouse=True)
def no_real_lm_studio(monkeypatch):
    monkeypatch.setattr(local_server, "start_local_server", lambda *a, **k: local_server.StartResult(False, "aus"))
    monkeypatch.setattr(local_server, "run_lms", lambda *a, **k: pytest.fail("darf lms nicht ausführen"))
    monkeypatch.setattr(llm_service, "list_models", lambda *a, **k: ["gemma-4-e2b-it", "text-embedding-x"])


def make_panel(root, model="gemma-4-e2b-it"):
    from features.ui.local_ai_panel import LocalAiPanel
    app = SimpleNamespace(settings=SimpleNamespace(custom_llm_model=model))
    activated, models = [], []
    panel = LocalAiPanel(
        root, app, get_url=lambda: "http://localhost:1234/v1", get_key=lambda: "",
        on_activate=activated.append, on_models=models.append,
    )
    panel.pack()
    return panel, activated, models


def wait(root, panel, seconds=5):
    import time
    end = time.time() + seconds
    while panel._busy and time.time() < end:
        root.update()
        time.sleep(0.05)
    root.update()


def test_panel_zeigt_alle_modelle_auch_nicht_installierte(root):
    panel, _, _ = make_panel(root)
    labels = list(panel._labels)
    assert len(labels) == len(model_catalog.CATALOG)
    assert any("Qwen 3.5 9B" in label and "nicht installiert" in label for label in labels)
    assert any("Gemma 4 E2B" in label and "aktiv" in label for label in labels)


def test_hardware_pruefung_empfiehlt_und_fuellt_die_modellliste(root, monkeypatch):
    monkeypatch.setattr(
        hardware_probe, "detect",
        lambda: hardware_probe.Hardware(ram_gb=32, cpu_threads=16, gpus=[hardware_probe.Gpu("Karte", 11)]),
    )
    panel, _, models = make_panel(root)
    panel._check_hardware()
    wait(root, panel)
    assert panel._recommended.key == "google/gemma-4-e4b"
    assert any("⭐" in label and "E4B" in label for label in panel._labels)
    assert models == [["gemma-4-e2b-it", "text-embedding-x"]]
    assert "Karte (11 GB)" in panel._hw_label.cget("text")


def test_installiertes_modell_wird_ohne_download_verwendet(root):
    panel, activated, _ = make_panel(root, model="")
    panel._installed = ["gemma-4-e2b-it"]
    panel._selected = model_catalog.by_key("gemma-4-e2b-it")
    panel._use_selected()
    assert activated == ["gemma-4-e2b-it"]


def test_fehlendes_modell_wird_nur_nach_rueckfrage_geladen(root, monkeypatch):
    from features.ui import local_ai_panel
    panel, activated, _ = make_panel(root)
    panel._selected = model_catalog.by_key("qwen/qwen3.5-9b")
    monkeypatch.setattr(local_ai_panel.messagebox, "askyesno", lambda *a, **k: False)
    monkeypatch.setattr(local_benchmark, "download", lambda *a, **k: pytest.fail("darf nicht laden"))
    panel._use_selected()
    assert activated == [] and not panel._busy


def test_download_nach_zusage_und_danach_aktiviert(root, monkeypatch):
    from features.ui import local_ai_panel
    panel, activated, _ = make_panel(root)
    panel._selected = model_catalog.by_key("qwen/qwen3.5-9b")
    monkeypatch.setattr(local_ai_panel.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(local_benchmark, "download", lambda m, url, progress: (True, "ok"))
    monkeypatch.setattr(llm_service, "list_models", lambda *a, **k: ["gemma-4-e2b-it", "qwen3.5-9b"])
    panel._use_selected()
    wait(root, panel)
    assert activated == ["qwen3.5-9b"]               # Name, wie ihn der Server meldet


def test_gescheiterter_download_aktiviert_nichts(root, monkeypatch):
    from features.ui import local_ai_panel
    panel, activated, _ = make_panel(root)
    panel._selected = model_catalog.by_key("qwen/qwen3.5-9b")
    monkeypatch.setattr(local_ai_panel.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(local_benchmark, "download", lambda m, url, progress: (False, "Kein Platz"))
    panel._use_selected()
    wait(root, panel)
    assert activated == [] and "Kein Platz" in panel._status.cget("text")


def test_tempomessung_waehlt_das_beste_modell_vor(root, monkeypatch):
    panel, _, _ = make_panel(root)
    by = model_catalog.by_key

    def fake_measure(m, url, key, progress):
        return Measurement(model=m, ok=True, tps=10, dictation_s=8, protocol_s=40 if m.quality < 4 else 90)

    monkeypatch.setattr(local_benchmark, "measure", fake_measure)
    monkeypatch.setattr(llm_service, "list_models", lambda *a, **k: ["gemma-4-e2b-it", "gemma-4-e4b-it"])
    panel._measure_all()
    wait(root, panel)
    assert panel._selected.key == by("gemma-4-e4b-it").key
    assert "Gemessen" in panel._detail.cget("text")


def test_tempomessung_ohne_installiertes_modell_meldet_das(root, monkeypatch):
    panel, _, _ = make_panel(root)
    monkeypatch.setattr(llm_service, "list_models", lambda *a, **k: ["text-embedding-x"])
    monkeypatch.setattr(local_benchmark, "measure", lambda *a, **k: pytest.fail("nichts zu messen"))
    panel._measure_all()
    wait(root, panel)
    assert "Noch kein Modell" in panel._status.cget("text")
