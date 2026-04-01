# Bug 修复记录：`_validate_target` 中 `forbidden_content` 过滤永远无效

## 问题描述

`core/mac/device_detection.py` 中，`_validate_target` 函数负责校验设备是否为可用目标盘，其中包含一段 `forbidden_content` 过滤逻辑，用于拦截 APFS、HFS+ 等 macOS 系统文件系统类型的设备，防止误写入系统盘或重要分区。

然而，该过滤逻辑**从未生效**，任何设备的 `content` 字段都会被当作空字符串处理，导致 APFS 容器盘等高风险设备可能通过校验。

---

## 根本原因

**`_scan_devices` 函数在构建设备字典时，遗漏了 `"content"` 字段的写入。**

`content` 变量在 `_scan_devices` 中被正确读取：

```python
content = disk.get("Content", "")
```

但在最终 `devices.append(...)` 时，该字段**没有被放入字典**：

```python
# 原有代码（有 Bug）
devices.append({
    "id": device_id,
    "device": device_path,
    "size_bytes": size_bytes,
    "internal": internal,
    "removable": removable,
    "mounted": mounted,
    "volumes": volumes,
    "is_system_risk": is_system_risk
    # ← "content" 字段缺失！
})
```

因此，当 `_validate_target` 调用 `device.get("content", "")` 时，始终返回默认值空字符串 `""`，永远不会命中 `forbidden_content` 集合，过滤形同虚设。

---

## 影响范围

- `_validate_target` 中的 `forbidden_content` 过滤完全失效
- `list_available_devices` 返回的设备列表可能包含 APFS 容器盘、HFS+ 盘等不应出现的高风险设备
- 虽然 `is_system_risk` 和 `internal` 字段提供了一定兜底保护，但 `forbidden_content` 作为独立防线的意义完全丧失

---

## 修复方案

在 `_scan_devices` 的 `devices.append(...)` 中补充 `"content"` 字段：

```python
# 修复后代码
devices.append({
    "id": device_id,
    "device": device_path,
    "size_bytes": size_bytes,
    "internal": internal,
    "removable": removable,
    "mounted": mounted,
    "volumes": volumes,
    "is_system_risk": is_system_risk,
    "content": content,  # ← 补充此字段，使 _validate_target 中的 forbidden_content 过滤生效
})
```

`_validate_target` 中的读取逻辑本身无误，无需修改。

---

## 修复文件

- `core/mac/device_detection.py`
  - `_scan_devices`：补充 `"content": content` 字段
  - `_validate_target`：添加注释说明原 Bug 及修复背景

---

## 修复日期

2026-04-01
