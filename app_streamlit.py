#!/usr/bin/env python3
"""Simple Streamlit UI for the controlled face swap demo."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from face_swap_demo import ControlledFaceSwapDemo, FaceSwapError

st.set_page_config(page_title="Controlled Face Swap Demo", layout="centered")
st.title("受控换脸 Demo（含合规与风控）")

st.info(
    "风控提示：仅处理你有权使用的素材；仅白名单目录可处理；输出会强制加水印并写入 sidecar 记录。"
)

whitelist_dir = Path("assets/whitelist")
whitelist_dir.mkdir(parents=True, exist_ok=True)
output_dir = Path("outputs")
output_dir.mkdir(parents=True, exist_ok=True)

source_file = st.file_uploader("上传 source_face.jpg（被替换人脸）", type=["jpg", "jpeg"], key="source")
target_file = st.file_uploader("上传 target_image.jpg 或 target_video.mp4", type=["jpg", "jpeg", "mp4"], key="target")

st.caption("上传后将自动保存到白名单目录固定文件名，以触发风控闸门。")

if st.button("开始生成", type="primary"):
    if source_file is None or target_file is None:
        st.error("请先上传 source 与 target 文件。")
    else:
        source_path = whitelist_dir / "source_face.jpg"
        target_name = "target_video.mp4" if target_file.name.lower().endswith(".mp4") else "target_image.jpg"
        target_path = whitelist_dir / target_name

        with source_path.open("wb") as f:
            f.write(source_file.getbuffer())
        with target_path.open("wb") as f:
            f.write(target_file.getbuffer())

        output_path = output_dir / ("output.mp4" if target_name.endswith(".mp4") else "output.jpg")

        try:
            demo = ControlledFaceSwapDemo(whitelist_dir)
            report = demo.process(source_path, target_path, output_path)
        except FaceSwapError as exc:
            st.error(f"处理失败：{exc}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"系统异常：{exc}")
        else:
            st.success("处理完成！")
            st.json(report)
            if output_path.suffix == ".jpg":
                st.image(str(output_path), caption="输出结果（带居中水印）")
            else:
                st.video(str(output_path))
            sidecar = output_path.with_suffix(output_path.suffix + ".json")
            if sidecar.exists():
                st.download_button(
                    "下载 sidecar JSON",
                    data=sidecar.read_bytes(),
                    file_name=sidecar.name,
                    mime="application/json",
                )

st.markdown("---")
st.caption("运行方式：`streamlit run app_streamlit.py`")
