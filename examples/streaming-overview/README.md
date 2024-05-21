# Streaming chatbot

This example shows how we can use the streaming API
to respond to return quicker results to the user and build a more
seamless interactive experience.

This is the same chatbot as the one in the `chatbot` example,
but it is built slightly differently (for streaming purposes).

## How to use

Run `streamlit run streamlit_app.py` from the command line and you will see the chatbot in action.
Open up the burr UI `burr` and you can track the chatbot.

## Async

We also have an async version in [async_application.py](async_application.py)
which demonstrates how to use streaming async. We have not hooked this up
to a streamlit application yet, but that should be trivial.

## Notebook
The notebook also shows how things work. <a target="_blank" href="https://colab.research.google.com/github/dagworks-inc/burr/blob/main/examples/streaming-overview/notebook.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>
