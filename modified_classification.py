import base64
from io import BytesIO
import logging

import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from urllib.request import urlopen
from PIL import Image
import numpy as np
import json
import sys
import time
import boto3

sqs = boto3.client('sqs')

file_handler = logging.FileHandler('classification.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logging.basicConfig(filename='classification.log', level=logging.DEBUG)
queue_url = 'https://sqs.us-east-1.amazonaws.com/874290406143/request_queue'

while True:
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    )
    if 'Messages' in response:
        message = response['Messages'][0]
        logging.debug('Received message from SQS', message)
        message_body = json.loads(message['Body'])
        image_data = message_body['image']
        # Logging ID for tracing
        logging.debug(f"Message Id: {message_body['id']}")
        # Decode the base64-encoded image data
        decoded_data = base64.b64decode(image_data)

        # Load the decoded data into a PIL image
        img = Image.open(BytesIO(decoded_data))
        model = models.resnet18(pretrained=True)

        model.eval()
        img_tensor = transforms.ToTensor()(img).unsqueeze_(0)
        outputs = model(img_tensor)
        _, predicted = torch.max(outputs.data, 1)

        with open('./imagenet-labels.json') as f:
            labels = json.load(f)
        result = labels[np.array(predicted)[0]]
        img_name = "received_image"
        # save_name = f"({img_name}, {result})"
        save_name = f"{img_name},{result}"
        print(f"{save_name}")

        # Delete the message from the queue
        receipt_handle = message['ReceiptHandle']
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        # TODO:Upload Image to S3 input bucket - Use id by message_body['id'] and img

        # TODO: Upload result to output bucket - Use result and id by message_body['id']

    else:
        logging.info("No messages in queue")
#img = Image.open(urlopen(url))

