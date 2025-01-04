from openai import OpenAI
import boto3
import json
from botocore.exceptions import ClientError
from enum import Enum

class Model(Enum):
    GPT4o = "gpt-4o"
    GPT4o_mini = "gpt-4o-mini"

TEMPERATURE = 0.5
TOP_1 = 1

def get_secret():
    secret_name = "EnvVar_OpenAi"
    region_name = "eu-south-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response
        secret_string = secret['SecretString']
        secret_dict = json.loads(secret_string)

        openai_api_key = secret_dict.get('OPENAI_API_KEY')
        print(f"key {openai_api_key}")
        return openai_api_key
    except ClientError as e:
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e


client = OpenAI(api_key = get_secret())

def update_test_suite(sourceCode, testCode, error, contentDeps):
    if error == None:
        print("modify")
        prompt = f"""
            Provide the missing tests for the given Java code using the Spring framework with maximum code coverage. Use JUnit5 and Mockito for creating the pure unit tests, focusing on Mockito mocks and skipping Spring context loading. Focus on covering all possible branches and edge cases.
            In some case, there could be some comments to document the method to test like the following case:
            /*
            Function to test the absolute value of the sum of the parameters
            */
            public int AbsOfSum2Int(int a, int b) {{ 
                return Math.abs(a + b);
            }}
            Try to understand the code first and never assume the method behavior according to the function name.
            
            Moreover, the path of the file is {sourceCode['filePath']}, which allows you to determine the package and import the entire project generically. For example, you can import all classes in the project using import com.example.demo.*;. When adding imports, ensure they are as generic as possible to cover all required classes.    
            
                        
            # What you are testing
            It's a Spring Boot project made in the java language which is able to interface with other external resources ie. databases so don't test edge cases like setter for the Ids of the entities/models inside the tables.
            
            # Received Input
            I'm sending you the code of the source code with some of its dependencies as well as the relative tests already written for it as follow between those <>:
            <class MyClass {{
                public int AlreadyTestedMethod() {{ code... }}
                public int NewMethodAdded() {{ new code... }}
                public int ModifiedMethod() {{ modified code... }}
            }}
            
            ###
            
            class MyClassTest {{
                @Test
                void testAlreadyTestedMethod() {{ test code... }}
                
                @Test 
                void testModifiedMethod() {{ already existing test code... }}
            }}
            
            ###
            // dependencies section (it can be empty)
            public class MyClassDependencyOne {{ code... }}
            public class MyClassDependencyTwo {{ code... }}>

            
            # Output Requirements
            - Output only the Java code, do not write the ```java and ``` quotes
            - Exclude any comments or explanations
            - Ensure all dependencies needed for the test are appropriately managed and configured.
            - Write newly added dependencies.
        """

        print("Prompt created")

        input_content = sourceCode['fileContent'].decode('utf-8') + "\n###\n" + testCode['fileContent'].decode('utf-8')
        for item in contentDeps:
            input_content += item['fileContent'].decode('utf-8')
        
        try:
            response = client.chat.completions.create(
                model=Model.GPT4o.value,
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": input_content
                    }
                ],
                temperature=TEMPERATURE,
                top_p=TOP_1
            )

            print("Generated")
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error processing {sourceCode['filePath']}: {e}")
    else:
        print("fix new new")
        prompt = f"""
            Fix the test for the given Java code using the Spring framework with maximum code coverage. Use JUnit5 and Mockito for creating the pure unit tests, focusing on Mockito mocks and skipping Spring context loading. Focus on covering all possible branches and edge cases.
            I'm giving you the test which fails and the error as follow: "testMethodWithFailingTest with error: error which makes it fail".
            In some case, there could be some comments to document the method to test like the following case:
            /*
            Function to test the absolute value of the sum of the parameters
            */
            public int AbsOfSum2Int(int a, int b) {{ 
                return Math.abs(a + b);
            }}
            Try to understand the code first and never assume the method behavior according to the function name.
            
            Moreover, the path of the file is {sourceCode['filePath']}, which allows you to determine the package and import the entire project generically. For example, you can import all classes in the project using import com.example.demo.*;. When adding imports, ensure they are as generic as possible to cover all required classes.    

            
            # What you are testing
            It's a Spring Boot project made in the java language which is able to interface with other external resources ie. databases so don't test edge cases like setter for the Ids of the entities/models inside the tables.
            
            # Received Input
            I'm sending you the code of the source code file as well as the relative tests already written for it as follow between those <>:
            <class MyClass {{
                public int AlreadyTestedMethod() {{ code... }}
                public int MethodWithFailingTest() {{ code... }}
            }}
            
            ###
            
            class MyClassTest {{
                @Test
                void testAlreadyTestedMethod() {{ test code... }}
                
                @Test 
                void testMethodWithFailingTest() {{ test code with lead to a failure... }}
            }}
            
            ### 

            testMethodWithFailingTest with error: error which makes it fail
            
            ###
            // dependencies section (it can be empty)
            public class MyClassDependencyOne {{ code... }}
            public class MyClassDependencyTwo {{ code... }}>
            
            The input example contains sections separated by ### with the following structure:

                - Source Code: The primary class or function implementation.
                - Test Code: Unit tests written for the source code.
                - Failing Test: Details of the failing test, including its name and error message.
                - Dependencies: Supporting classes, functions, or dependencies to help understand the context.

            Your task:

                - Analyze why the test is failing.
                - If the test logic is faulty (e.g., asserting 10.50 but receiving 10.5), fix the test.
                - If the failure requires a change in the source code or dependencies, comment out the test and prepend it with the heading DEV NEEDED.
                
            # Output Requirements
            - Output only the Java code, do not write the ```java and ``` quotes
            - Exclude any comments or explanations
            - Ensure all dependencies needed for the test are appropriately managed and configured.
            - Remove the failing test and return the full fixed test suite
        """

        print(f"Prompt created with error {error}")

        input_content = sourceCode['fileContent'].decode('utf-8') + "\n###\n" + testCode['fileContent'].decode('utf-8') + "\n###\n" + error + "\n###\n"
        for item in contentDeps:
            input_content += item['fileContent'].decode('utf-8')
        try:
            
            s3_client = boto3.client('s3')
            s3_client.put_object(
                Bucket="demo-bucket-cloudformation",
                Key="debug/prompt.txt",
                Body=input_content,
                ContentType="text/plain"
            )
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "message": "An error occurred at writing the debug file",
                    "error": str(e)
                })
            }
            
        try:
            response = client.chat.completions.create(
                model=Model.GPT4o.value,
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": input_content
                    }
                ],
                temperature=TEMPERATURE,
                top_p=TOP_1
            )

            print("Generated")
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error processing {sourceCode['filePath']}: {e}")


