# 自校验清单

## A. 稳定性（不同角度 / 光照）
- [ ] 正常正脸（室内均匀光）可输出可用结果。
- [ ] 侧脸 > 35° 时，系统可给出失败提示（不 silent fail）。
- [ ] 强逆光场景下，若检测失败能返回明确错误。

## B. 失败案例处理
- [ ] source 无人脸：报错 `Source image must contain exactly 1 face...`
- [ ] target 多人脸：报错 `Target frame must contain exactly 1 face...`
- [ ] target 视频全帧失败：报错 `Failed on all video frames...`

## C. 风控策略可绕过性检查
- [ ] 非白名单目录输入会被拒绝。
- [ ] 非固定文件名会被拒绝。
- [ ] 输出必带可见水印。
- [ ] 输出必生成 sidecar JSON（含输入哈希与时间戳）。

## D. 结论
当前 Demo 已满足“受控演示”目标，但风控规则（公众人物识别）仍为简化策略，生产需接入更强模型与人工复核链路。
