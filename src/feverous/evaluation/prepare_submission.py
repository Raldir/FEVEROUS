import jsonlines
import argparse




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str)
    args = parser.parse_args()

    predictions = []
    with jsonlines.open(args.input_file) as f:
        for i,line in enumerate(f.iter()):
            if i  == 0 :
                continue
            curr_l = {}
            # curr_l['id'] = line['id']
            curr_l['predicted_label'] = line['predicted_label']
            curr_l['predicted_evidence'] = [[el.split('_')[0], el.split('_')[1] if 'table_caption' not in el and 'header_cell' not in el else '_'.join(el.split('_')[1:3]), '_'.join(el.split('_')[2:]) if 'table_caption' not in el and 'header_cell' not in el else '_'.join(el.split('_')[3:])] for el in  line['predicted_evidence']]
            predictions.append(curr_l)


    with jsonlines.open('{}.jsonl'.format(args.input_file.split('.jsonl')[0] + '.submission'), 'w') as f:
        for ele in predictions:
            f.write(ele)