def create_test_suite_with_deps(content, path, contentDeps):
    prompt = f"""
    Provide a complete test suite for the given Java code using the Spring framework with maximum code coverage. Use JUnit5 and Mockito for creating the pure unit tests, focusing on Mockito mocks and skipping Spring context loading. Focus on covering all possible branches and edge cases. Try to understand the code first and never assume the method behavior according to the function name. 
    In some cases, there could be comments to document the method to test, such as the following example:
    /*
    Function to test the absolute value of the sum of the parameters
    */
    public int AbsOfSum2Int(int a, int b) {{ 
        return Math.abs(a + b);
    }}
    Try to understand the code first and never assume the method behavior according to the function name. 
    
    You will receive the source code in the following format:
    // source code section
    public class Controller {{ code... }}
    ###
    // dependencies section (it can be empty)
    public class ControllerDependency {{ code... }}

    Moreover, the path of the file is {path}, which allows you to determine the package and import the entire project generically. For example, you can import all classes in the project using import com.example.demo.*;. When adding imports, ensure they are as generic as possible to cover all required classes.    
    # What you are testing
    It's a Spring Boot project made in the java language which is able to interface with other external resources ie. databases so don't test edge cases like setter for the Ids of the entities/models inside the tables.
    
    # Output Requirements
    - Output only the Java code, do not write the ```java and ``` quotes
    - Exclude any comments or explanations if not already written
    - Ensure all dependencies needed for the test are appropriately managed and configured.
    - Print the related package as first line according to the receieved {path} 
    """

    print("Prompt created")

    input_content = content['fileContent'].decode('utf-8') + "\n###\n"
    for item in contentDeps:
        input_content += item['fileContent'].decode('utf-8')
    
    print("Calling GPT")
    try:
        response = client.chat.completions.create(
            model=Model.GPT4o.value,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": input_content
                }
            ],
            temperature=TEMPERATURE,
            top_p=TOP_1
        )

        print("Generated")
        return response.choices[0].message.content

    except Exception as e:
        print(f"Error processing {content['filePath']}: {e}")

