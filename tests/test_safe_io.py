"""Regression checks for writing reports into an untrusted checkout."""

from __future__ import annotations

import os
import stat

import pytest

from stride_gpt.agent import safe_io
from stride_gpt.agent.safe_io import atomic_write_text, prepare_output_path


@pytest.fixture(params=["native", "portable"])
def writer_mode(request, monkeypatch):
    if request.param == "portable":
        monkeypatch.setattr(safe_io, "_has_dir_fd", lambda: False)


def test_atomic_replace_does_not_modify_other_hardlink(tmp_path, writer_mode):
    outside = tmp_path / "outside"
    outside.write_text("original")
    destination = tmp_path / "report.json"
    destination.hardlink_to(outside)
    atomic_write_text(destination, "new report")
    assert destination.read_text() == "new report"
    assert outside.read_text() == "original"
    assert not list(tmp_path.glob(".stride-export-*"))


def test_destination_symlink_refuses_without_touching_target(tmp_path, writer_mode):
    outside = tmp_path / "outside"
    outside.write_text("original")
    destination = tmp_path / "report.json"
    destination.symlink_to(outside)
    with pytest.raises(OSError):
        atomic_write_text(destination, "new report")
    assert outside.read_text() == "original"
    assert destination.is_symlink()
    assert not list(tmp_path.glob(".stride-export-*"))


def test_parent_symlink_refuses_before_creating_children(tmp_path, writer_mode):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "exports").symlink_to(outside, target_is_directory=True)
    destination = tmp_path / "exports" / "nested" / "report.json"
    with pytest.raises(OSError):
        prepare_output_path(destination)
    with pytest.raises(OSError):
        atomic_write_text(destination, "report", create_parents=True)
    assert list(outside.iterdir()) == []


def test_private_utf8_export_and_parent_creation(tmp_path, writer_mode):
    destination = tmp_path / "new" / "nested" / "report.json"
    atomic_write_text(destination, "résumé\n", create_parents=True)
    assert destination.read_text(encoding="utf-8") == "résumé\n"
    if os.name == "posix":
        assert stat.S_IMODE(destination.stat().st_mode) == 0o600
        assert stat.S_IMODE(destination.parent.stat().st_mode) == 0o700


def test_replace_failure_leaves_old_report_and_cleans_temp(tmp_path, writer_mode, monkeypatch):
    destination = tmp_path / "report.json"
    destination.write_text("original")

    def fail(*args, **kwargs):
        raise OSError("simulated filesystem failure")

    monkeypatch.setattr(safe_io.os, "replace", fail)
    with pytest.raises(OSError, match="simulated"):
        atomic_write_text(destination, "new report")
    assert destination.read_text() == "original"
    assert not list(tmp_path.glob(".stride-export-*"))


def test_destination_changed_to_symlink_during_write_is_replaced(tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.write_text("original")
    destination = tmp_path / "report.json"
    replace = os.replace

    def swap_then_replace(src, dst, **kwargs):
        destination.symlink_to(outside)
        return replace(src, dst, **kwargs)

    monkeypatch.setattr(safe_io.os, "replace", swap_then_replace)
    atomic_write_text(destination, "new report")
    assert outside.read_text() == "original"
    assert not destination.is_symlink()
    assert destination.read_text() == "new report"


@pytest.mark.skipif(not safe_io._has_dir_fd(), reason="requires descriptor-relative operations")
def test_parent_swapped_after_open_does_not_redirect_export(tmp_path, monkeypatch):
    parent = tmp_path / "export"
    parent.mkdir()
    original_parent = tmp_path / "original-export"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "report.json").write_text("original")
    replace = os.replace

    def swap_then_replace(src, dst, **kwargs):
        parent.rename(original_parent)
        parent.symlink_to(outside, target_is_directory=True)
        return replace(src, dst, **kwargs)

    monkeypatch.setattr(safe_io.os, "replace", swap_then_replace)
    atomic_write_text(parent / "report.json", "new report")
    assert (outside / "report.json").read_text() == "original"
    assert (original_parent / "report.json").read_text() == "new report"
