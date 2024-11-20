import lancedb
import openai


def relevant_chunks(user_query: str) -> list[dict]:
    chunks_table = lancedb.connect("./blogs").open_table("chunks")
    search_results = (
        chunks_table.search(user_query).select(["text", "url", "position"]).limit(3).to_list()
    )
    return search_results


def system_prompt(relevant_chunks: list[dict]) -> str:
    relevant_content = "\n".join([c["text"] for c in relevant_chunks])
    return (
        "Answer the user's questions based on the provided blog post content. "
        "Answer in a concise and helpful manner, and tell the user "
        "if you don't know the answer or you're unsure.\n\n"
        f"BLOG CONTENT:\n{relevant_content}"
    )


def llm_answer(system_prompt: str, user_query: str) -> str:
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
    )
    return response.choices[0].message.content
