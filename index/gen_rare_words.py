import pickle
import argparse
from pathlib import Path
import pandas as pd

def get_rare_words(low_idf, high_idf, idf_file_path):
    df = pd.read_csv(idf_file_path)
    df = df[df["idf"]>=low_idf]
    df = df[df["idf"]<=high_idf]
    df = df[["stem","most_freq_term"]]
    #rare_words: dict: <stem>: <list of most_freq_word>
    #though list contains only one word i.e. most occuring word for the stem
    rare_words = df.set_index('stem').T.to_dict('list')
    return rare_words

if __name__=="__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--idf_path", type=str)
    parser.add_argument("--rw_path", type=str, help="path to store rare_word")
    parser.add_argument("--high_idf", type=float, help="highest IDF value we will take into account for rare word" )
    parser.add_argument("--low_idf", type=float, help="low idf value that we will consider for rare word")

    args = parser.parse_args()

    my_file = Path(args.rw_path)
    if my_file.is_file():
        #ids already exists
        pass

    rare_words = get_rare_words(args.low_idf, args.high_idf, args.idf_path)
    #Dump the high rare_words
    with open(args.rw_path,"wb") as file:
        pickle.dump(rare_words,file)