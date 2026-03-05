#!/bin/bash

# This is the sample hook script.

# jq '[.subject, .sender.address, .to_recipients[].address]' > /path/to/save.txt