# dataman

AI training dataset management CLI + Web UI for on-prem GPU servers.

---

## Dataset 標準操作流程

> 所有對 dataset 的操作都必須在完成後 register 新版本，確保版本可追蹤、可還原。

### 新增 dataset

```bash
# 1. 把資料放到 NFS
cp -r /your/data /storage/Internal_NAS/dataset/NEW_DATASET

# 2. Register
dataman register \
  --path /storage/Internal_NAS/dataset/NEW_DATASET \
  --name new_dataset \
  --version 1.0 \
  --repo-path ~/Code/dataman-registry
```

### 修改 dataset（增加/刪除/修改檔案）

```bash
# 1. 確認舊版本已經 register（重要！）
dataman list --repo-path ~/Code/dataman-registry

# 2. 直接在 NFS 上修改資料
# 增加檔案：cp new_files/ /storage/Internal_NAS/dataset/BONES/
# 刪除檔案：rm /storage/Internal_NAS/dataset/BONES/bad_file.jpg

# 3. Register 新版本（版本號 +1）
dataman register \
  --path /storage/Internal_NAS/dataset/BONES \
  --name bones \
  --version 2.0 \
  --repo-path ~/Code/dataman-registry
```

### 刪除 dataset

dataman 不支援刪除（保留歷史記錄）。如果不想在 Web UI 顯示，直接不 register 新版本即可。真正要清除需手動刪除 git tag 和 NFS 資料。

### 注意事項

- 名稱只能用**小寫英文、數字、底線**（例如 `bones`、`animate_pose`）
- 每次修改資料後**一定要 register 新版本**，否則舊版本無法還原
- 不要在同一個版本號上重複 register（用新版本號）
- `temp`、`testcase`、`tmp` 等暫時性資料夾不需要 register

## 架構

```
NFS                              Server                        GitHub
───────────────────              ──────────────────            ──────────────────────────────
/storage/Internal_NAS/           dataman register  ──────►     hank-intelligarts/dataman-registry
  dataset/BONES/                 dataman serve                   ├── bones.dvc
    ├── metadata.json            (Web UI :8000)                  ├── animate_pose.dvc
    ├── manifest.txt                                             └── git tags (版本快照)
    └── A0001.png ...
  dataset/animate_pose/
  dataset/...
```

## 兩個 GitHub Repo 的用途

| Repo | 內容 | 誰更新 |
|---|---|---|
| `hank-intelligarts/dataman` | CLI 工具 source code | 開發者（你）|
| `hank-intelligarts/dataman-registry` | `.dvc` 追蹤檔 + git tag | 每次 `dataman register` 自動 push |

**metadata.json は NFS 上**（不在 GitHub）：

```
/storage/Internal_NAS/dataset/BONES/
├── metadata.json    ← 品質分數、檔案數、registered_by 等
├── manifest.txt     ← 每個檔案的 SHA256
└── A0001.png ...    ← 實際資料
```

---

## 一、Server 端設定（管理者，第一次）

### 1. 安裝 dataman

```bash
mkdir ~/Code/dataman-workspace
cd ~/Code/dataman-workspace
pyenv local 3.11.9
python -m venv venv
source venv/bin/activate

pip install dvc
pip install git+https://github.com/hank-intelligarts/dataman.git
```

### 2. Clone registry repo

```bash
cd ~/Code
git clone git@github.com:hank-intelligarts/dataman-registry.git
```

### 3. 設定 NFS config

```bash
dataman config init
```

輸入：
- NFS remote name: `internal-nas`
- DVC cache path: `/storage/Internal_NAS/dvc-remote`
- Dataset path: `/storage/Internal_NAS/dataset`
- Default remote: `internal-nas`
- Dataset name: Enter 跳過

---

## 二、Server 端日常操作（管理者）

### 新增 dataset

```bash
dataman register \
  --path /storage/Internal_NAS/dataset/BONES \
  --name bones \
  --version 1.0 \
  --repo-path ~/Code/dataman-registry
```

名稱規則：只能用小寫英文、數字、底線（例如 `bones`、`animate_pose`）。

### 更新 dataset（新版本）

```bash
dataman register \
  --path /storage/Internal_NAS/dataset/BONES \
  --name bones \
  --version 2.0 \
  --repo-path ~/Code/dataman-registry
```

### 啟動 Web UI

```bash
dataman serve --repo-path ~/Code/dataman-registry --port 8000
```

---

## 三、Data Scientist Onboarding

### 方式 1 — 只看資料（Web UI，不需安裝任何東西）

直接用瀏覽器開：

```
http://192.168.51.48:8000
```

可以看到：
- 所有 dataset 列表與版本
- 每個 dataset 的檔案數、大小、品質分數
- Quality Issues 詳細列表

### 方式 2 — 需要把資料抓到本機訓練（CLI）

#### Step 1 — 安裝（每台機器做一次）

```bash
pip install git+https://github.com/hank-intelligarts/dataman.git
```

#### Step 2 — Clone registry（每台機器做一次）

```bash
git clone git@github.com:hank-intelligarts/dataman-registry.git ~/dataman-registry
```

#### Step 3 — 設定 NFS config（每台機器做一次）

```bash
dataman config init
```

輸入：
- NFS remote name: `internal-nas`
- DVC cache path: `/storage/Internal_NAS/dvc-remote`
- Dataset path: `/storage/Internal_NAS/dataset`
- Default remote: `internal-nas`
- Dataset name: Enter 跳過

#### Step 4 — 看有哪些 dataset

```bash
dataman list --repo-path ~/dataman-registry
```

輸出範例：
```
dataset/bones/v1.0
dataset/animate_pose/v1.0
```

#### Step 5 — 把 dataset 抓到本機

```bash
dataman pull dataset/bones/v1.0 --repo-path ~/dataman-registry
```

資料會出現在目前目錄下。

#### Step 6 — 用自己的訓練程式訓練

`train.py` 是你自己的訓練程式，dataman 只負責提供資料。記錄用了哪個版本：

```python
# 在你的 train.py 或 config.yaml 裡記錄
DATASET_SNAPSHOT = "dataset/bones/v1.0"
```

```bash
python train.py --data ./BONES
```

#### 更新到新版本

```bash
git pull                                    # 拿到最新的 registry
dataman pull dataset/bones/v2.0 --repo-path ~/dataman-registry
python train.py --data ./BONES
```

---

## 品質掃描說明

`dataman register` 時自動掃描，結果顯示在 Web UI 的 Quality Issues 區塊。

| Kind | 說明 | 判斷方式 |
|---|---|---|
| `duplicate` | 兩個檔案內容完全相同 | SHA256 hash 相同 |
| `corrupt` | 檔案損壞無法開啟 | PIL/cv2 無法開啟 |
| `resolution_anomaly` | 解析度異常 | 圖片/影片尺寸 < 32px 或 > 16384px |
| `unsupported_format` | 不支援的檔案格式 | 副檔名不在允許清單內 |

允許的格式：`.jpg` `.jpeg` `.png` `.mp4` `.avi` `.mov`

掃描結果不會阻止 register，只是記錄供參考。

---

## Config 格式參考

`~/.dataman/config.toml`（每台機器各自設定，不 commit 到 GitHub）：

```toml
[nfs]
default = "internal-nas"

[nfs.remotes.internal-nas]
cache = "/storage/Internal_NAS/dvc-remote"
datasets = "/storage/Internal_NAS/dataset"
```
