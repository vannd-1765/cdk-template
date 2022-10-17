from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_s3 as _s3,
    aws_logs as logs,
    aws_iam as iam,
    aws_kinesisfirehose as _firehose
)

from constructs import Construct

class CdkTemplateStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        def create_s3_logs():
            s3_log = _s3.Bucket(
                self, 'Bucket-Log',
                bucket_name='cdk-kinesis-s3-logs',
                # removal_policy=removal_policy,
                # object_ownership=s3.ObjectOwnership.BUCKET_OWNER_PREFERRED
            )

            return s3_log
        
        def create_role_for_stream(bucket_name):
            role = iam.Role(
                self, 'Kinesis-Role',
                role_name='FirehosetoS3RoleVanND',
                assumed_by=iam.ServicePrincipal('firehose.amazonaws.com')
            )

            role.add_to_policy(iam.PolicyStatement(
                resources=[f'arn:aws:s3:::{bucket_name}', f'arn:aws:s3:::{bucket_name}/*'],
                actions=[
                    's3:AbortMultipartUpload',
                    's3:GetBucketLocation',
                    's3:GetObject',
                    's3:ListBucket',
                    's3:ListBucketMultipartUploads',
                    's3:PutObject',
                    'logs:PutLogEvents'
                ]
            ))

            return role

        def create_delivery_stream(ingest_bucket, firehose_role):
            kinesisfirehose = _firehose.CfnDeliveryStream(
                self, "CfnDeliveryStream",
                delivery_stream_name='my-delivery-stream',
                s3_destination_configuration=_firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=ingest_bucket.bucket_arn,
                buffering_hints=_firehose.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=60
                ),
                compression_format="UNCOMPRESSED",
                role_arn=firehose_role.role_arn
            ))

            return kinesisfirehose

        def create_cw_role():
            role = iam.Role(
                self, 'CW-Role',
                role_name='CWLtoKinesisFirehoseRoleVanND',
                assumed_by=iam.ServicePrincipal('logs.ap-southeast-1.amazonaws.com')
            )

            stmt = iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                resources=['arn:aws:firehose:ap-southeast-1:448849899098:*'],
                actions=['firehose:*']
            )

            stmt.add_condition("StringLike", 
                {"aws:SourceArn": ["arn:aws:logs:ap-southeast-1:448849899098:*"]}
            )

            role.add_to_policy(stmt)

            return role
        
        def create_handler(name_parts, firehose_delivery_stream, cw_role):
            lambda_function = _lambda.Function(
                self, f"{'_'.join(name_parts)}Lambda",
                function_name=f"{'.'.join(name_parts)}_MyLambda",
                runtime=_lambda.Runtime.PYTHON_3_7,
                handler=f"{('.').join(name_parts)}.handler",
                code=_lambda.Code.from_asset('./lambda'),
                timeout=Duration.minutes(1),
                log_retention=logs.RetentionDays.THREE_DAYS
            )

            # step 5: create subscription filter1
            logs.CfnSubscriptionFilter(
                self, f"{'_'.join(name_parts)}-SubscriptionFilter",
                destination_arn=f'arn:aws:firehose:ap-southeast-1:448849899098:deliverystream/{firehose_delivery_stream.delivery_stream_name}',
                # destination_arn='consumer3-firehose',
                filter_pattern='',
                log_group_name=lambda_function.log_group.log_group_name,

                role_arn=f'arn:aws:iam::123456789012:role/{cw_role.role_name}'
            )

            return lambda_function

        bucket = create_s3_logs()
        
        # step 2: create stream role
        firehose_role = create_role_for_stream(bucket.bucket_name)

        # step 4: create delivery stream
        firehose_delivery_stream = create_delivery_stream(bucket, firehose_role)

        # step 3: create cw role
        cw_role = create_cw_role()

        lambda_1 = create_handler(['hello'], firehose_delivery_stream, cw_role)
        lambda_2 = create_handler(['good_bye'], firehose_delivery_stream, cw_role)
