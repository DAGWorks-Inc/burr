# Tool-calling

This example shows the basic tool-calling design pattern for agents.

While this leverages the [OpenAI API](https://platform.openai.com/docs/guides/function-calling), the lessons are the same whether you use different tool-calling APIs (E.G. [Anthropic](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)), or general structured outputs (E.G. with [instructor](https://useinstructor.com/)).

Rather than explain the code here, we direct you to the [blog post](https://blog.dagworks.io/p/agentic-design-pattern-1-tool-calling)

# Files

- [application.py](application.py) -- contains code for calling tools + orchestrating them
- [notebook.ipynb](notebook.ipynb) -- walks you through the example with the same code
- [requirements.txt] -- install this to get the right environment
