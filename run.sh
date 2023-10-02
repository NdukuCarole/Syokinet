#!/bin/bash

cd .
# Set the host and port for the FastAPI application
HOST="0.0.0.0"
PORT="8000"

# Set the main file of your FastAPI application (replace "main.py" with your actual main file)
MAIN_FILE="main"

# Command to run the FastAPI application with Uvicorn
uvicorn $MAIN_FILE:app --host $HOST --port $PORT --reload
