import boto3
import streamlit
from pandasai.llm import BedrockClaude


@streamlit.cache_resource
def get_aws_llm(conf):
    session = boto3.Session(profile_name=conf['aws_user'])
    region = conf['aws_region']
    bedrock_client = session.client('bedrock-runtime', region_name=region)

    llm = BedrockClaude(
        bedrock_runtime_client=bedrock_client,
        model=conf['aws_model'],
        max_tokens=conf['llm_max_tokens'],
        temperature=conf['llm_temperature']
    )
    return llm
