from minio import Minio
from minio.error import S3Error


MINIO_ADDRESS = '10.43.103.121:9000'
MINIO_ACCESS = 'DgZG6K01XCNQbQ3z'
MINIO_SECRET = 'PXUSMTYhTcNCSkHkl3OOqHh2xJ9eMe2b'
BUCKET_NAME = 'workspace'


def get_pickles(path, pcklname):
    print("function get_pickles start", 50*'-')
    minio_client = Minio(
        MINIO_ADDRESS,
        access_key=MINIO_ACCESS,
        secret_key=MINIO_SECRET,
        secure=False,
    )
    try:
        objects = minio_client.list_objects(BUCKET_NAME, recursive=True)
        print('get objects in minio')
        if any(True for _ in objects):
            for obj in objects:
                print('Checking ', obj.object_name)
                # if obj.object_name.endswith(endswith):
                if obj.object_name == (pcklname):
                    # Download the pickle
                    print(f'processing {obj.object_name}')
                    local_path = path + obj.object_name
                    minio_client.fget_object(BUCKET_NAME, obj.object_name, local_path)
        else:
            print('Pickles not found')
    except S3Error as exc:
        print("Error occurred:", exc)

def put_file(full_path, minio_object_name):
    minio_client = Minio(
        MINIO_ADDRESS,
        access_key=MINIO_ACCESS,
        secret_key=MINIO_SECRET,
        secure=False,
    )
    try:
        # Upload the result back to MinIO
        minio_client.fput_object(BUCKET_NAME, minio_object_name, full_path)
    except S3Error as exc:
        print("Error occurred:", exc)
