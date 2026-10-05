from llm.resource_orchestrator import (
    HardwareSnapshot,
    assess_local_model,
)


def test_local_gpu_fit():
    hardware = HardwareSnapshot(
        cpu_cores=8,
        ram_gb=16.0,
        vram_gb=6.5,
        storage_free_gb=100.0,
        cuda_available=True,
        platform="test",
    )
    result = assess_local_model(
        required_ram_gb=4.0,
        required_vram_gb=4.0,
        gpu_required=False,
        snapshot=hardware,
    )
    assert result.resource_fit is True
    assert result.execution_mode == "local_gpu"


def test_local_ram_fallback_without_gpu():
    hardware = HardwareSnapshot(
        cpu_cores=8,
        ram_gb=16.0,
        vram_gb=0.0,
        storage_free_gb=100.0,
        cuda_available=False,
        platform="test",
    )
    result = assess_local_model(
        required_ram_gb=4.0,
        required_vram_gb=0.0,
        snapshot=hardware,
    )
    assert result.resource_fit is True
    assert result.execution_mode == "local_ram"


def test_gpu_required_model_falls_back_when_gpu_is_unavailable():
    hardware = HardwareSnapshot(
        cpu_cores=8,
        ram_gb=16.0,
        vram_gb=0.0,
        storage_free_gb=100.0,
        cuda_available=False,
        platform="test",
    )
    result = assess_local_model(
        required_ram_gb=4.0,
        required_vram_gb=4.0,
        gpu_required=True,
        snapshot=hardware,
    )
    assert result.resource_fit is False
    assert result.execution_mode == "cloud_fallback"


def test_local_model_fails_when_ram_is_insufficient():
    hardware = HardwareSnapshot(
        cpu_cores=4,
        ram_gb=2.0,
        vram_gb=8.0,
        storage_free_gb=100.0,
        cuda_available=True,
        platform="test",
    )
    result = assess_local_model(
        required_ram_gb=4.0,
        required_vram_gb=4.0,
        snapshot=hardware,
    )
    assert result.resource_fit is False
    assert result.execution_mode == "cloud_fallback"
