from growme.research.aliasing import alias_text, alias_obj


def test_alias_text_replaces_neon_with_photon_db():
    src = "Neon is a serverless Postgres. Try neon.tech today."
    out = alias_text(src, real="Neon", alias="Photon DB", real_url="neon.tech", alias_url="photondb.io")
    assert "Photon DB" in out
    assert "Neon" not in out
    assert "photondb.io" in out
    assert "neon.tech" not in out


def test_alias_text_case_insensitive():
    out = alias_text("NEON neon Neon", "Neon", "Photon DB", "neon.tech", "photondb.io")
    assert "NEON" not in out and "neon" not in out


def test_alias_obj_recurses_into_dicts_and_lists():
    src = {"a": "Neon is great", "b": ["use neon.tech", {"c": "Neon"}]}
    out = alias_obj(src, "Neon", "Photon DB", "neon.tech", "photondb.io")
    assert out == {"a": "Photon DB is great", "b": ["use photondb.io", {"c": "Photon DB"}]}
