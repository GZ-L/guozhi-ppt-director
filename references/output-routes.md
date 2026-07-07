# Output Routes

Use this file before choosing a production path.

## Route A: Editable PPTX

Choose this route when the user needs:

- School assignment, company report, client proposal, pitch deck, class presentation, or team collaboration.
- A `.pptx` file with editable text, shapes, charts, and layout.
- Compatibility with PowerPoint, Keynote import, WPS, or Feishu import.

Recommended adapter:

- PPT Master or another true PPTX generator.

Required handoff package:

- `deck-brief.md`
- `outline.md`
- `style-board.md`
- source links or evidence notes

Delivery should include:

- `.pptx`
- optional `.pdf`
- `qa-report.md`

## Route B: Frontend Slides

Choose this route when the user needs:

- Web slides, animated presentation, product-launch style, keynote feeling, motion graphics, screen recording, short-video repurposing, or interactive demo.
- HTML/CSS/JS control over transitions, layout, and responsive scenes.

Recommended adapter:

- Frontend Slides or another HTML slide generator.

Required handoff package:

- `deck-brief.md`
- `outline.md`
- `style-board.md`
- motion notes per page

Delivery should include:

- `index.html` or project folder
- preview URL or local run command
- optional exported images/video
- `qa-report.md`

## Route C: Dual Version

Choose this route when the user needs both:

- A formal editable PPTX for submission.
- A high-aesthetic animated version for video, social media, or live presentation.

Recommended sequence:

1. Build `deck-brief.md`, `outline.md`, and `style-board.md`.
2. Produce a visual/motion direction with Frontend Slides.
3. Convert or recreate the stable pages into editable PPTX with PPT Master.
4. QA both versions separately.

Use dual version as the default when the user says "both", "PPT + video", "can submit and can post", "advanced version", or "make it cool and editable".
