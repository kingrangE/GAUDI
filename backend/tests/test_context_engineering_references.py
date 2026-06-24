"""Gold reference (answer key) invariants: present for every project, never leaked via API."""

from feature_context_engineering.projects import list_projects
from feature_context_engineering.references import get_reference, has_reference


def test_every_project_has_a_gold_reference():
    for project in list_projects():
        gold = get_reference(project.id)
        assert gold and gold.strip(), project.id
        assert has_reference(project.id)


def test_unknown_project_has_no_reference():
    assert get_reference("does-not-exist") is None
    assert has_reference("does-not-exist") is False


def test_gold_reference_is_not_part_of_the_served_payload():
    # The answer key must never ship to the candidate: no served file carries the gold doc.
    for project in list_projects():
        gold = get_reference(project.id)
        for f in project.files:
            assert f.content != gold, project.id
