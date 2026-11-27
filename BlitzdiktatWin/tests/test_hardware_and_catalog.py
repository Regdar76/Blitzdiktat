# Copyright (c) 2026 Thorben Meier. MIT License.
"""Hardware-Erkennung und Modellempfehlung für die lokale KI."""

import pytest

from services import hardware_probe as hp
from services import model_catalog as mc


def hw(ram=32.0, threads=16, vram=0.0) -> hp.Hardware:
    gpus = [hp.Gpu("Testkarte", vram)] if vram else []
    return hp.Hardware(ram_gb=ram, cpu_threads=threads, gpus=gpus)


# ── Ausgaben der Programme lesen ────────────────────────────────────────────

def test_nvidia_smi_ausgabe():
    gpus = hp.parse_nvidia_smi("NVIDIA GeForce RTX 2080 Ti, 11264\nNVIDIA T400, 4096\n")
    assert [(g.name, round(g.vram_gb)) for g in gpus] == [("NVIDIA GeForce RTX 2080 Ti", 11), ("NVIDIA T400", 4)]


def test_nvidia_smi_unsinn_wird_ignoriert():
    assert hp.parse_nvidia_smi("kein Treiber gefunden\n") == []
    assert hp.parse_nvidia_smi("") == []


def test_lms_survey_ausgabe():
    text = (
        "Survey by llama.cpp-win-x86_64-nvidia-cuda12-avx2 (2.83.0)\n"
        "GPU/ACCELERATORS                              VRAM     \n"
        "NVIDIA GeForce RTX 2080 Ti (CUDA, Discrete)   11.00 GiB\n"
        "\n"
        "CPU: x86_64 (AVX, AVX2)\n"
        "RAM: 31.92 GiB\n"
    )
    gpus = hp.parse_lms_survey(text)
    assert len(gpus) == 1
    assert gpus[0].name == "NVIDIA GeForce RTX 2080 Ti" and gpus[0].vram_gb == pytest.approx(11.0)


def test_beschreibung():
    h = hw(ram=32, threads=16, vram=11)
    assert "32 GB" in h.describe() and "16" in h.describe() and "Testkarte (11 GB)" in h.describe()
    assert "keine Grafikkarte" in hw().describe()
    assert h.best_vram_gb == 11 and hw().best_vram_gb == 0


# ── Empfehlung ──────────────────────────────────────────────────────────────

def test_starke_grafikkarte_bekommt_groesstes_passendes_modell():
    rec, _ = mc.recommend(hw(vram=24))
    assert rec.key == "qwen/qwen3.5-9b"


def test_mittlere_grafikkarte_bekommt_gemma_e4b():
    rec, ratings = mc.recommend(hw(vram=11))
    assert rec.key == "google/gemma-4-e4b"
    assert next(r for r in ratings if r.model.key == rec.key).on_gpu


def test_ohne_grafikkarte_bleibt_es_beim_kleinen_standardmodell():
    rec, _ = mc.recommend(hw(ram=16, threads=8))
    assert rec.key == "google/gemma-4-e2b"


def test_zu_wenig_arbeitsspeicher_ohne_grafikkarte_empfiehlt_nichts():
    rec, ratings = mc.recommend(hw(ram=8, threads=4))
    assert rec is None
    assert all(not r.fits and r.reason for r in ratings)


def test_modell_ohne_passenden_speicher_wird_nicht_empfohlen():
    rec, ratings = mc.recommend(hw(ram=10, threads=16))
    by_key = {r.model.key: r for r in ratings}
    assert by_key["google/gemma-4-e2b"].fits
    assert not by_key["qwen/qwen3.5-9b"].fits
    assert rec.key == "google/gemma-4-e2b"


def test_langsamer_rechner_bekommt_das_schnellste_statt_nichts():
    rec, _ = mc.recommend(hw(ram=12, threads=2))
    assert rec is not None


# ── Messung ─────────────────────────────────────────────────────────────────

