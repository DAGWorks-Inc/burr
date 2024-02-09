# Burr

## What is Burr?

Burr is a state machine for data/AI projects. You can (and should!) use it for anything where managing state can be hard. Hint: managing state
is always hard!

You can find the documentation [here](https://studious-spork-n8kznlw.pages.github.io/).
## What can you do with Burr?

Burr can be used for a variety of applications. Burr can build a state machine to orchestrate, express, and track:

1. [A gpt-like chatbot](examples/gpt)
2. [A machine learning pipeline](examples/ml_training)
3. [A trading simulation](examples/simulation)

And a lot more!

Using hooks and other integrations you can (a) integrate with any of your favorite vendors (LLM observability, storage, etc...), and
(b) build custom actions that delegate to your favorite libraries.

Bur will *not* tell you how to build your models, how to query APIs, or how to manage your data. It will help you tie all these together
in a way that scales with your needs and makes following the logic of your system easy.


## Why the name Burr?

Burr is named after Aaron Burr, founding father, third VP of the United States, and murderer/arch-nemesis of Alexander Hamilton.
We imagine a world in which Burr and Hamilton lived in harmony and saw through their differences. We originally
built Burr as a _harness_ to handle state between executions of Hamilton DAGs,
but realized that it has a wide array of applications and decided to release it.

# Getting Started

To get started, install from `pypi`, using your favorite package manager:

```
pip install burr
```

Next, see the documentation for [getting started](https://studious-spork-n8kznlw.pages.github.io/getting_started/simple-example.html), and follow the example.
Then read through some of the concepts and write your own application!
