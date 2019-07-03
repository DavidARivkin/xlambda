# Setting up configuration options for your X-Lambda deployment

The the `xlambda-config.yml` file, in the project root path, contains two main blocks of settings:

- **Global settings**: provide the default AWS region and scaling options
- **Functions list**: for each Lambda you would like to keep warm, provide at least the function name. Region and function-level scaling are optional (will default to global settings if not set)

## Enforce container count boundaries

In scaling options, you must enforce lower and upper boundaries for how many containers X-Lambda should warm up:

- `min_containers`
- `max_containers`
- `max_concurrency`

That's important because our internal forecasts can generate pretty much any number, and that could be dangerous. These parameters will override the X-Lambda forecasts, making sure the warming process won't eat up your AWS concurrency quota.

## `max_concurrency` explained:

Consider:

- You have Lambdas A, B and C
- The forecasted container demands are: A (15), B (15), C (30)

If you set `max_concurrency` to 30, we will first warm up A and B concurrently (totalling 30 requests) and, after finished with them, we will process the last one. This option gives you control to prevent X-Lambda from exhausting the [Lambda concurrency quota](https://docs.aws.amazon.com/lambda/latest/dg/concurrent-executions.html) on your AWS account.