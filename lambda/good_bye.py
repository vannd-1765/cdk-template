import json

def handler(event, context):
  return {
    'statusCode': 200,
    'body': json.dumps('Good bye!, deployed using AWS CDK!')
  }