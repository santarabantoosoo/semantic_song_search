# -*- coding: utf-8 -*-
"""semantic_song_search.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17IwipreOw_cvu1TsA4WUrfzxTBBHMiVh
"""


from sentence_transformers import SentenceTransformer, util
from datasets import load_dataset
import gradio as gr
import pandas as pd
import torch
import numpy as np


"""### model all mini -- small dataset """

model_all_mini = SentenceTransformer('all-MiniLM-L12-v2')

sds = load_dataset("Santarabantoosoo/small_lyrics_dataset")

sds = pd.DataFrame(sds['train'])
# sds = pd.read_csv("data/small_dataset.csv")

sds.head()

embeddings_sds = model_all_mini.encode(sds['lyrics'])
sds['embeddings'] = list(embeddings_sds)

def relevance_scores(query_embed):
    scores = [cosine_similarity(query_embed, v2) for v2 in sds['embeddings']]
    scores = pd.Series(scores)
    return(scores)


def semantic_search(query_sentence, df = sds, return_top = False):
    query_embed = model_all_mini.encode(query_sentence)
    scores = relevance_scores(query_embed)
    df['scores'] = scores
    sorted_df = df.sort_values(by = 'scores', ascending = False)
    if return_top == False:
        sorted_df['scores'] = round(sorted_df['scores'],3)
        return sorted_df[['title','artist','scores']].head(3)
    else:
        return sorted_df.iloc[0]['lyrics'][:200]
    
def cosine_similarity(v1, v2):
    d = np.dot(v1, v2)
    cos_theta = d / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return(cos_theta)

semantic_search("i'm pleased you are doing well after we left each other")

print(semantic_search("i'm pleased you are doing well after we left each other", return_top = True))

"""### model msmarco-distilbert-base-dot-prod-v3  with hf dataset (with song name)"""

query = ["i'm pleased you are doing well after we left each other"]

# hf_data = pd.read_csv('data/hf_train_with_SName.csv')

hf_data = load_dataset("Santarabantoosoo/hf_song_lyrics_with_names")

hf_data = pd.DataFrame(hf_data['train'])

hf_data['Lyric'] = hf_data['Lyric'].str.replace('\\n', "")

hf_data.head()

model_msmarco_v3 = SentenceTransformer('msmarco-distilbert-base-dot-prod-v3')

query_embedding = model_msmarco_v3.encode(query)

passage_embedding = model_msmarco_v3.encode(hf_data[:1000].Lyric)

corpus_embeddings = torch.from_numpy(passage_embedding).float()#.to('cuda')
corpus_embeddings = util.normalize_embeddings(corpus_embeddings)

# query_embeddings = torch.from_numpy(query_embedding).float().to('cuda')
# query_embeddings = util.normalize_embeddings(query_embeddings)
# hits = util.semantic_search(query_embeddings, corpus_embeddings, score_function=util.dot_score)

# best_match = hits[0][0]['corpus_id']

# hf_data.iloc[best_match, :]

# hf_data.iloc[best_match]['Lyric']

# hf_data.head()

def msmarco_match(query, return_top = True):
    query_embedding = model_msmarco_v3.encode(query)
    query_embeddings = torch.from_numpy(query_embedding).float()#.to('cuda')
    query_embeddings = util.normalize_embeddings(query_embeddings)
    hits = util.semantic_search(query_embeddings, corpus_embeddings, score_function=util.dot_score)
    top_hits = hits[0][0:3]
    
    ids = [item['corpus_id'] for item in top_hits]
    scores = pd.Series([round(item['score'],3) for item in top_hits])

    if return_top == True:
       return hf_data.iloc[ids[0]]['Lyric'][:200]
    else: 
       songs = hf_data.iloc[ids].reset_index()
       songs = pd.concat([songs, scores], axis = 1)

       songs.rename(columns={0: 'Score'},
          inplace=True)
       return songs.drop(columns = 'index')

msmarco_match(query, return_top= False)

msmarco_match(query)

msmarco_match(query, return_top = False)

"""## Fine-tuned all-mini -- small dataset"""

model_fine_tuned = SentenceTransformer('Santarabantoosoo/songs_fine-tuned-all-MiniLM-L12-v2')

embeddings_sds_ft = model_fine_tuned.encode(sds['lyrics'])
sds['embeddings_ft'] = list(embeddings_sds_ft)

def relevance_scores_ft(query_embed):
    scores = [cosine_similarity(query_embed, v2) for v2 in sds['embeddings_ft']]
    scores = pd.Series(scores)
    return(scores)


def semantic_search_ft(query_sentence, df = sds, return_top = False):
    query_embed = model_fine_tuned.encode(query_sentence)
    scores = relevance_scores(query_embed)
    df['scores'] = scores
    sorted_df = df.sort_values(by = 'scores', ascending = False)
    if return_top == False:
        sorted_df['scores'] = round(sorted_df['scores'],3)
        return sorted_df[['title','artist','scores']].head(3)
    else:
        return sorted_df.iloc[0]['lyrics'][:200]

"""## Gradio App """

def get_recom(choice, query): 
    if choice == "all-MiniLM":
        return  semantic_search(query), semantic_search(query, return_top = True) 
    elif choice == "all-MiniLM-fine-tuned":
        return  semantic_search_ft(query), semantic_search_ft(query, return_top = True) 
    else: 
        list_query = []
        query2 = query
        list_query.append([query, query2])
        return msmarco_match(list_query, return_top = False) ,  msmarco_match(list_query)
        

iface = gr.Interface(    
    title = 'Enjoy our recommendations', 
                     description = 'Do you think we can guess what you like?', 
                    fn=get_recom, 
                     inputs=  [ gr.Radio(choices = ["all-MiniLM", "all-MiniLM-fine-tuned", "msmarco"], label="Choose ur model"),
    gr.Textbox(lines=4, placeholder="Enter ur query...", label = 'Query', show_label = True)],
    outputs = [gr.Dataframe(label = "Top songs", show_label = True), 
               gr.Text(label = 'A glimpse of the closest match', show_label = True)]
    ,live = False,
    interpretation="default",
)


iface.launch(share = False, debug = True)



from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')

query_embedding = model.encode('I am so happy')
passage_embedding = model.encode(sds['embeddings'])

print("Similarity:", util.dot_score(query_embedding, passage_embedding))

