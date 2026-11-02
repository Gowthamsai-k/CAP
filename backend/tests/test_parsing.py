from app.services.parsing import company_chunks, legal_chunks


def test_legal_chunking_keeps_section_heading_with_content():
    chunks = legal_chunks("Preamble\n\nSection 1. Definitions\n\nPersonal data means data about an individual.\n\nSection 2. Scope\n\nThis Act applies.")
    assert chunks[0][0] is None
    assert chunks[1][0] == "Section 1. Definitions"
    assert "Personal data" in chunks[1][1]
    assert chunks[2][0] == "Section 2. Scope"


def test_legal_chunking_splits_large_paragraphs_with_parent_section():
    chunks = legal_chunks("Section 8\n\n" + "x" * 4000, max_chars=1000)
    assert len(chunks) == 4
    assert all(section == "Section 8" for section, _ in chunks)
    assert all("x" in text for _, text in chunks)


def test_company_markdown_chunking_keeps_policy_heading_as_metadata():
    chunks = company_chunks("# Retention\n\nDelete support tickets after the fictional retention period.")
    assert len(chunks) == 1
    assert chunks[0][0] == "Retention"
    assert "Delete support tickets" in chunks[0][1]
