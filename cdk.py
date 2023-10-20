#!/usr/bin/env python3

import os
import aws_cdk as cdk
from constructs import Construct


class IMDBenchStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        imdbench_lambda = cdk.aws_lambda.DockerImageFunction(
            self,
            "imdbench",
            code=cdk.aws_lambda.DockerImageCode.from_image_asset("."),
            timeout=cdk.Duration.minutes(15),
            environment={
                key: value
                for key, value in os.environ.items()
                if key.startswith("IMDBENCH")
            },
            memory_size=1024,
        )

        cdk.aws_apigateway.LambdaRestApi(
            self,
            "imdbench-endpoint",
            handler=imdbench_lambda,
            integration_options=cdk.aws_apigateway.LambdaIntegrationOptions(
                timeout=cdk.Duration.minutes(15),
            ),
        )


app = cdk.App()
IMDBenchStack(app, "IMDBenchStack")
app.synth()
