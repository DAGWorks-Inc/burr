# Build trustworthy LLM agents & applications for production with Instructor + Burr

The challenge with large language models (LLMs) is handling the 5% of the time they say crazy things. Being able to debug why an output is bad and having tools for fixing are critical requirements for making LLM features / agents trustworthy and available to users.

In this example, you'll learn how `instructor` can make LLM reliability produce structured outputs, and `burr` helps you introspect and debug your application.

In a few lines of code, you can query an LLM API and can create powerful productivity utilities. However, user-facing features deserve much more scrutiny, which requires tooling and solving complex engineering problems.

Building our app with Burr provides several benefits that we'll detail next:
- **Observability**: monitor in real-time and log the execution of your `Application` and view it in Burr's web user interface.
- **Persistence**: At any point, you can save the application `State`. This allows to create user sessions (e.g., the conversation history menu in ChatGPT), which helps developers investigate bugs and test potential solutions.
- **Portability**: your `Application` can run in a notebook, as a script, as a web service, or anywhere Python runs. We'll show how to use Burr with [FastAPI](https://fastapi.tiangolo.com/).
