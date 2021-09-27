import os
import sys

rule all:
    input: "data/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl"


PYTHON_EXE = "python"

venv_activation_file = os.path.join(os.path.dirname(sys.executable), 'activate')

if sys.prefix != sys.base_prefix and os.path.exists(venv_activation_file) and '--use-conda' not in sys.argv:
    # hack to support using virtualenv on cluster
    # if the current default python is in a virtualenv and conda was not specified
    # then also activate this virtualenv for subsequent python steps
    PYTHON_EXE = f'source {venv_activation_file}; python'

# default memory and time limits for cluster jobs (only applicable if submitting to a compute cluster)
MAX_TIME = 24 * 60 * 60
DEFAULT_MEMORY_MB = 32 * 1000
DEFAULT_GPUS = 1


rule download_cell_extractor_model:
    output: "models/feverous_cell_extractor.zip"
    params:
        file_id=lambda w: "1Zu3RUFzThPpsSkBhlYc0CBoRpIRxauGR"
    shell: "gdown https://drive.google.com/uc?id={params.file_id} -O {output}"


rule download_verdict_predictor_model:
    output: "models/feverous_verdict_predictor.zip"
    params:
        file_id=lambda w: "1SoxeTDp2NETbZdMpEle_QO8Cw0oxgUbV"
    shell: "gdown https://drive.google.com/uc?id={params.file_id} -O {output}"


rule extract_cell_extractor:
    input: rules.download_cell_extractor_model.output
    output: "models/feverous_cell_extractor/pytorch_model.bin"
    shell: "cd $(dirname {input}); unzip $(basename {input})"


rule extract_verdict_predictor:
    input: rules.download_verdict_predictor_model.output
    output: "models/feverous_verdict_predictor/pytorch_model.bin"
    shell: "cd $(dirname {input}); unzip $(basename {input})"


rule download_spacy_model:
    log: "logs/download_spacy_model.log"
    shell: PYTHON_EXE + " -m spacy download en_core_web_sm > {log}"


rule download_data:
    output: dev="data/dev.jsonl",
        train="data/train.jsonl",
        wiki="data/feverous_wikiv1.db"
    resources:
        time_limit=MAX_TIME,
        mem_mb=8000,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: "bash scripts/download_data.sh"


rule build_db:
    input: rules.download_data.output.wiki
    output: "data/feverous-wiki-docs.db"
    resources:
        time_limit=MAX_TIME,
        mem_mb=DEFAULT_MEMORY_MB,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: PYTHON_EXE + " src/feverous/baseline/retriever/build_db.py --db_path {input} --save_path {output}"


rule build_tfidf:
    input: rules.build_db.output
    output: "data/index/feverous-wiki-docs-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz"
    resources:
        time_limit=MAX_TIME,
        mem_mb=DEFAULT_MEMORY_MB,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: PYTHON_EXE + " src/feverous/baseline/retriever/build_tfidf.py --db_path {input} --out_dir {output}"


rule extract_k_docs:
    input: index=rules.build_tfidf.output,
        db=rules.build_db.output
    output: "data/dev.pages.p5.jsonl"
    resources:
        time_limit=MAX_TIME,
        mem_mb=DEFAULT_MEMORY_MB,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: PYTHON_EXE + " src/feverous/baseline/retriever/document_entity_tfidf_ir.py  --model '{input.index}' --db {input.db} --count 5 --split dev --data_path data/"


rule extract_sentences:
    input: docs=rules.extract_k_docs.output,
        db=rules.build_db.output
    output: "data/dev.sentences.not_precomputed.p5.s5.jsonl"
    resources:
        time_limit=MAX_TIME,
        mem_mb=DEFAULT_MEMORY_MB,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: PYTHON_EXE + " src/feverous/baseline/retriever/sentence_tfidf_drqa.py --db {input.db} --split dev --max_page 5 --max_sent 5 --use_precomputed false --data_path data/"


rule extract_tables:
    input: docs=rules.extract_k_docs.output,
        db=rules.build_db.output
    output: "data/dev.tables.not_precomputed.p5.t3.jsonl"
    resources:
        time_limit=MAX_TIME,
        mem_mb=DEFAULT_MEMORY_MB,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: PYTHON_EXE + " src/feverous/baseline/retriever/table_tfidf_drqa.py --db {input.db} --split dev --max_page 5 --max_tabs 3 --use_precomputed false --data_path data/"


rule combine_tables_and_sentences:
    input: rules.extract_sentences.output,
        rules.extract_tables.output
    output: "data/dev.combined.not_precomputed.p5.s5.t3.jsonl"
    resources:
        time_limit=MAX_TIME,
        mem_mb=DEFAULT_MEMORY_MB,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: PYTHON_EXE + " src/feverous/baseline/retriever/combine_retrieval.py --data_path data --max_page 5 --max_sent 5 --max_tabs 3 --split dev"


rule extract_table_cells:
    input: data=rules.combine_tables_and_sentences.output,
        model=rules.extract_cell_extractor.output,
        db=rules.download_data.output.wiki
    output: "data/dev.combined.not_precomputed.p5.s5.t3.cells.jsonl"
    params:
        model=lambda w, input: os.path.dirname(input.model[0])
    resources:
        time_limit=MAX_TIME,
        mem_mb=DEFAULT_MEMORY_MB,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: PYTHON_EXE + " src/feverous/baseline/retriever/predict_cells_from_table.py --input_path {input.data} --max_sent 5 --wiki_path {input.db} --model_path {params.model}"


rule evaluate_predictor:
    input: data=rules.extract_table_cells.output,
        model=rules.extract_verdict_predictor.output,
        db=rules.download_data.output.wiki
    output: "data/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl"
    params:
        model=lambda w, input: os.path.dirname(input.model[0])
    resources:
        time_limit=MAX_TIME,
        mem_mb=DEFAULT_MEMORY_MB,
        gpus=DEFAULT_GPUS,
        log_dir="logs"
    shell: PYTHON_EXE + " src/feverous/baseline/predictor/evaluate_verdict_predictor.py --input_path {input.data} --wiki_path {input.db} --model_path {input.model}"
