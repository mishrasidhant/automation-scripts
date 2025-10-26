#!/bin/bash
# Quick test for background recording and stopping

echo "Testing background recording with --stop command"
echo "================================================"
echo ""

# Clean up any existing files
rm -f /tmp/dictation/*.wav
rm -f /tmp/dictation.lock

echo "1. Starting recording in background..."
python dictate.py --start &
RECORDING_PID=$!

echo "   Recording PID: $RECORDING_PID"
echo ""

# Wait a bit and check lock file
sleep 2
echo "2. Checking lock file..."
if [ -f /tmp/dictation.lock ]; then
    echo "   ✓ Lock file exists"
    cat /tmp/dictation.lock | head -3
else
    echo "   ✗ Lock file not found!"
    exit 1
fi
echo ""

# Wait a few more seconds for some audio
sleep 3
echo "3. Stopping recording with --stop command..."
python dictate.py --stop
echo ""

# Check if file was created
sleep 1
echo "4. Checking for WAV file..."
if ls /tmp/dictation/*.wav 1> /dev/null 2>&1; then
    WAV_FILE=$(ls /tmp/dictation/*.wav | head -1)
    echo "   ✓ WAV file created: $WAV_FILE"
    FILE_SIZE=$(du -h "$WAV_FILE" | cut -f1)
    echo "   File size: $FILE_SIZE"
    
    # Check file format
    file "$WAV_FILE"
else
    echo "   ✗ No WAV file found!"
    exit 1
fi
echo ""

echo "✅ Test passed!"
echo ""
echo "You can play the recording with:"
echo "   aplay $WAV_FILE"

