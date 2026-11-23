from backend.rag.retriever import SearchHit

NOT_FOUND_MESSAGE="I could not find this in the manual."
PROMPT_TEMPLATE = """You are a technical assistant for marine engineers working with the HiMSEN H21/32 diesel generator engine.

Answer the question using ONLY the manual excerpts below.
- If the answer is not in the excerpts, reply exactly: "{not_found}"
- Be concise and practical. Use numbered steps for procedures.
- After the answer, list the sources you used as: Sources: <section code> (p. <page>)

Manual excerpts:
{context}

Question: {question}
Answer:"""

def build_prompt(question:str,hits:list[SearchHit]) -> str:
    context_parts=[]
    for hit in hits:
        context_parts.append(f"[Section {hit.section_code} - {hit.section_title}, page {hit.page_number}]\n{hit.content}")
    context = "\n\n---\n\n".join(context_parts)
    return PROMPT_TEMPLATE.format(not_found=NOT_FOUND_MESSAGE, context=context, question=question)