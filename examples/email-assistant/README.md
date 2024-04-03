# Email Assistant

This example shows how to create a basic email assistant. This assistant
takes in an email and will write a response. It allows you to prompt it with:
1. An email
2. Directions on how to respond

Then it generates questions for you for clarifications, and uses the answer to write a draft.
It will go back and forth with you until you are satisfied with the response.

This demonstrates how to do multi-shot modeling interactively with an LLM. You'll learn:

1. How to move in/out of program control -> user control
2. How to process inputs at multiple points through the process
3. How to involve multi-shot modeling with an LLM

## How to run

To run this example, you need to install the following dependencies:

```bash
pip install -r requirements.txt
```

Then if you run `jupyter lab` you can open/execute the notebook.
This simulates an interactive web app. The notebook is the best way to get started.

Note we will be adding two things to this demo:
1. An integration with the burr web app
2. a standalone server example with a walkthrough

Open the notebook <a target="_blank" href="https://colab.research.google.com/github/dagworks-inc/burr/blob/main/examples/email-assistant/notebook.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>
