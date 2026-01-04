import weaviate

with weaviate.connect_to_local() as client:
    print([c for c in client.collections.list_all()])
    coll = client.collections.get("CefrGrammarProfile")
    res = coll.query.fetch_objects(limit=3)
    for obj in res.objects:
        print(obj.properties)