from knowledge.db import get_all_knowledge

async def find_relevant_chunks(query: str, max_chunks: int = 3) -> list[str]:
    keywords = [w.lower() for w in query.split() if len(w) > 2]
    if not keywords:
        return []
    all_knowledge = await get_all_knowledge()
    scored = []
    for row in all_knowledge:
        content_lower = row["content"].lower()
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scored.append((score, row["content"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [content for _, content in scored[:max_chunks]]
