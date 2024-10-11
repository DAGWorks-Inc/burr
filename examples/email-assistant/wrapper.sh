#!/bin/bash

# Start the Burr UI
burr --host 0.0.0.0 &

# Start the FastAPI server using uvicorn
uvicorn server:app --host 0.0.0.0 --port 7242