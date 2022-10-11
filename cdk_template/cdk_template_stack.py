from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_logs_destinations as destinations
)
from constructs import Construct

class CdkTemplateStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        log_group = logs.LogGroup(
            self, "LogGroup",
            retention=logs.RetentionDays.ONE_WEEK
        )

        lambda_function = _lambda.Function(
            self, "MyLambda",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="hello.handler",
            code=_lambda.Code.from_asset('./lambda'),
            timeout=Duration.minutes(1)
        )

        logs.SubscriptionFilter(
            self, "Subcription",
            log_group=log_group,
            destination=destinations.LambdaDestination(lambda_function),
            filter_pattern=logs.FilterPattern.all_terms("ERROR", "MainThread")
        )
        
