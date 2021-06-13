mkdir -p data
mkdir -p models
wget -O data/train.jsonl https://s3-eu-west-1.amazonaws.com/fever.public/feverous/train.jsonl
wget -O data/dev.jsonl https://s3-eu-west-1.amazonaws.com/fever.public/feverous/dev.jsonl
# wget -O data/test.jsonl https://s3-eu-west-1.amazonaws.com/fever.public/shared_task_test.jsonl
wget -O data/feverous-wiki-pages-db.zip https://s3-eu-west-1.amazonaws.com/fever.public/feverous/feverous-wiki-pages-db.zip
unzip data/feverous-wiki-pages-db.zip
