# Nexus Dataset

Working directory for the documents Nexus will eventually read. Nothing is
committed here yet — real files are added later, with permission.

## Layout

```
dataset/
├── university/            # documents that define the rules
│   ├── requirements/       # mandatory structure, sections, word counts…
│   ├── guidelines/         # writing/style guides, assessment criteria
│   └── templates/          # official templates and formatting samples
│
└── student/               # documents the assistant checks against those rules
    ├── research/           # research papers, proposals, reports
    └── theses/             # bachelor/master theses
```

## University vs student documents

- **University documents** are the reference: what a submission must contain.
- **Student documents** are the work being checked: what the student actually wrote.

The assistant compares the two, so both sides need to stay clearly separated.

## Formats to support later

`.pdf`, `.docx`, `.doc`, `.txt`, `.md` — matching the accepted types in the
frontend upload component.

## Ground rules

- Add only documents you are allowed to use.
- Do **not** commit private, confidential or copyrighted university material
  unless you have explicit permission.
- Keep sample files small and anonymized when possible.
- Large files belong outside Git (or in Git LFS later); commit placeholders here.
