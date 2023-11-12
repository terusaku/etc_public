import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
// import * as sam from 'aws-cdk-lib/aws-sam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as _lambda from 'aws-cdk-lib/aws-lambda';
import * as alpha from '@aws-cdk/aws-lambda-python-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ssm from 'aws-cdk-lib/aws-ssm';


export class PythonApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const chat_table = new dynamodb.Table(this, 'ChatGptHistoryTable', {
      tableName: 'chatgpt-llm-history',
      partitionKey: {
        name: 'sessionId',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      sortKey: {
        name: 'createdAt',
        type: dynamodb.AttributeType.NUMBER,
      },
      timeToLiveAttribute: 'ttl',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    // chat_table.addGlobalSecondaryIndex({
    //   indexName: 'byKeyTime',
    //   partitionKey: {
    //     name: 'sessionId',
    //     type: dynamodb.AttributeType.STRING,
    //   },
    //   sortKey: {
    //     name: 'keyTime',
    //     type: dynamodb.AttributeType.NUMBER,
    //   },
    // });

    const pythonClient = new alpha.PythonFunction(this, 'chatGptApiFunction', {
      functionName: 'chatgpt-api-llm',
      entry: './functions/hello',
      index: 'lambda_function.py',
      handler: 'handler',
      memorySize: 512,
      timeout: cdk.Duration.seconds(20),
      runtime: _lambda.Runtime.PYTHON_3_10,
      environment: {
        TABLE_NAME: chat_table.tableName,
        OPENAI_API_KEY: ssm.StringParameter.fromStringParameterAttributes(this, 'chatApiKey', {
          parameterName: '/openai/chatgpt/apiKey',
        }).stringValue,
        SLACK_SIGNING_SECRET: ssm.StringParameter.fromStringParameterAttributes(this, 'slackSigningSecret', {
          parameterName: '/slack/chatgpt_slackbot/signing_secret',
        }).stringValue,
        SLACK_BOT_TOKEN: ssm.StringParameter.fromStringParameterAttributes(this, 'slackBotToken', {
          parameterName: '/slack/chatgpt_slackbot/oauth_token',
        }).stringValue,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
      role: new iam.Role(this, 'chatgpt-api-clientRole', {
        assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        managedPolicies: [
          iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        ],
      }),
    });

    chat_table.grantReadWriteData(pythonClient);
    // pythonClient.addToRolePolicy(new iam.PolicyStatement({
    //   actions: [
    //     'ssm:GetParameter',
    //     'kms:Decrypt'
    //   ],
    //   resources: [`arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter/openai/chatgpt/*`],
    // }));


    const restApi = new apigateway.RestApi(this, 'chatGptApi', {
      restApiName: 'chatgpt-api-rest',
      deployOptions: {
        stageName: 'dev',
        tracingEnabled: true,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
      },
      defaultMethodOptions: {
        // apiKeyRequired: true,
        authorizationType: apigateway.AuthorizationType.NONE,
        requestValidatorOptions: {
          requestValidatorName: 'chatgpt-api-validator',
          validateRequestBody: true,
          validateRequestParameters: true,
        },
        methodResponses: [
          {
            statusCode: '200',
            responseParameters: {
              'method.response.header.Access-Control-Allow-Origin': true,
            },
          },
        ],
        requestParameters: {
          'method.request.header.Access-Control-Allow-Origin': true,
        },
      },
      endpointConfiguration: {
        types: [apigateway.EndpointType.REGIONAL],
      },
    });

    const chatgptClientResource = new apigateway.Resource(this, 'lambdaApiResource', {
      parent: restApi.root,
      pathPart: 'chatgpt-client',
    });
    // chatgptClientResource.addMethod('GET',
    //   new apigateway.LambdaIntegration(pythonClient),
    //   {
    //     operationName: 'get-prompts',
    //   },
    // );
    chatgptClientResource.addMethod('POST',
      new apigateway.LambdaIntegration(pythonClient),
      {
        operationName: 'control-settings',
      },
    );
    chatgptClientResource.addMethod('OPTIONS',
      new apigateway.MockIntegration({
        integrationResponses: [
          {
            statusCode: '200',
            responseParameters: {
              'method.response.header.Access-Control-Allow-Origin': "'*'",
              'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'",
            },
          },
        ],
        passthroughBehavior: apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
        requestTemplates: {
          'application/json': '{"statusCode": 200}',
        },
      }),
      {
        operationName: 'options-mock',
        methodResponses: [
          {
            statusCode: '200',
            responseParameters: {
              'method.response.header.Access-Control-Allow-Origin': true,
              'method.response.header.Access-Control-Allow-Methods': true,
            },
          },
        ],
      },
    );
  };
}

    // chatgptClientResource.addMethod('POST',
    //   new apigateway.LambdaIntegration(pythonClient),
    // );
    // // restApi.root.addResource('chatgpt-client').addMethod('GET',
    // //   new apigateway.LambdaIntegration(pythonClient),
    // // );
    // restApi.root.addResource('chatgpt-client').addMethod('OPTIONS',
    //   new apigateway.MockIntegration({
    //     integrationResponses: [
    //       {
    //         statusCode: '200',
    //         responseParameters: {
    //           'method.response.header.Access-Control-Allow-Origin': "'*'",
    //           'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'",
    //         },
    //       },
    //     ],
    //     passthroughBehavior: apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
    //     requestTemplates: {
    //       'application/json': '{"statusCode": 200}',
    //     },
    //   }),
    // );
    
