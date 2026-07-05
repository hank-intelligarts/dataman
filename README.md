# dataman

AI training dataset management CLI + Web UI for on-prem GPU servers.

## 架構

```
dataman (CLI 工具)          dataman-registry (Git repo)      NFS
──────────────────          ───────────────────────────      ───
dataman register    ──►     .dvc + metadata + git tag   ◄──  /storage/Internal_NAS/dataset/
dataman serve       ──►     Web UI 讀取 git tag
dataman pull        ──►     git checkout + dvc pull from NFS
```

## 安裝

```bash
pip install git+https://github.com/hank-intelligarts/dataman.git
```

## Server 設定（第一次）

```bash
# 1. Clone registry repo
git clone git@github.com:hank-intelligarts/dataman-registry.git
cd dataman-registry

# 2. 設定 NFS config
dataman config init
# NFS remote name:  internal-nas
# DVC cache path:   /storage/Internal_NAS/dvc-remote
# Dataset path:     /storage/Internal_NAS/dataset
# Default remote:   internal-nas
```

## 主要指令

### Register dataset

```bash
dataman register \
  --path /storage/Internal_NAS/dataset/BONES \
  --name bones \
  --version 1.0 \
  --repo-path ~/Code/dataman-registry
```

名稱規則：只能用小寫英文、數字、底線（例如 `bones`、`animate_pose`）。

### 啟動 Web UI

```bash
dataman serve --repo-path ~/Code/dataman-registry --port 8000
```

瀏覽器開 `http://<server-ip>:8000`

### 列出所有 dataset

```bash
dataman list --repo-path ~/Code/dataman-registry
```

### 查看 dataset 資訊

```bash
dataman info --path /storage/Internal_NAS/dataset/BONES
```

### Pull dataset（Data Scientist 用）

```bash
dataman pull dataset/bones/v1.0 --repo-path ~/Code/dataman-registry
```

### 品質掃描

```bash
dataman scan --path /storage/Internal_NAS/dataset/BONES
```

## 品質掃描說明

`dataman register` 時會自動對 dataset 做品質掃描，結果顯示在 Web UI 的 Quality Issues 區塊。

| Kind | 說明 | 判斷方式 |
|---|---|---|
| `duplicate` | 兩個檔案內容完全相同 | SHA256 hash 相同 |
| `corrupt` | 檔案損壞無法開啟 | PIL/cv2 無法開啟 |
| `resolution_anomaly` | 解析度異常 | 圖片/影片尺寸 < 32px 或 > 16384px |
| `unsupported_format` | 不支援的檔案格式 | 副檔名不在允許清單內 |

允許的格式：`.jpg` `.jpeg` `.png` `.mp4` `.avi` `.mov`

掃描結果不會阻止 register，只是記錄在 `metadata.json` 供參考。

## 完整流程

### 管理者（server 上）

```
1. dataman register   ← 新增/更新 dataset
2. dataman serve      ← 啟動 Web UI
```

### Data Scientist（自己的訓練機）

```
1. git clone dataman-registry    ← 第一次
2. dataman config init           ← 第一次設定 NFS
3. dataman list                  ← 看有哪些 dataset
4. dataman pull dataset/bones/v1.0  ← 拿資料到本機
5. python train.py --data ./BONES   ← 訓練
```

### Dataset 有新版本

```bash
# 管理者
dataman register --name bones --version 2.0 ...

# Scientist
dataman pull dataset/bones/v2.0
```

## Config 格式

`~/.dataman/config.toml`（每台機器各自設定，不 commit 到 GitHub）：

```toml
[nfs]
default = "internal-nas"

[nfs.remotes.internal-nas]
cache = "/storage/Internal_NAS/dvc-remote"
datasets = "/storage/Internal_NAS/dataset"
```
