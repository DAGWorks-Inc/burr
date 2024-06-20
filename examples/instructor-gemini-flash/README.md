# Structured Outputs with Instructor

We will show how to use [Instructor](https://python.useinstructor.com/) with [Gemini Flash](https://deepmind.google/technologies/gemini/flash/) to get structured outputs with a human in the loop.

Suppose you have an outline for a course you're teaching and you want to break it down into n topics with this structure:  

    Topic 1
    |__ Subtopic 1
        |__ Concept 1
        |__ Concept 2
        |   ...
    |__ Subtopic 2
        |__ Concept 1
        |__ Concept 2
        |__ Concept 3
        |   ...
    |   ...
    Topic 2
    |__ Subtopic 1
        |__ Concept 1
        |   ...
    |   ...
    .
    .
    .
    Topic n
    |__ Subtopic 1
        |__ Concept 1
        |   ...
    |   ...
    
Instructor allows us to set `Topic` as the return type of our LLM call. So we can guarantee that the output will be a `Topic` object, and not just a string.

## How to run

To run this example, you need to install the following dependencies:

```bash
pip install -r requirements.txt
```

Then if you run `jupyter lab` you can open/execute the notebook.
This simulates an interactive web app. The notebook is the best way to get started.