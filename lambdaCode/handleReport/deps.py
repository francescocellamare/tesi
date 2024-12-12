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
        
        output_content = ""
        for key in tree.keys():
            output_content += f"key: {key}\n"
            for item in tree[key]:
                output_content += f"\titem: {item}\n"

        # Write the output content to a new file in the S3 bucket
        output_key = "deps/deps_tree_output.txt"
        s3_client.put_object(
            Bucket='demo-package-bucket',
            Key=output_key,
            Body=output_content
        )
    return tree
