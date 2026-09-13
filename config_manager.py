"""Versioned settings, legacy migration and atomic writes."""
import json
import os
from pathlib import Path
import sys
import tempfile
from triangle_logic import TriangleState


def app_directory():
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def default_path():
    if os.environ.get("TRIANGLE_STUDIO_CONFIG_DIR"):
        return Path(os.environ["TRIANGLE_STUDIO_CONFIG_DIR"]) / "settings.json"
    base = (Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            if sys.platform == "win32" else Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")))
    return base / "TriangleStudio" / "settings.json"


def normalize_payload(data):
    if not isinstance(data, dict):
        raise ValueError("Cấu hình không đúng định dạng.")
    if "chieu_cao" in data or "chieu_rong" in data:
        state = TriangleState.from_dict({
            "width": data.get("chieu_rong", 420), "height": data.get("chieu_cao", 320),
            "sync": data.get("dong_bo", False), "opacity": max(.15, data.get("opacity", .85)),
            "color": "#008000", "outline": "#008000"})
    else:
        if data.get("version", 2) != 2:
            raise ValueError("Phiên bản cấu hình chưa được hỗ trợ.")
        state = TriangleState.from_dict(data.get("state", {}))
    anchor = data.get("anchor", [data.get("anchor_x", 100), data.get("anchor_y", 650)])
    if (not isinstance(anchor, (list, tuple)) or len(anchor) != 2
            or any(type(v) is not int or abs(v) > 100000 for v in anchor)):
        raise ValueError("Vị trí tam giác không hợp lệ.")
    presets = data.get("presets", {})
    if not isinstance(presets, dict) or len(presets) > 50:
        raise ValueError("Danh sách mẫu không hợp lệ (tối đa 50 mẫu).")
    cleaned = {}
    for name, item in presets.items():
        if not isinstance(name, str) or not name.strip() or len(name) > 40:
            raise ValueError("Tên mẫu phải dài từ 1 đến 40 ký tự.")
        cleaned[name] = TriangleState.from_dict(item).to_dict()
    return {"version": 2, "state": state.to_dict(), "anchor": list(anchor), "presets": cleaned}


class ConfigStore:
    def __init__(self, path=None, legacy_path=None):
        self.path = Path(path) if path is not None else default_path()
        self.legacy_path = Path(legacy_path) if legacy_path is not None else app_directory() / "config.json"
        self.warning = ""
        self.loaded_legacy = False

    def load(self):
        source = self.path if self.path.exists() else self.legacy_path
        if source.exists():
            try:
                if source.stat().st_size > 1_000_000:
                    raise ValueError("Tệp cấu hình quá lớn.")
                data = normalize_payload(json.loads(source.read_text(encoding="utf-8")))
                self.loaded_legacy = source == self.legacy_path
                return data
            except (OSError, ValueError, TypeError) as exc:
                self.warning = f"Không đọc được cấu hình; đang dùng mặc định. {exc}"
                try:
                    if source == self.path:
                        backup = source.with_name(source.name + ".invalid.bak")
                        if not backup.exists():
                            backup.write_bytes(source.read_bytes())
                except OSError:
                    pass
        return normalize_payload({})

    def save(self, data):
        data = normalize_payload(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix="settings-", suffix=".tmp", delete=False) as f:
                tmp = Path(f.name)
                json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
