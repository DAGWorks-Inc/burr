import textwrap

import pyarrow as pa


def generative_context(search_results: pa.Table) -> str:
    results = search_results.to_pandas()["text"].to_list()
    return " ".join(results)


def response_prompt(search_input: str, generative_context: str) -> str:
    return textwrap.dedent(
        f"""
        CONTEXT
        {generative_context}

        CONVERSATION
        User: {search_input}
        Assistant:"""
    )
