"""Hardware/resource-aware execution planning for FinAI.

The resource profile is routing metadata and is intentionally conservative.
It is not a benchmark of actual model memory consumption.
"""

from dataclasses import dataclass
import ctypes
import os
import platform
import shutil
from typing import Any, Optional


@dataclass(frozen=True)
class HardwareSnapshot:
    cpu_cores: int
    ram_gb: float
    vram_gb: float
    storage_free_gb: float
    cuda_available: bool
    platform: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_cores": self.cpu_cores,
            "ram_gb": round(self.ram_gb, 2),
            "vram_gb": round(self.vram_gb, 2),
            "storage_free_gb": round(self.storage_free_gb, 2),
            "cuda_available": self.cuda_available,
            "platform": self.platform,
        }


@dataclass(frozen=True)
class ResourceDecision:
    execution_mode: str
    resource_fit: bool
    reason: str
    required_ram_gb: float
    required_vram_gb: float
    gpu_required: bool
    snapshot: HardwareSnapshot

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_mode": self.execution_mode,
            "resource_fit": self.resource_fit,
            "reason": self.reason,
            "required_ram_gb": self.required_ram_gb,
            "required_vram_gb": self.required_vram_gb,
            "gpu_required": self.gpu_required,
            "snapshot": self.snapshot.to_dict(),
        }


def _windows_memory_gb() -> Optional[float]:
    if platform.system() != "Windows":
        return None

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return status.ullTotalPhys / (1024 ** 3)
    return None


def _ram_gb() -> float:
    windows_ram = _windows_memory_gb()
    if windows_ram is not None:
        return windows_ram

    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / (1024 ** 2)
    except (OSError, ValueError):
        pass

    return 0.0


def _cuda_snapshot() -> tuple[bool, float]:
    try:
        import torch

        if torch.cuda.is_available():
            free_bytes, _ = torch.cuda.mem_get_info()
            total_bytes = torch.cuda.get_device_properties(0).total_memory
            return True, max(free_bytes, total_bytes) / (1024 ** 3)
    except Exception:
        pass

    return False, 0.0


def detect_hardware() -> HardwareSnapshot:
    cuda_available, vram_gb = _cuda_snapshot()
    root = os.path.abspath(os.sep)
    storage_free_gb = shutil.disk_usage(root).free / (1024 ** 3)

    return HardwareSnapshot(
        cpu_cores=max(1, os.cpu_count() or 1),
        ram_gb=_ram_gb(),
        vram_gb=vram_gb,
        storage_free_gb=storage_free_gb,
        cuda_available=cuda_available,
        platform=platform.system().lower(),
    )


def assess_local_model(
    *,
    required_ram_gb: float,
    required_vram_gb: float,
    gpu_required: bool = False,
    snapshot: Optional[HardwareSnapshot] = None,
) -> ResourceDecision:
    snapshot = snapshot or detect_hardware()

    ram_ok = snapshot.ram_gb >= required_ram_gb
    vram_ok = required_vram_gb <= 0 or (
        snapshot.cuda_available and snapshot.vram_gb >= required_vram_gb
    )

    if not ram_ok:
        mode = "cloud_fallback"
        reason = "local model does not fit configured RAM requirements"
        fit = False
    elif gpu_required and not vram_ok:
        mode = "cloud_fallback"
        reason = "local model requires GPU resources that are unavailable"
        fit = False
    elif required_vram_gb > 0 and vram_ok:
        mode = "local_gpu"
        reason = "local model fits configured RAM and preferred VRAM requirements"
        fit = True
    else:
        mode = "local_ram"
        reason = "local model fits configured RAM requirements"
        fit = True

    return ResourceDecision(
        execution_mode=mode,
        resource_fit=fit,
        reason=reason,
        required_ram_gb=float(required_ram_gb),
        required_vram_gb=float(required_vram_gb),
        gpu_required=bool(gpu_required),
        snapshot=snapshot,
    )
