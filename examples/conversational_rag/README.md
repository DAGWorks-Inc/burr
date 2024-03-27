# Conversational RAG with memory
This example demonstrates how to build a conversational RAG agent with "memory".

The "memory" here is stored in state, which Burr then can help you track,
manage, and introspect.

The set up of this example is that you have:

1. Some initial "documents" i.e. knowledge.
2. We bootstrap a vector store with these documents.
3. We then have a pipeline that uses a vector store for a RAG query.
4. We hook everything together with Burr that will manage the state
of the conversation and asking for user inputs.

To run this example, install Burr and the necessary dependencies:

```bash
pip install "burr[start]" -r requirements.txt
```

Then run the server in the background:

```bash
burr
```

Make sure you have an `OPENAI_API_KEY` set in your environment.

Then run
```bash
python application.py
```

You'll then have a text terminal where you can interact. Type exit to stop.

# Video Walkthrough via Notebook
Watch the video walkthrough in the notebook (1.5x+ speed recommended):
<div>
<iframe width="800" height="455" src="https://www.youtube.com/embed/t54DCiOH270?si=QpPNs7m2t0L0V8Va" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
