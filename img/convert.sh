#!/bin/bash

# Check if a filename argument was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

FILENAME="$1"

# Verify the input file exists before running ffmpeg
if [ ! -f "input.mp4" ]; then
    echo "Error: 'input.mp4' not found in current directory."
    exit 1
fi

# Run the conversion command
echo "Converting video to $FILENAME..."
ffmpeg -i input.mp4 -c:v libx264 "$FILENAME".mp4

# Check if ffmpeg succeeded (exit code 0)
if [ $? -eq 0 ]; then
    echo "Conversion successful. Deleting original file."
    
    # Delete the original input file
    rm -f input.mp4
    
else
    echo "Error: Conversion failed or was interrupted."
fi

echo "Done."