def _m(key: str, ok=True, dictation=10.0, protocol=60.0) -> mc.Measurement:
    return mc.Measurement(model=mc.by_key(key), ok=ok, tps=10, dictation_s=dictation, protocol_s=protocol)


def test_beste_gemessene_wahl_ist_das_genaueste_flotte_modell():
    best = mc.pick_best([_m("gemma-4-e2b-it", protocol=40), _m("gemma-4-e4b-it", protocol=100)])
    assert best.key == "google/gemma-4-e4b"


def test_zu_langsames_modell_wird_uebergangen():
    best = mc.pick_best([_m("gemma-4-e2b-it", protocol=40), _m("qwen/qwen3.5-9b", dictation=60, protocol=400)])
    assert best.key == "google/gemma-4-e2b"


def test_ist_alles_langsam_gewinnt_das_schnellste():
    best = mc.pick_best([_m("gemma-4-e2b-it", dictation=50, protocol=300), _m("gemma-4-e4b-it", dictation=90, protocol=500)])
    assert best.key == "google/gemma-4-e2b"


def test_fehlgeschlagene_messung_zaehlt_nicht():
    assert mc.pick_best([_m("gemma-4-e4b-it", ok=False)]) is None
    assert mc.pick_best([_m("google/gemma-4-e4b", ok=False), _m("google/gemma-4-e2b")]).key == "google/gemma-4-e2b"


# ── Katalog ─────────────────────────────────────────────────────────────────

def test_modellnamen_werden_ohne_herausgeber_gefunden():
    assert mc.by_key("Qwen/Qwen3.5-9B").key == "qwen/qwen3.5-9b"
    assert mc.by_key("gemma-4-E2B-it").key == "google/gemma-4-e2b"
    assert mc.by_key("unbekannt") is None


def test_installiert_wird_ueber_den_servernamen_erkannt():
    m = mc.by_key("qwen/qwen3.5-9b")
    assert mc.is_installed(m, ["text-embedding-nomic", "qwen3.5-9b"])
    assert not mc.is_installed(m, ["gemma-4-e2b-it"])
    assert not mc.is_installed(m, [])


def test_zeitangaben():
    assert mc.format_duration(12.4) == "12 s"
    assert mc.format_duration(150) == "2,5 min"
    assert mc.speed_label(30) == "schnell" and mc.speed_label(100) == "mittel" and mc.speed_label(400) == "langsam"


def test_standardmodell_des_installers_steht_im_katalog():
    assert mc.by_key("gemma-4-e2b-it") is not None


def test_server_nennt_dasselbe_modell_alt_oder_neu():
    m = mc.by_key("google/gemma-4-e2b")
    assert mc.is_installed(m, ["gemma-4-e2b-it"])               # Name nach Installer-Download
    assert mc.is_installed(m, ["google/gemma-4-e2b"])           # Name nach "lms get"
    assert mc.server_name(m, ["x", "google/gemma-4-e2b"]) == "google/gemma-4-e2b"
    assert mc.server_name(m, []) is None


def test_umbenanntes_modell_wird_im_server_wiedergefunden():
    # LM Studio führt das Modell nach "lms get" unter einem neuen Namen.
    assert mc.resolve_model("gemma-4-e2b-it", ["google/gemma-4-e2b", "text-embedding-x"]) == "google/gemma-4-e2b"
    assert mc.resolve_model("google/gemma-4-e2b", ["gemma-4-e2b-it"]) == "gemma-4-e2b-it"


def test_unveraenderter_oder_unbekannter_name_wird_nicht_angefasst():
    assert mc.resolve_model("gemma-4-e2b-it", ["gemma-4-e2b-it"]) is None
    assert mc.resolve_model("", ["google/gemma-4-e2b"]) is None
    assert mc.resolve_model("eigenes-modell", ["google/gemma-4-e2b"]) is None
    assert mc.resolve_model("gemma-4-e2b-it", []) is None
