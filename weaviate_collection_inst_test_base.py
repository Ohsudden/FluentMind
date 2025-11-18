from pathlib import Path

import pandas as pd
import weaviate
from weaviate.classes.config import Configure, DataType, Property


DATASET_PATH = Path("datasets") / "voc_combined.csv"
VOCAB_COLLECTION = "Vocabulary"
SECONDARY_COLLECTION = "vocabulary"
VECTOR_SOURCE_PROPERTIES = [
    "headword",
    "pos",
    "CEFR",
    "CoreInventory 1",
    "CoreInventory 2",
    "Threshold",
    "notes",
]

with weaviate.connect_to_local() as client:
    if client.collections.exists(VOCAB_COLLECTION):
        vocabulary = client.collections.get(VOCAB_COLLECTION)
    else:
        vocabulary = client.collections.create(
            name=VOCAB_COLLECTION,
            vector_config=Configure.Vectors.text2vec_ollama(
                api_endpoint="http://host.docker.internal:11434",
                model="nomic-embed-text",
            ),
        )

    df = pd.read_csv(DATASET_PATH)
    data_objects = df.to_dict(orient="records")

    vectorizer_config = [
        Configure.NamedVectors.text2vec_transformers(
            name="vector",
            source_properties=VECTOR_SOURCE_PROPERTIES,
            vectorize_collection_name=False,
            inference_url="http://127.0.0.1:5000",
        )
    ]

    if client.collections.exists(SECONDARY_COLLECTION):
        collection = client.collections.get(SECONDARY_COLLECTION)
    else:
        collection = client.collections.create(
            name=SECONDARY_COLLECTION,
            vectorizer_config=vectorizer_config,
            reranker_config=Configure.Reranker.transformers(),
            properties=[
                Property(name="headword", vectorize_property_name=True, data_type=DataType.TEXT),
                Property(name="pos", vectorize_property_name=True, data_type=DataType.TEXT),
                Property(name="CEFR", vectorize_property_name=True, data_type=DataType.TEXT),
                Property(name="CoreInventory 1", vectorize_property_name=True, data_type=DataType.TEXT),
                Property(name="CoreInventory 2", vectorize_property_name=True, data_type=DataType.TEXT),
                Property(name="Threshold", vectorize_property_name=True, data_type=DataType.TEXT),
                Property(name="notes", vectorize_property_name=True, data_type=DataType.TEXT),
            ],
        )

    vocabulary = client.collections.use(VOCAB_COLLECTION)
    with vocabulary.batch.fixed_size(batch_size=200) as batch:
        for obj in data_objects:
            batch.add_object(properties=obj)

    print(
        f"Imported & vectorized {len(data_objects)} objects into the {VOCAB_COLLECTION} collection"
    )