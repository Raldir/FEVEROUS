mkdir -p data
mkdir -p models
wget -O data/train.jsonl https://fever.ai/download/feverous/feverous_train_challenges.jsonl
wget -O data/dev.jsonl https://fever.ai/download/feverous/feverous_dev_challenges.jsonl
wget -O data/test_unlabeled.jsonl https://fever.ai/download/feverous/feverous_test_unlabeled.jsonl
wget -O data/feverous-wiki-pages-db.zip https://fever.ai/download/feverous/feverous-wiki-pages-db.zip
unzip data/feverous-wiki-pages-db.zip -d data/feverous_wikiv1.db
