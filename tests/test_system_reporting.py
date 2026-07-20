from __future__ import annotations

import socket

import pytest

from src.system.reporting import (
    format_system_report,
    generate_system_report,
    get_basic_system_info,
    get_disk_usage,
    get_network_info,
    get_python_environment_info,
    get_resource_usage,
)


def test_system_information_is_structured() -> None:
    basic = get_basic_system_info()
    python_info = get_python_environment_info()
    assert basic["os_name"]
    assert python_info["python_executable"]


def test_disk_usage_reports_existing_path(tmp_path) -> None:
    usage = get_disk_usage([str(tmp_path), str(tmp_path / "missing")])
    assert str(tmp_path) in usage
    assert str(tmp_path / "missing") not in usage


def test_network_probe_is_bounded_and_labeled() -> None:
    info = get_network_info()
    assert set(info) >= {"ip_addresses", "internet_connected", "dns_resolution", "errors"}


def test_network_probe_validates_inputs() -> None:
    with pytest.raises(ValueError, match="timeout"):
        get_network_info(timeout=0)
    with pytest.raises(ValueError, match="dns_host"):
        get_network_info(dns_host=" ")


def test_network_probe_reports_labeled_failures(monkeypatch) -> None:
    def fail_addrinfo(*_args, **_kwargs):
        raise OSError("local lookup failed")

    def fail_connection(*_args, **_kwargs):
        raise OSError("connect failed")

    def fail_dns(*_args, **_kwargs):
        raise OSError("dns failed")

    monkeypatch.setattr(socket, "getaddrinfo", fail_addrinfo)
    monkeypatch.setattr(socket, "create_connection", fail_connection)
    monkeypatch.setattr(socket, "gethostbyname", fail_dns)

    info = get_network_info(timeout=0.01, dns_host="example.invalid")

    assert info["internet_connected"] is False
    assert info["dns_resolution"] is False
    assert any(error.startswith("local_address:") for error in info["errors"])
    assert any(error.startswith("internet:") for error in info["errors"])
    assert any(error.startswith("dns:") for error in info["errors"])


def test_system_report_preserves_network_diagnostics() -> None:
    report = generate_system_report()
    assert isinstance(report.network_errors, list)


def test_formatted_report_and_resource_fallbacks(monkeypatch) -> None:
    report = generate_system_report()
    report.network_errors = ["dns: unavailable"]
    rendered = format_system_report(report, detailed=True)
    assert "Network diagnostics:" in rendered
    assert "dns: unavailable" in rendered

    import builtins

    real_import = builtins.__import__

    def import_without_psutil(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_psutil)
    usage = get_resource_usage()
    assert usage.cpu_percent == 0.0
