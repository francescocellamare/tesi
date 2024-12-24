import json
import boto3
import io
import re
import zipfile

s3_client = boto3.client('s3')

                # - echo "[{\"name\":\"spring-boot-app\",\"imageUri\":\"$REPOSITORY_URI:latest\"}]" > imagedefinitions.json

def adaptOutput(event, context):
    print(event)
    print(context)
    return [
        {
            "name": "backend-service",
            "imageUri": "344740472567.dkr.ecr.eu-south-1.amazonaws.com/spring-boot-app:latest"   
        },
        {
            "name": "postgres-db",
            "imageUri": "postgres:latest"
        }
    ]