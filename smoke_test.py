from src.models.meta import MetaModel, total_spent

m = MetaModel("muse-spark-1.3")
print(m.complete("", [{"role": "user", "content": "Say hi in 3 words."}]))
print(f"Estimated spend so far: ${total_spent():.5f}")