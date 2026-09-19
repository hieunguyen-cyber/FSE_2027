# Dữ liệu và artefact không nằm trong Git

GitHub chỉ chứa source code, test và cấu hình. Các file dưới đây bị loại khỏi
`main` vì kích thước lớn, giấy phép upstream hoặc vì là checkpoint/artefact sinh
ra trong quá trình chạy. Hãy tải thủ công vào đúng đường dẫn trước khi chạy
reproduction.

## 1. BigVul cleaned function-level dataset — bắt buộc

- Nguồn chính thức: [Google Drive cleaned release](https://drive.google.com/file/d/1-0VhnHBp9IGh90s2wCNjeCMuy70HPl8X/view?usp=sharing)
- Tên file tải về: `MSR_data_cleaned.zip`
- Đặt tại: `/Users/hieunguyen/FSE_2027/MSR_data_cleaned.zip`
- Giải nén CSV vào: `/Users/hieunguyen/FSE_2027/vendor/bigvul/MSR_data_cleaned.csv`
- SHA-256 archive: `be96d4133fe4e75a2c5dd3f36eae22939612083cd1f7bcaa3bb5ce782316e0f2`
- Kích thước CSV sau giải nén: khoảng 10.8 GB

Sau khi tải và giải nén:

```bash
mkdir -p vendor/bigvul
unzip -o MSR_data_cleaned.zip -d vendor/bigvul
shasum -a 256 MSR_data_cleaned.zip
python3 -m mira_mas.cli --curate-bigvul \
  --input-csv vendor/bigvul/MSR_data_cleaned.csv \
  --output artifacts/curated_v2/defect_cards.jsonl
python3 -m mira_mas.cli --build-split \
  --cards artifacts/curated_v2/defect_cards.jsonl \
  --split-manifest artifacts/curated_v2/split_manifest.json
```

## 2. BigVul raw metadata — tuỳ chọn, chỉ để provenance

- Repository: [MSR_20_Code_Vulnerability_CSV_Dataset](https://github.com/ZeoVan/MSR_20_Code_Vulnerability_CSV_Dataset)
- File: `all_c_cpp_release2.0.csv`
- Đặt tại: `vendor/bigvul/all_c_cpp_release2.0.csv`

File raw này không đủ hai cột `func_before`/`func_after`, vì vậy không dùng trực
tiếp để tạo `DefectCard`. Pipeline cần cleaned release ở mục 1.

## 3. CodeReviewer dataset/checkpoint — chỉ cần khi chạy native model

- Dataset và artefact: [Zenodo record 6900648](https://zenodo.org/records/6900648)
- Checkpoint: [microsoft/codereviewer trên Hugging Face](https://huggingface.co/microsoft/codereviewer)
- Source: clone `microsoft/CodeBERT`, sau đó giữ thư mục `CodeReviewer/` tại:
  `vendor/CodeBERT/CodeReviewer/`

API track của dự án không cần checkpoint này; nó dùng OpenRouter backend và chỉ
cần dữ liệu BigVul.

## 4. T5 code-review-automation dataset/checkpoint — chỉ cần khi chạy T5 native

- Replication package: [Zenodo record 5387856](https://zenodo.org/records/5387856)
- Các archive cần thiết trong record: `datasets.zip`, `models.zip`,
  `tokenizer.zip`, `generate_predictions.zip`.
- Source repository: [RosaliaTufano/code_review_automation](https://github.com/RosaliaTufano/code_review_automation)
- Đặt source tại: `vendor/code_review_automation/`

MIRA-MAS API evaluation không phụ thuộc T5 checkpoint. Các file này chỉ phục vụ
đối chiếu/reproduce baseline native.

## 5. CodeAgent full source archive — tuỳ chọn

- Full source: [Zenodo record 11666403](https://zenodo.org/records/11666403)
- Source archive: [CodeAgent.zip](https://zenodo.org/records/11666403/files/CodeAgent.zip?download=1)
- MD5 archive: `e87438952d574dae790e558b44ca4137`
- Source repository snapshot: [Code4Agent/codeagent](https://github.com/Code4Agent/codeagent)
- Đặt source native tại: `vendor/codeagent/`

API track hiện tại không cần archive này. Nếu chạy native reproduction, cần tải
đầy đủ archive thay vì chỉ dùng GitHub snapshot.

## 6. File sinh ra khi chạy — không tải từ upstream

Các thư mục sau được sinh cục bộ và không commit:

- `artifacts/`: ledger, audit, summaries, cost meter và kết quả evaluation;
- `artifacts/curated_v2/defect_cards.jsonl`: sinh từ BigVul cleaned CSV;
- `artifacts/curated_v2/split_manifest.json`: sinh từ curated cards;
- `vendor/`: các snapshot/upstream checkout lớn.

Kiểm tra nhanh dữ liệu trước khi chạy:

```bash
python3 -m mira_mas.cli --preflight \
  --cards artifacts/curated_v2/defect_cards.jsonl \
  --split-manifest artifacts/curated_v2/split_manifest.json
```

Không commit `.env` hoặc API key. Chỉ sao chép `.env.example` thành `.env` và
điền key cục bộ.
