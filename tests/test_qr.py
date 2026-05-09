from growme.qr import generate_qr_png


def test_generate_qr_png_returns_png_bytes():
    data = generate_qr_png("http://localhost:8501/?assessment=abc&kind=pre")
    assert isinstance(data, bytes) and len(data) > 100
    assert data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic
