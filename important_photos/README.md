# Budget Darpan — Diagram and Presentation Assets

This folder contains editable PlantUML sources for the system report, pitch deck, technical presentation, and viva. The `.puml` files are the source of truth; export them to SVG for slides and PNG only when a raster image is required.

## Diagram index

| File | Best use |
|---|---|
| `01_system_context_and_use_cases.puml` | Problem, users, and product scope |
| `02_overall_system_architecture.puml` | Main technical architecture slide |
| `03_end_to_end_system_flowchart.puml` | Complete citizen journey |
| `04_development_methodology.puml` | Development methodology/report |
| `05_domain_class_diagram.puml` | Database/domain design |
| `06_rag_pipeline.puml` | RAG and bilingual AI explanation |
| `07_investigator_query_sequence.puml` | Runtime AI question flow |
| `08_document_ingestion_pipeline.puml` | PDF extraction and OCR flow |
| `09_mock_identity_verification.puml` | Demo Nagarik-style verification |
| `10_anomaly_detection_pipeline.puml` | Explainable anomaly system |
| `11_deployment_architecture.puml` | Local demo and cloud roadmap |
| `12_testing_and_evaluation_strategy.puml` | Testing, F1, retrieval metrics |
| `13_data_provenance_and_safety.puml` | Official vs synthetic trust boundary |

`_theme.puml` contains the common visual style and is included by every diagram.

## VS Code shortcuts

These instructions are for the **PlantUML extension by jebbs**, which is installed on this machine.

1. Open any `.puml` file.
2. Place the cursor anywhere inside the diagram.
3. Press **Alt + D** on Windows/Linux to preview. On macOS use **Option + D**.
4. Press **Ctrl + Shift + P** and run **PlantUML: Export Current Diagram**.
5. Select **SVG** for PowerPoint/Canva/Figma because it stays sharp at any size.

Other useful commands from `Ctrl + Shift + P`:

- `PlantUML: Export Current Diagram`
- `PlantUML: Export Current File Diagrams`
- `PlantUML: Export Workspace Diagrams`

The extension also supports **Ctrl + Shift + O** to list diagrams in the current file.

## Command-line validation and export

From the repository root in PowerShell:

```powershell
$plantUmlJar = "$env:USERPROFILE\.vscode\extensions\jebbs.plantuml-2.18.1\plantuml.jar"

Get-ChildItem .\important_photos\*.puml |
  Where-Object { $_.Name -ne '_theme.puml' } |
  ForEach-Object { java -jar $plantUmlJar -checkonly $_.FullName }
```

Export all diagrams to SVG:

```powershell
$plantUmlJar = "$env:USERPROFILE\.vscode\extensions\jebbs.plantuml-2.18.1\plantuml.jar"

Get-ChildItem .\important_photos\*.puml |
  Where-Object { $_.Name -ne '_theme.puml' } |
  ForEach-Object { java -jar $plantUmlJar -tsvg $_.FullName }
```

For PNG, replace `-tsvg` with `-tpng`.

If the extension version changes, locate the current JAR with:

```powershell
Get-ChildItem "$env:USERPROFILE\.vscode\extensions" -Recurse -Filter plantuml.jar
```

## Presentation recommendations

- Use diagrams 01, 02, 03, 06, 09, 10, and 12 in the main pitch.
- Put diagrams 04, 05, 08, 11, and 13 in the technical appendix/report.
- Do not place the entire class diagram on a small slide; crop or zoom it during the technical explanation.
- Keep the trust labels visible: `official`, `reconstructed_from_official_sources`, `curated_demo`, and `synthetic_demo`.
- Always retain the statement: **Budget Darpan does not accuse. It identifies patterns and evidence that may require further review.**

## Test-command locations

Run the real project checks from these locations:

```powershell
# Entire Python repository, including mock identity integration
cd D:\Codefest\codefest-2026-Die_Vordenker
backend\.venv\Scripts\python.exe -m pytest -q

# Django checks and migrations
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest -q

# Frontend
cd ..\frontend
npm.cmd run lint
npm.cmd run test -- --run
npm.cmd run build

# Private multilingual evaluation (intentionally Git-ignored)
cd ..
backend\.venv\Scripts\python.exe reports_private\evaluate_system.py
```

Latest verified results are documented privately in `reports_private/AI_EVALUATION_REPORT.md`.
