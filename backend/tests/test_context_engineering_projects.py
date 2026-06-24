"""Project registry: deterministic structure checks (no LLM)."""

from feature_context_engineering.projects import get_project, list_projects


def test_list_projects_nonempty():
    projects = list_projects()
    assert projects
    assert all(p.id and p.title and p.brief for p in projects)


def test_get_project_known_and_unknown():
    assert get_project("todo-api") is not None
    assert get_project("does-not-exist") is None


def test_files_have_content_and_dirs_inferred():
    for project in list_projects():
        files = [f for f in project.files if f.kind == "file"]
        dirs = [f for f in project.files if f.kind == "dir"]
        # every file carries its full content (served whole for the left panel)
        assert files and all(f.content for f in files), project.id
        # directories are inferred from paths and carry no content
        assert all(d.content is None for d in dirs), project.id


def test_tree_is_consistent():
    for project in list_projects():
        # no duplicate paths
        assert len({f.path for f in project.files}) == len(project.files), project.id
        # every nested file's parent directories exist as dir nodes
        dir_paths = {f.path for f in project.files if f.kind == "dir"}
        for f in project.files:
            if f.kind == "file" and "/" in f.path:
                assert f.path.rsplit("/", 1)[0] in dir_paths, f.path
