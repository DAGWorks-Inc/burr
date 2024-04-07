# Image Telephone

This example demonstrates how to play telephone with DALL-E and ChatGPT. See some examples of the outputs
in this [streamlit app](https://image-telephone.streamlit.app).

It is a fun example of how to use Burr! In this example you'll see a simple way to define an application
that talks to itself to do something fun. The game is simple:

1. You provide an initial image to ChatGPT, which then generates a caption. The caption is saved to state.
2. That caption is then provided to DALL-E, which generates an image based on the caption, which is saved to state.
3. The loop repeats -- and you have encoded the game of telephone!

Specifically, each action here in Burr is delegated to the [Hamilton](https://github.com/dagworks-inc/hamilton) micro-framework to run.
Hamilton is a great replacement for tools like LCEL, because it's built to provide a great SDLC experience, in addition
to being lightweight, extensible and more general
purpose (e.g. it's great for expressing things data processing, ML, and web-request logic). We're using
off-the-shelf dataflows from the [Hamilton hub](https://hub.dagworks.io) to do the work of captioning and generating images.

Right now the terminal state is set to four iterations, so the game will end after 4 images are captioned:

![Telephone](statemachine.png)

## Running the Example
We recommend starting with the notebook.

### notebook.ipynb
You can use [notebook.ipynb](./notebook.ipynb) to run things. Or
<a target="_blank" href="https://colab.research.google.com/github/DAGWorks-Inc/burr/blob/main/examples/image-telephone/notebook.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

### Running application.py

To run the basics do:
```bash
python application.py
```
To modify it for your purposes you'll need to adjust the code to point to your image that you want to start with.

## Modifying the telephone game
There are two levels you can modify:

1. The high-level orchestration and state management
2. What each action actually does.

For the high-level orchestration you can add more nodes, modify the actions (e.g. to save the images),
change conditions, etc.

For the low-level actions, you can change the prompt, the template, etc. too. To do so see the
documentation for the Hamilton dataflows that are used: [captioning](https://hub.dagworks.io/docs/Users/elijahbenizzy/caption_images/) and
[generating image](https://hub.dagworks.io/docs/Users/elijahbenizzy/generate_images/). You can easily modify the prompt and
template by overriding values, or by copying the code and modifying it yourself in 2 minutes - see instructions on the [hub](https://hub.dagworks.io/).

## Hamilton code
For more details on the [Hamilton](https://github.com/dagworks-inc/hamilton) code and
this [streamlit app](https://image-telephone.streamlit.app) see [this example in the Hamilton repo.](https://github.com/DAGWorks-Inc/hamilton/tree/main/examples/LLM_Workflows/image_telephone)
