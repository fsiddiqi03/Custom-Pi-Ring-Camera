# Main file for the S3 uploader

import boto3
from datetime import datetime
from config import BUCKET_NAME, BUCKET_NAME, ACCESS_KEY, SECRET_KEY

class S3Uploader:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket_name = BUCKET_NAME
        self.region_name = BUCKET_NAME
        self.access_key = ACCESS_KEY
        self.secret_key = SECRET_KEY
    

    def create_file_name(self):
        return datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"

    
    def upload_file(self, frame):
        file_name = self.create_file_name()
        self.s3.upload_file(frame, self.bucket_name, file_name)