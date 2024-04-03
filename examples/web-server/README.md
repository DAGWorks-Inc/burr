# Running Burr in a web server

We're working on fleshing out this demo, but we have an example to get started with.

You can play around with this example by running the `burr` command after running `pip install`.
Then navigate to [examples/chatbot](http://localhost:7241/demos/chatbot) in your browser (it will open up).

```bash
pip install burr[start]
burr
```

You'll see the telemetry on the right and the chatbot on the left.

## General strategy

The general approach for a read/write app (say, a chatbot) is as follows:
1. Instantiate a burr application using the builder whenever you need it, loading the state from your persistence layer
2. Use the burr application object to handle incoming requests
3. Return the full state result from the burr application object to the client
4. Render that on the frontend

This way you can keep the frontend simple (just render burr's state), and keep the backend simple (delegate
loading/persistence/logic to burr). Then you can view in telemetry.

## Code

To see the code, you'll want to open the following:

- [application file](../multi-modal-chatbot/application.py) - The main application file. This defines the Burr logic
- [fastAPI app](../../tracking/server/examples/chatbot.py) - The server file. This defines the FastAPI app

You can see that the server file defines a rounter which gets imported by the main server file -- this
allows us to reuse this in the demo. We'll be updating this with a self-contained copy/paste example shortly, stay tuned!
