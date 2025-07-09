#4:47
from django.shortcuts import get_object_or_404, render
import os
# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse
from .models import UploadedFile, FileModel
import boto3
from django.conf import settings
from django.views import View
import botocore.exceptions


# Initialize the boto3 client for advanced operations if needed (optional)
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)

def index(request):
    files = UploadedFile.objects.all().order_by('-uploaded_at')
    valid_files = [file for file in files if file.s3_key and check_file_exists_in_s3(file.s3_key)]
    return render(request, "fileapp/index.html", {"files": valid_files})

def upload_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = UploadedFile(file=request.FILES["file"])
        uploaded_file.save()  # Save first to generate an ID
        uploaded_file.s3_key = uploaded_file.file.name  # Remove 'uploads/' prefix
        uploaded_file.save(update_fields=["s3_key"])  # Ensure s3_key is saved
        return render(request, "fileapp/upload_success.html", {"filename": uploaded_file.file.name})
    return JsonResponse({"error": "Invalid request"}, status=400)

def download_file(request, id):
    try:
        file_obj = UploadedFile.objects.get(id=id)  # Fetch the file from DB
        filename = os.path.basename(file_obj.file.name)
        file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/uploads/{filename}"
        return JsonResponse({"file_url": file_url}, status=200)
    except UploadedFile.DoesNotExist:
        return JsonResponse({"error": "File not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# fileapp/views.py
def generate_presigned_url(file_key):
    s3 = boto3.client(
        "s3",
        region_name=AWS_S3_REGION_NAME,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    try:
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_STORAGE_BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600  # Valid for 1 hour
        )
        return presigned_url
    except Exception as e:
        # Handle or log the exception as needed
        return None

import boto3

def delete_file(request, file_key):
    print(f"🔍 Delete request received for: {file_key}")

    if request.method == "POST":
        try:
            # Step 1: Verify file exists in database
            file_instance = UploadedFile.objects.filter(s3_key=file_key).first()
            if not file_instance:
                print(f"❌ File not found in DB: {file_key}")
                return JsonResponse({"error": "File not found"}, status=404)

            print(f"✅ File found in DB: {file_key}")

            # Step 2: Attempt deletion from S3
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            try:
                print(f"🔍 Deleting from S3: {file_key}")
                response = s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
                print(f"✅ S3 deletion response: {response}")
            except Exception as s3_error:
                print(f"❌ S3 Deletion Failed: {s3_error}")
                return JsonResponse({"error": str(s3_error)}, status=500)

            # Step 3: Delete from database
            file_instance.delete()
            print(f"✅ Deleted {file_key} from DB")

            return render(request, "fileapp/delete_success.html")

        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)



def delete_success(request):
    return render(request, "delete_success.html")

def check_file_exists_in_s3(file_key):
    if not file_key:  # Prevent passing None
        print("🚨 Warning: Received a None file_key!")  # Debugging
        return False

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,  # Ensure region is passed
    )

    try:
        print(f"🔍 Checking file in S3: {file_key}")  # Debugging
        s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        print(f"✅ File exists: {file_key}")  # Confirm success
        return True
    except botocore.exceptions.ClientError as e:
        print(f"❌ S3 Error: {e}")  # Detailed exception logging
        return False  # File not found in S3

