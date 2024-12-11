import boto3


def createDepsTree():
    s3_client = boto3.client('s3')
    report = s3_client.get_object(
                Bucket="demo-bucket-cloudformation",
                Key="deps/deps.txt"
            )
    
    body = report['Body']
    fileContent = body.read().decode('utf-8')
    
    tree = {}
    
    for line in fileContent.splitlines():
        [src, dst] = line.split(" -> ")
        src = src.strip()
        dst = dst.strip()
        if src not in tree:
            tree[src] = []
        
        tree[src].append(dst)
        
    for key in tree.keys():
        print(f"key: {key}")
        for item in tree[key]:
            print(f"\titem: {item}")
    return tree
