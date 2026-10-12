# Question Layer

Use this file only to render unresolved decisions defined by `CALLING_SPEC.md`. It does not classify operations, define routes, or change state transitions.

## Human Mode

When material decisions are missing, show one complete production recommendation and `style_candidates`: three eligible style candidates containing one recommended candidate and two visual alternatives. Candidate selection is deterministic and never random.

```markdown
我建议按下面的配置制作，确认后开始生成：

- 页数/时长：[exact page count] 页，约 [minutes] 分钟
- 交付：[deliverable]
- 路线：[route_id and label]
- 推荐风格 ID / recommended_style_id：[exact stable style ID]
- 内容处理：[rewrite boundary]
- 演讲备注：[yes/no]
- 动效配置：[profile_id / choreography_mode / subtle|dynamic|reduced-motion / grouped in-slide intent / playback targets / verification_required / advance]
- 图片配置：[authorized source images / product screenshots / native PPT / generated visuals / none；推荐媒体槽数量；模板媒体质感参考；缺图时 visual_intent_only；可选 IP/角色或 none；全部 inherit_ppt_style]
- 视频配置：[none, or delivery / playback / audio / loop / poster / fallback]

### 推荐风格
- style_id / name / style category / visual traits / fit evidence / Preview asset
![推荐风格预览]([preview asset])

### 视觉备选 1
- style_id / name / style category / visual traits / fit evidence / Preview asset
![备选风格预览 1]([preview asset])

### 视觉备选 2
- style_id / name / style category / visual traits / fit evidence / Preview asset
![备选风格预览 2]([preview asset])

推荐依据：[one evidence-based sentence]
已知风险：[one concrete risk or none]

请回复准确的 style_id 或风格名称并确认其他配置；不要回复裸字母。
```

Rules:

- Do not hide alternatives in a file while asking the user to choose them.
- Display all three Preview asset images inline whenever the channel supports local images or URLs. A style ID without a visible preview and plain-language description is not an eligible candidate.
- Validate the complete candidate object with `scripts/validate_runtime_payload.py --kind style_selection` before showing it.
- Label each candidate with its exact `style_id`; never use A/B/C as the confirmation value.
- A confirmation applies only to the immediately preceding complete recommendation.
- If the user changes one field, preserve all other confirmed fields and present the updated complete configuration once.
- If all required fields were already explicit and the user authorized direct generation, record confirmation without another question.
- Do not offer an external image skin or painting style after the PPT style candidates. The PPT style remains authoritative. When an IP or custom character is proposed, show its exact identity/form as a baseline preview already transformed into the selected PPT style and ask only whether to use that character.

## Agent Mode

Return a result conforming to `contracts/result.schema.json`:

```json
{
  "protocol_version": "1.1",
  "request_id": "request-123",
  "run_id": "run-123",
  "operation": "deck.create",
  "status": "needs_input",
  "resolved_decisions": {},
  "unresolved_fields": ["page_count", "style_id"],
  "proposed_decisions": {
    "page_count": 6,
    "recommended_style_id": "ref-23-black-orange-auto-marketing-strategy",
    "style_candidates": {
      "protocol_version": "1.1",
      "selection_method": "deterministic_fit_diversity_v1",
      "recommended_style_id": "ref-23-black-orange-auto-marketing-strategy",
      "recent_style_ids": ["ref-16-black-ai-collaboration-editorial"],
      "rejected_style_ids": [],
      "candidates": [
        {
          "rank": 1,
          "style_id": "ref-23-black-orange-auto-marketing-strategy",
          "style_name": "Black Orange Strategy Report",
          "style_category": "premium strategy report",
          "visual_family": "warm-dark-modular-report",
          "fit_score": 14,
          "repeat_penalty": 0,
          "effective_score": 14,
          "fit_evidence": "Complete process, compare, data, and body roles.",
          "visual_traits": ["charcoal canvas", "warm orange accents", "modular cards"],
          "preview_asset": "assets/style-library/style-packs/ref-23-black-orange-auto-marketing-strategy/contact-sheet.png",
          "preview_available": true,
          "recommended": true
        },
        {
          "rank": 2,
          "style_id": "ref-18-soft-editorial-muse-template",
          "style_name": "Soft Editorial Muse Template",
          "style_category": "soft editorial",
          "visual_family": "soft-neutral-editorial-collage",
          "fit_score": 13,
          "repeat_penalty": 0,
          "effective_score": 13,
          "fit_evidence": "A visibly lighter editorial alternative.",
          "visual_traits": ["soft neutral palette", "airy spacing", "serif accents"],
          "preview_asset": "assets/style-library/style-packs/ref-18-soft-editorial-muse-template/contact-sheet.png",
          "preview_available": true,
          "recommended": false
        },
        {
          "rank": 3,
          "style_id": "ref-20-black-blue-saas-proposal",
          "style_name": "Black Blue SaaS Proposal",
          "style_category": "dense SaaS proposal",
          "visual_family": "cool-dark-saas-data",
          "fit_score": 13,
          "repeat_penalty": 0,
          "effective_score": 13,
          "fit_evidence": "A cool data-led workflow alternative.",
          "visual_traits": ["black-blue gradient", "compact data cards", "technical labels"],
          "preview_asset": "assets/style-library/style-packs/ref-20-black-blue-saas-proposal/contact-sheet.png",
          "preview_available": true,
          "recommended": false
        }
      ]
    }
  },
  "artifacts": [],
  "verification": [],
  "warnings": [],
  "error": null,
  "next_action": "Parent Agent obtains confirmation or supplies authorized defaults."
}
```

The child Agent never asks the end user directly. The parent Agent resumes with the same `request_id` and `run_id`.

## Material Decisions

For deck production, unresolved means any missing or conflicting value among:

- exact page count;
- deliverable;
- route ID;
- style ID, `preserve_existing`, or confirmed DashiAI theme;
- rewrite boundary;
- speaker-notes decision.
- when motion is requested: profile ID, choreography mode, motion intensity, grouped in-slide intent, playback targets, `verification_required`, advance mode, semantic checkpoints, and reduced-motion fallback;
- when richer visuals are requested: authorized source images first, planned media-slot count, generated-visual fallback, and attribution policy;
- when IP or a custom character is proposed: exact character/form, a baseline preview in the selected PPT style, and explicit use approval; never infer approval from the style choice;
- when video is requested: delivery, playback, audio, loop, poster, and fallback policy.

Audience and occasion are required only when they materially affect story or style and cannot be derived from explicit source context. Record any derivation as proposed until confirmation.
