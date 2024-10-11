# Use an official Python runtime as a parent image
FROM python:3.11-bookworm

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
# Assuming you have a requirements.txt file with all the necessary dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY server.py /app
COPY wrapper.sh /app

# Make port 7241 and 7242 available to the world outside this container
EXPOSE 7241 7242

# Make the wrapper script executable
RUN chmod +x wrapper.sh

# Run wrapper.sh when the container launches
CMD ["./wrapper.sh"]
