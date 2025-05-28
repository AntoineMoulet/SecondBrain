#!/bin/bash

echo "Testing development environment (using .env file):"
echo "----------------------------------------------"
python test_config.py

echo -e "\nTesting production environment (using ENV variable):"
echo "----------------------------------------------"
ENV=production python test_config.py 