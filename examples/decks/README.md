# Example Decks

这里保存 `guozhi-ppt-director` 实际运行产生并经用户授权上传的案例。每个目录包含可编辑 `deck.pptx` 和 GitHub 可直接显示的 `preview.png`，不包含原始文章、用户 PDF 或第三方风格参考图。

## 案例清单

| 案例 | 页数 | 演讲备注 | 路线或风格证据 | PPTX | 预览 |
| --- | ---: | ---: | --- | --- | --- |
| AI 知识库搭建方法 | 5 | 5 | 动漫扁平插画风 | [下载](ai-knowledge-flat-illustration/deck.pptx) | [查看](ai-knowledge-flat-illustration/preview.png) |
| Life Design Prompt | 6 | 6 | `ref-16-black-ai-collaboration-editorial` | [下载](life-design-ref16/deck.pptx) | [查看](life-design-ref16/preview.png) |
| Identity Skill | 6 | 6 | `dashiai` | [下载](identity-skill-dashiai/deck.pptx) | [查看](identity-skill-dashiai/preview.png) |

## 验证记录

三份 PPTX 均在上传前执行：

```bash
unzip -t deck.pptx
python3 slides_test.py deck.pptx
```

检查结果：压缩包完整，无幻灯片画布溢出。页数和备注数量通过 PPTX 包结构复核；预览图由最终 PPTX 渲染生成或与最终成品逐页对应。

## 使用边界

- 案例用于展示实际输出和验证方式，不是可复用模板许可证。
- 不要从案例中提取品牌、人物、插画或内容后重新分发。
- 测试新版本时可以复用案例请求结构，但应生成新的输出文件，不覆盖这些基线案例。
