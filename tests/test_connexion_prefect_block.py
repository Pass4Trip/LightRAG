from prefect.blocks.core import Block
from pydantic import SecretStr
from typing import Optional
import asyncio
import os

# Set Prefect Cloud environment variables
# export PREFECT_ACCOUNT_ID=42cb0262-af09-4eb2-9d92-97142d7fcedd
# export PREFECT_WORKSPACE_ID=a0d5688e-41c6-4d18-bc27-294f7fd7a9e7
PREFECT_ACCOUNT_ID = os.getenv("PREFECT_ACCOUNT_ID")
PREFECT_WORKSPACE_ID = os.getenv("PREFECT_WORKSPACE_ID")

if not PREFECT_ACCOUNT_ID or not PREFECT_WORKSPACE_ID:
    raise ValueError("Please set PREFECT_ACCOUNT_ID and PREFECT_WORKSPACE_ID environment variables")

os.environ["PREFECT_API_URL"] = f"https://api.prefect.cloud/api/accounts/{PREFECT_ACCOUNT_ID}/workspaces/{PREFECT_WORKSPACE_ID}"

class RabbitMQCredentials(Block):
    """Stores RabbitMQ credentials"""
    username: str
    password: SecretStr
    host: str
    port: str

class Neo4jCredentials(Block):
    """Stores Neo4j credentials"""
    uri: str
    username: str
    password: SecretStr

class OVHCredentials(Block):
    """Stores OVH credentials"""
    llm_api_token: SecretStr

# First, register blocks and create credentials
async def register_blocks():
    # Register all block types
    await RabbitMQCredentials.register_type_and_schema()
    await Neo4jCredentials.register_type_and_schema()
    await OVHCredentials.register_type_and_schema()
    
    # Create and save RabbitMQ credentials
    rabbitmq_creds = RabbitMQCredentials(
        username="rabbitmq",
        password="mypassword",  # Remplacez par votre vrai mot de passe
        host="51.77.200.196",
        port="30645"
    )
    await rabbitmq_creds.save("rabbitmq-credentials", overwrite=True)

    # Create and save Neo4j credentials
    neo4j_creds = Neo4jCredentials(
        uri="bolt://51.77.200.196:30687",
        username="neo4j",
        password="mypassword"  # Remplacez par votre vrai mot de passe
    )
    await neo4j_creds.save("neo4j-credentials", overwrite=True)

    # Create and save OVH credentials
    ovh_creds = OVHCredentials(
        llm_api_token="your-token-here"  # Remplacez par votre vrai token
    )
    await ovh_creds.save("ovh-credentials", overwrite=True)

# Run the registration
asyncio.run(register_blocks())

# Load and display all credentials
print("\n=== RabbitMQ Configuration ===")
rabbitmq_block = RabbitMQCredentials.load("rabbitmq-credentials")
print(f"Username: {rabbitmq_block.username}")
print(f"Host: {rabbitmq_block.host}")
print(f"Port: {rabbitmq_block.port}")

print("\n=== Neo4j Configuration ===")
neo4j_block = Neo4jCredentials.load("neo4j-credentials")
print(f"URI: {neo4j_block.uri}")
print(f"Username: {neo4j_block.username}")

print("\n=== OVH Configuration ===")
ovh_block = OVHCredentials.load("ovh-credentials")
print("Token is stored securely and hidden")

# Note: passwords and tokens are hidden by SecretStr