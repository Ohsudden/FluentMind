from pathlib import Path

import pandas as pd
import weaviate
from weaviate.classes.config import Configure, DataType, Property


def recreate_collection(
    client: weaviate.WeaviateClient,
    name: str,
    *,
    vector_config=None,
    vectorizer_config=None,
    reranker_config=None,
    properties=None,
):

    if client.collections.exists(name):
        client.collections.delete(name)

    return client.collections.create(
        name=name,
        vector_config=vector_config,
        vectorizer_config=vectorizer_config,
        reranker_config=reranker_config,
        properties=properties,
    )

DATASET_PATH = Path("datasets") / "voc_combined.csv"
CEFR_TEXT_DATASET = Path("datasets") / "cefr_leveled_texts.csv"
GRAMMAR_DATASET = Path("datasets") / "cefrj-grammar-profile-20180315.csv"

VOCAB_COLLECTION = "Vocabulary"
SECONDARY_COLLECTION = "vocabulary"
CEFR_TEXT_COLLECTION = "CefrLeveledTexts"
GRAMMAR_COLLECTION = "CefrGrammarProfile"
VECTOR_SOURCE_PROPERTIES = [
    "headword",
    "pos",
    "CEFR",
]

GRAMMAR_COLUMN_MAP = {
    "ID": ("grammar_id", DataType.TEXT),  
    "Shorthand Code": ("shorthand_code", DataType.TEXT),
    "Grammatical Item": ("grammatical_item", DataType.TEXT),
    "Sentence Type": ("sentence_type", DataType.TEXT),
    "CEFR-J Level": ("cefr_j_level", DataType.TEXT),
    "FREQ*DISP": ("freq_disp", DataType.TEXT),
    "Core Inventory": ("core_inventory", DataType.TEXT),
    "EGP": ("egp", DataType.TEXT),
    "GSELO": ("gselo", DataType.TEXT),
    }

def _clean_value(value):
    if pd.isna(value):
        return ""
    return str(value)


def _ingest_records(collection, records, batch_size=200):
    with collection.batch.fixed_size(batch_size=batch_size) as batch:
        for obj in records:
            batch.add_object(properties=obj)


def _ingest_vocabulary(client):
    shared_properties = [
        Property(name="headword", vectorize_property_name=True, data_type=DataType.TEXT),
        Property(name="pos", vectorize_property_name=True, data_type=DataType.TEXT),
        Property(name="CEFR", vectorize_property_name=True, data_type=DataType.TEXT),
    ]

    collection = recreate_collection(
        client,
        VOCAB_COLLECTION,
        vectorizer_config=Configure.Vectorizer.text2vec_ollama(
            api_endpoint="http://ollama:11434",
            model="nomic-embed-text",
        ),
        properties=shared_properties,
    )

    df = pd.read_csv(DATASET_PATH)[["headword", "pos", "CEFR"]]
    records = df.to_dict(orient="records")

    recreate_collection(
        client,
        SECONDARY_COLLECTION,
        vectorizer_config=Configure.Vectorizer.none(),
        reranker_config=None,
        properties=shared_properties,
    )

    _ingest_records(collection, records)
    print(f"Imported & vectorized {len(records)} objects into the {VOCAB_COLLECTION} collection")


def _ingest_cefr_texts(client):
    collection = recreate_collection(
        client,
        CEFR_TEXT_COLLECTION,
        vectorizer_config=Configure.Vectorizer.text2vec_ollama(
            api_endpoint="http://ollama:11434",
            model="nomic-embed-text",
        ),
        properties=[
            Property(name="text", data_type=DataType.TEXT, vectorize_property_name=True),
            Property(name="label", data_type=DataType.TEXT, vectorize_property_name=True),
        ],
    )

    df = pd.read_csv(CEFR_TEXT_DATASET)
    records = (
        df.fillna("")
        .assign(label=lambda frame: frame["label"].astype(str))
        .to_dict(orient="records")
    )

    _ingest_records(collection, records, batch_size=100)
    print(f"Imported {len(records)} leveled texts into {CEFR_TEXT_COLLECTION}")


def _ingest_grammar_profile(client):
    properties = []
    for _, (prop_name, data_type) in GRAMMAR_COLUMN_MAP.items():
        properties.append(
            Property(name=prop_name, data_type=data_type, vectorize_property_name=True)
        )

    collection = recreate_collection(
        client,
        GRAMMAR_COLLECTION,
        vectorizer_config=Configure.Vectorizer.text2vec_ollama(
            api_endpoint="http://ollama:11434",
            model="nomic-embed-text",
        ),
        properties=properties,
    )

    df = pd.read_csv(GRAMMAR_DATASET)
    records = []
    for _, row in df.iterrows():
        record = {}
        for source, (prop_name, _) in GRAMMAR_COLUMN_MAP.items():
            record[prop_name] = _clean_value(row[source])
        records.append(record)

    _ingest_records(collection, records, batch_size=100)
    print(f"Imported {len(records)} grammar rows into {GRAMMAR_COLLECTION}")



if __name__ == "__main__":
    with weaviate.connect_to_local() as client:
        _ingest_vocabulary(client)
        _ingest_cefr_texts(client)
        _ingest_grammar_profile(client)