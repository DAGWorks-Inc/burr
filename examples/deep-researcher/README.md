# Deep Researcher

## Introduction

The structure of the research assistant is taken from a [langchain and langgraph example](https://github.com/langchain-ai/local-deep-researcher). It is rewritten here in the Burr framework in `application.py`.

![Deep Researcher](statemachine.png)

The helper code in `prompts.py` and `utils.py` is directly taken from the original deep researcher codebase. The following is its license:

> MIT License
>
> Copyright (c) 2025 Lance Martin
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Prerequisites

Set the configuration variables at the beginning of the main section of `application.py`.

Then install Python modules
```sh
pip install -r requirements.txt
```

You will need accounts for [Tavily search](https://tavily.com/) and the [OpenAI API](https://platform.openai.com/docs/overview). Once you have those accounts, set the environment variables TAVILY_API_KEY and OPENAI_API_KEY and run the script.

```sh
export OPENAI_API_KEY="YOUR_OPENAI_KEY"
export TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
python application.py
```
