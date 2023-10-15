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

    const chat_table = new dynamodb.Table(this, 'historyTable', {
      tableName: 'chatgpt-client-history',
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      // sortKey: {
      //   name: 'createdAt',
      //   type: dynamodb.AttributeType.STRING,
      // },
    });
    chat_table.addGlobalSecondaryIndex({
      indexName: 'byUserId',
      partitionKey: {
        name: 'userId',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'createdAt',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // const clientFunction = new _lambda.Function(this, 'PythonApiFunction', {
    //   functionName: 'chatgpt-python-client',
    //   runtime: _lambda.Runtime.PYTHON_3_10,
    //   code: _lambda.Code.fromAsset('./functions/hello'),
    //   handler: 'lambda_function.handler',
    //   environment: {
    //     TABLE_NAME: dynamoTable.tableName,
    //   },
    //   role: new iam.Role(this, 'chatgpt-python-clientRole', {
    //     assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    //     managedPolicies: [
    //       iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
    //     ],
    //   }),
    // });

    // const openapiApiKey = ssm.StringParameter.fromSecureStringParameterAttributes(this, 'chatApiKey', {
    //   parameterName: '/openai/chatgpt/api_key',
    //   // version: 1,
    // }).stringValue
    const pythonClient = new alpha.PythonFunction(this, 'apiFunction', {
      functionName: 'chatgpt-api-client',
      entry: './functions/hello',
      index: 'lambda_function.py',
      handler: 'handler',
      runtime: _lambda.Runtime.PYTHON_3_10,
      environment: {
        TABLE_NAME: chat_table.tableName,
        OPENAI_API_KEY: ssm.StringParameter.fromStringParameterAttributes(this, 'chatApiKey', {
          parameterName: '/openai/chatgpt/apiKey',
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


    const restApi = new apigateway.RestApi(this, 'PythonApi', {
      restApiName: 'chatgpt-api',
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
    chatgptClientResource.addMethod('GET',
      new apigateway.LambdaIntegration(pythonClient),
      {
        operationName: 'get-prompts',
      },
    );
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
    

      
      // new sam.CfnFunction(this, 'PythonApiFunction', {
      //   functionName: 'chatgpt-api',
      // runtime: 'python3.10',
      // codeUri: {
      //   bucket: 'chatgpt-api',
      //   key: `functions/app.zip`
      // },
      // handler: 'app.lambda_handler',
      // events: {
      //   api: {
      //     type: 'Api',
      //     properties: {
      //       restApiId: restApi.ref,
      //       method: 'POST',
      //       path: '/',
      //     },
      //   },
      // },
      // environment: {},
      // https://github.com/aws/serverless-application-model/blob/master/docs/policy_templates.rst
      // policies: [
      //   {
      //     dynamoDbCrudPolicy: {
      //       tableName: dynamoTable.tableName,
      //     },
      //   },
      // ],
  
  }
}
