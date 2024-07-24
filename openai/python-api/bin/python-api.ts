#!/usr/bin/env node
import 'source-map-support/register';

import * as path from 'path';

import * as cdk from 'aws-cdk-lib';
import { PythonApiStack } from '../lib/python-api-stack';


const currentDir = process.cwd();
const projectName = path.basename(currentDir);

const app = new cdk.App();
cdk.Tags.of(app).add('Project', 'openai-chatgpt');
cdk.Tags.of(app).add('ManagedBy', `aws-cdk/${projectName}`);

new PythonApiStack(app, 'ChatGptApiStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});
