#!/bin/bash
aws ecr get-login-password --region sa-east-1 | docker login --username AWS --password-stdin 971901834579.dkr.ecr.sa-east-1.amazonaws.com
docker build -t casia/crawler .
docker tag casia/crawler:latest 971901834579.dkr.ecr.sa-east-1.amazonaws.com/casia/crawler:latest
docker push 971901834579.dkr.ecr.sa-east-1.amazonaws.com/casia/crawler:latest