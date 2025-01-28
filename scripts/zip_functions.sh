#!/bin/bash

# Directory containing all function directories
FUNCTIONS_DIR="functions"

# Loop through each function directory
for func_dir in "$FUNCTIONS_DIR"/*/ ; do
    if [ -d "$func_dir" ]; then
        echo "Processing $func_dir"
        
        # Create zip file
        cd "$func_dir"
        zip -r function.zip . -x "*.zip"
        cd - > /dev/null
        
        echo "Created function.zip in $func_dir"
    fi
done 