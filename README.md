# AI 实操题 B3：受控换脸 Demo

> 岗位方向：产品培训生（实现产品）  
> 项目目标：在可运行换脸能力的基础上，落实“合规前置 + 风控限制 + 可追溯”。

## 1. 项目说明
本项目实现了一个**受控换脸 Demo（CLI）**，支持输入 `source_face.jpg` 与 `target_image.jpg / target_video.mp4`，输出 `output.jpg / output.mp4`，并内置多条可验证的防滥用限制。

核心脚本：`face_swap_demo.py`

---

## 2. 合规前置（素材来源与使用权说明）
本仓库内演示素材约束为固定白名单目录 `assets/whitelist/` 下的固定文件名：

- `source_face.jpg`
- `target_image.jpg`
- `target_video.mp4`

当前演示素材统一使用 [Vecteezy](https://www.vecteezy.com/) 获取并授权的图片/视频；本 Demo 将拒绝处理白名单外文件。

> Vecteezy 授权记录模板（建议随仓库保存截图或下载记录）：
> - source 素材：来自 Vecteezy（资源链接：`<填写 URL>`；License：`Free` 或 `Pro`）
> - target image 素材：来自 Vecteezy（资源链接：`<填写 URL>`；License：`Free` 或 `Pro`）
> - target video 素材：来自 Vecteezy（资源链接：`<填写 URL>`；License：`Free` 或 `Pro`）
>
> 说明：
> - 若使用 Vecteezy `Free` 资源，需按平台条款完成署名/归因。
> - 若使用 Vecteezy `Pro` 资源，按对应条款执行（通常可免署名）。
> - 请遵守 Vecteezy 最新《Terms & Licensing Agreement》。

---

## 3. 已实现能力

### 3.1 换脸能力（可运行）
- 输入：
  - `--source assets/whitelist/source_face.jpg`
  - `--target assets/whitelist/target_image.jpg` 或 `assets/whitelist/target_video.mp4`
- 输出：
  - `--output outputs/output.jpg` 或 `outputs/output.mp4`
- 图像融合：使用 OpenCV `seamlessClone` 尽量保持肤色与光照协调（Demo 级）。

### 3.2 失败提示（可读错误）
明确错误信息包括：
- 找不到输入文件
- 输入不在白名单目录
- 文件名不在允许列表
- 检测不到人脸 / 人脸数不是 1
- 视频帧全部处理失败
- 角度/遮挡导致融合失败

---

## 4. 风控与防滥用设计（已实现 ≥2 条）
已实现并可验证：

1. **白名单路径限制**：仅允许 `assets/whitelist` 内文件。  
2. **固定文件名闸门**：只接受 `source_face.jpg`、`target_image.jpg`、`target_video.mp4`。  
3. **疑似公众人物关键词拦截（简化版）**：文件名命中关键词直接拒绝。  
4. **单人脸策略**：source/target 必须且仅能检测到 1 张脸，多人脸拒绝。  
5. **强制可见水印**：输出带 `Demo only / For evaluation`。  
6. **元信息侧车记录**：输出同名 `.json`，记录输入哈希、时间戳、启用风控项。

---

## 5. 环境安装与运行

### 5.1 安装
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2 图像换脸
```bash
python3 face_swap_demo.py \
  --source assets/whitelist/source_face.jpg \
  --target assets/whitelist/target_image.jpg \
  --output outputs/output.jpg
```

### 5.3 视频换脸
```bash
python3 face_swap_demo.py \
  --source assets/whitelist/source_face.jpg \
  --target assets/whitelist/target_video.mp4 \
  --output outputs/output.mp4
```

---

## 6. 项目结构
```text
.
├── face_swap_demo.py
├── requirements.txt
├── README.md
├── AI_USAGE_LOG.md
├── SELF_CHECKLIST.md
├── assets/
│   └── whitelist/
│       ├── source_face.jpg
│       ├── target_image.jpg
│       └── target_video.mp4
├── outputs/
│   ├── output.jpg
│   └── output.jpg.json
└── demo_recording.mp4
```

---

## 7. 取舍与限制
- 人脸检测采用 Haar Cascade，鲁棒性不如深度模型（姿态、遮挡、复杂光照下会失败）。
- “公众人物检测”当前为简化规则（文件名关键词），仅用于展示风控链路，不可用于生产。
- Demo 优先强调“可控可审计”，而不是极致画质。

---

## 8. AI 使用记录与自校验
- AI 使用过程见：`AI_USAGE_LOG.md`
- 自校验清单见：`SELF_CHECKLIST.md`
