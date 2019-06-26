# X-Lambda
Use statistical power against cold starts in AWS Lambda functions.

![X-Lambda Logo](https://github.com/dashbird/xlambda/raw/master/images/logo.jpg)

## In a nutshell

X-Lambda will monitor your AWS Lambda functions, analyze past behavior and use statistical methods to forecast short-term invocation demand. Running on a scheduled basis, it will keep the right number of containers warm, mitigating cold start latency.

It is themed after X-Men characters. Because, well, why not name a Lambda function after Wolverine, right?

## Acknowledgements

### Proudly offered and supported by

[Dashbird.io](https://dashbird.io): the leading serverless monitoring platform in the market with +250,000 Lambda functions monitored.

[![Dashbird Logo](https://github.com/dashbird/xlambda/raw/master/images/dashbird-logo.jpg)](https://dashbird.io)

### Special kudos to

[StatsModels](https://www.statsmodels.org): easy to use timeseries analysis models

[Serverless](https://serverless.com/framework/): seamless deployment of X-Lambda on AWS

[aiohttp](https://aiohttp.readthedocs.io): making concurrent HTTP requests a piece of cake

## Requirements

[AWS Account](https://aws.amazon.com)

[Python +3.7](https://www.python.org/downloads/)

[NodeJS +8](https://nodejs.org)

[Serverless +1.45](https://serverless.com/framework/)

## Quick Start

### Installation

1. Make sure your system meets the requirements above
2. Download or clone X-Lambda repo
3. Install Python requirements: `pip install -r requirements` ([virtualenv](https://docs.python.org/3/tutorial/venv.html) is highly recommended)

### Setup your configuration options

Create a custom YAML file following this pattern:

_PENDING: Detail YAML template here..._

### Deployment

1. Create an S3 bucket (or use an existing one) and upload your YAML configuration options
2. In the `serverless.yml` template, customize:
  * In which AWS region you would like to run X-Lambda (under `provider.region`)
  * The input S3 Bucket and Object names according to the ones you created in the previous step, (under `functions.professor.events.schedule`)
3. Run the serverless template: `serverless deploy`

# About X-Lambda

## Under the Hood

Four Lambda functions take care of everything:

### Professor

![Professor Xavier](https://github.com/dashbird/xlambda/raw/master/images/professor.PNG)

Of course, we wouldn’t let Professor Xavier out of this mission. This function takes care of controlling the entire warming process, coordinating the other Lambdas.

Professor will get the list of functions to keep warm and fan-out tasks to three of his team members:

*   **Wolverine**: retrieves the necessary Lambda metrics
*   **Jean**: forecasts container demand
*   **Cyclops**: fires up the right number of Lambda containers

Whenever possible and necessary, requests are launched concurrently. For that reason, boto3 was not used in the Lambda invocation requests, because it’s not compatible with non-blocking async calls. Instead, we implemented requests to AWS Lambda endpoints using [aiohttp](https://github.com/aio-libs/aiohttp).

We do not parallelize anything (actually processing things in parallel on multiple cores) because that would require assigning +2 GB of memory to the X-Lambda functions in order to get two cores. This would add too much cost for very little value, since most of the blocking processes in X-Lambda are IO-bound and the Python [asyncio](https://docs.python.org/3/library/asyncio.html) is good at handling concurrency.

### Wolverine

![Wolverine](https://github.com/dashbird/xlambda/raw/master/images/wolverine.PNG)

Logan will gather all the information we need so that the other Lambdas can accomplish their tasks on a timely and precise manner.

The data is retrieved from AWS APIs:

*   **CloudWatch**: a timeseries of concurrent requests;
*   **Lambda**: basic info about the function, such as memory size, whether it’s running inside a VPC, etc;

All these data points will influence the warming dynamics. The startup time of Lambda containers is longer inside a VPC, for example, and this measure is important to avoid containers being reused during the warming process. Allocating more memory, on the other hand, speeds up the startup and execution time.

Wolverine is then charged with supplying every data point needed by our warming process to work flawlessly.

### Jean

![Jean Grey](https://github.com/dashbird/xlambda/raw/master/images/jean.PNG)

Based on the Lambda concurrent invocation metrics, the _Marvel Girl_ forecasts how many containers will be needed in the near-term.

An [Exponential Smoothing](https://en.wikipedia.org/wiki/Exponential_smoothing) model is used to extrapolate the forecasts, optimized by maximizing a log-likelihood function. There are dozens of Time Series forecasting techniques out there. We chose Exponential Smoothing because it’s simple and favours recent observations above older ones, which enables X-Lambda to react more quickly to unexpected spikes in demand.

Currently we use historic concurrent requests provided by CloudWatch, with a 5-minute resolution, extrapolating the next 15 minutes (3 predicted slots of 5 minutes each).

### Cyclops

![Cyclops](https://github.com/dashbird/xlambda/raw/master/images/cyclops.PNG)

Scott Summers is responsible for adjusting its laser power and firing up the right number of containers for a given Lambda function.

Cyclops will invoke the functions providing a specific payload that allows your functions to propertly identify and adjust to X-Lambda requests. This way, the execution can be short-circuited to only serve as a warming request, skipping execution of the entire function’s code. Functions will also be able to sleep for the right period of time before terminating the execution to make sure containers will not be reused during the warming process.

## What to expect and current limitations

The project is still in alpha, meaning you will almost certainly encounter bugs, unexpected behavior and many things may change in future versions. For now, we do not recommend to rely on it if you’re running mission critical applications in production.

Our main purpose with this initial release was to start lean, publish our ideas, gather feedback and improve to launch a more stable and scalable version in the near term.

Due to how CloudWatch metrics are designed, X-Lambda only works with functions that have [reserved concurrency setting](https://docs.aws.amazon.com/lambda/latest/dg/concurrent-executions.html#per-function-concurrency). Our team is working on an API to provide concurrency metrics for any function but we still don’t have an ETA for releasing it.

We suggest keeping the number of functions to warm below 50. X-Lambda uses the CloudWatch API endpoint [GetMetricData](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_GetMetricData.html), which [has its limitations](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_limits.html). In future releases, we are going to implement an architecture that can support virtually any number of Lambda functions while still working within CloudWatch API limits.

The forecasting of Lambda containers demand still don’t have a feedback loop to automatically improve its own accuracy. Ideally, X-Lambda would be able to compare predictions against actual observations and tweak the prediction model to learn from experience and improve over time. This is also in our roadmap.

## Architecture

### Runtime

![Python Logo](https://github.com/dashbird/xlambda/raw/master/images/python-logo.png)

X-Lambda is implemented in Python, version 3.7. It is hands down a very good option for any project relying on statistical packages. Since using statistical and machine learning analysis is at the core of our vision for X-Lambda development, Python was our go-to choice.

### Warming dynamics

![Fire](https://github.com/dashbird/xlambda/raw/master/images/fire.png)

From a naive standpoint, warming up a certain number of containers is piece of cake: just fire up a bunch invocations concurrently and _voilá_! Right? Well, bottom line it is, but there are some caveats along the way.

Basically, we need to make sure that container spinned up during the warming process will only terminate its execution **_after_** the last warming request is fired, otherwise we will be reusing containers, not actually warming them up.

To illustrate our point, consider we have 10 containers warmed up for a given function, but we need to have 30 warmed up in total. Containers already warmed up will take, say 100 milliseconds to spin up and terminate. Since the invocation requests aren’t being fired in parallel, but concurrently, there’s a lag of 10 milliseconds between the start of one request and the next one. By the time the eleventh request goes out, the first container is already done (10 requests * 10 milliseconds = 100 ms) and will get reused by Lambda to serve the incoming warm request, defeating our purpose of spinning up an additional container.

A number of factors affect the startup time of lambda functions:

*   **Runtime**: compiled languages such as Java and C# tend to be much slower than interpreted ones, such as Python and Javascript (NodeJS)
*   **Memory size**: the more memory we allocate, the faster a container will spin up; surprisingly, the relation here looks more exponential than linear (1024 Mb will be more than twice as fast as a 512 Mb function)
*   **VPC**: startup can be greatly affected by VPC connections, some benchmarks reporting 2 to 10 seconds added
*   **Cold state**: as we start the warming process, there’s no way to know how many containers are already warmed, but a warmed container will terminate execution considerably faster than fresh ones

Considering all these factors, it’s not the most trivial task to make sure the warming logic is _really_ spinning up the right amount of containers.

To factor in the runtime and memory size effects, we based our calculations on a [benchmark work](https://read.acloud.guru/does-coding-language-memory-or-package-size-affect-cold-starts-of-aws-lambda-a15e26d12c76) by Yan Cui. In summary, Java and C# are much slower to start from cold state, while Python and NodeJS are quite fast. Also, the more memory is assigned, the faster it starts up.

We used the benchmark results for the 99<sup>th</sup> percentile and applied a [regression analysis](https://en.wikipedia.org/wiki/Regression_analysis) to estimate the sensitiveness of startup time in relation to the memory size. Since the relation between time and memory isn’t linear, natural logarithm was applied to the values before estimating the regression coefficients (thus, exponential should be applied to the results before interpreting as a real-world time value). The regressions R<sup>2</sup> - a measure of how much of variations in the data can be explained by our model - was really good, varying from 90% to 98% across runtimes.

The results are documented in an [Excel spreadsheet](https://github.com/dashbird/xlambda/blob/master/lambda-startup-time-analysis.xlsx), in the project Github repo, in case you’re curious. The final coefficients are used by X-Lambda to adjust how much time we ask your functions to wait before terminating the warming request.

This is a controversial topic. Multiple benchmark attempts have come to different conclusions from Yan Cui, such as the [Alessandro Morandi](https://www.simplybusiness.co.uk/about-us/tech/2019/03/aws-lambda-cold-start/)’s one. We are not aware of an _official_ AWS benchmark. This is something we should revisit in the future, maybe it will make sense to run our own benchmark at some point. Or even consider a totally different strategy for controlling this factor.

One alternative method would be each request report to a central reference point (say a DynamoDB table). Each one would then be able to listen and wait to eachother before terminating. Another option is to chain requests from within the function. We fire one warming request, your own function would call itself and so on. All requests would be synchronous, meaning the first one would only terminate after all others have replied. These would be _safer_ approaches, but also more expensive.

For now, we thought it would be enough to just make function containers sleep silently for an estimated period of time, but we may need to change this approach after battle testing X-Lambda.

### Forecasting

![StatsModels Forecast](https://github.com/dashbird/xlambda/raw/master/images/statsmodels-forecast.png)

There are multiple approaches to timeseries forecasting, each having its pros and cons, and more appropriate to one or another circumstance. We don’t expect X-Lambda users to be data scientists, or even if they are, to have the time for customizing prediction models for each Lambda function. Thus, we needed a generally applicable approach and settled with the [Simple Exponential Smoothing](https://en.wikipedia.org/wiki/Exponential_smoothing) (SES), using the [StatsModels](https://github.com/statsmodels/statsmodels) library implementation.

SES is simple enough to apply to virtually any timeseries. It has only one hyperparameter (_alpha_) which balances how much weight is given to recent and old observations, making it very straightforward to optimize. By default, recent observations are given more importance than older ones in the forecasting calculations. We find this particularly important to enable X-Lambda to quickly adapt its forecasting to peaks and sudden shifts in container demand.

We think that Double or Triple Exponential Smoothing aren’t suitable to our use case. We analyze Lambda metrics for the past few days only (1,000 observations of 5-minute periods). Looking for a trend and seasonality components within this timeframe doesn’t seem reasonable for the general use case.

X-Lambda is open though, so we invite you to play with other options (check [StatsModels documentation on timeseries analysis](https://www.statsmodels.org/stable/tsa.html)) and see whether you can beat the SES forecasting accuracy. You will want to play with the Jean function, more precisely [this script](https://github.com/dashbird/xlambda/blob/master/xlibs/jean/utils.py). Please let us know your results, if you ever attempt this.

### Handling concurrency

![Concurrency](https://github.com/dashbird/xlambda/raw/master/images/concurrency.png)

Although we use the AWS Python SDK - [boto3](https://github.com/boto/boto3) - for some endpoints ([GetMetricData](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_GetMetricData.html) and [GetFunctionConfiguration](https://docs.aws.amazon.com/lambda/latest/dg/API_GetFunctionConfiguration.html)), we decided not to use it for the [Lambda Invoke](https://docs.aws.amazon.com/lambda/latest/dg/API_Invoke.html) endpoint. That’s because boto3 is not compatible with asynchronous, non-blocking requests. We would need to use threads in order to invoke functions concurrently, adding some overhead. Instead, we implemented this HTTP endpoint using the [asyncio](https://docs.python.org/3/library/asyncio.html) and [aiohttp](https://github.com/aio-libs/aiohttp) libraries.

We do not actually parallelize anything in X-Lambda ([difference between concurrency and parallelism](https://stackoverflow.com/questions/1050222/what-is-the-difference-between-concurrency-and-parallelism)). Most blocking executions within the project that could be parallelized are IO-bound and Python asyncio takes care of that in a performant way already. In order to run things in parallel, you would need to assign +2 GB to the X-Lambda functions. It’s the only way to get two CPU cores in AWS Lambda. Balancing benefits and costs, we decided it was not going to be effective.

### Lambda metrics

We currently retrieve the _ConcurrentRequests_ measure from the CloudWatch API endpoint [GetMetricsData](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_GetMetricData.html). The downside: it’s only available to functions with [reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/concurrent-executions.html#per-function-concurrency) setting. We tried to use invocations per second as a proxy, which would allow X-Lambda to work with any function, but in our tests it didn’t prove to be precise enough.

Lambda executions are most often short-lived (few dozen or hundred milliseconds). It means the same container can be reused for multiple sequential requests during a full second. The invocation count would be an inflated proxy for container count and using it in our warming process would lead to a waste of resources. Or, if invocations take too much longer than a second, we could miserably fail by under estimating the number of containers needed. In short: not gonna work.

Our awesome [dev team at Dashbird](https://dashbird.io/team/) is working on a custom API endpoint to provide the same metrics for any Lambda function, regardless of having a reserved concurrency setting in place. We’ll be using the start and end time of each Lambda invocation present in CloudWatch log streams as a proxy to count the number of containers alive at any point in time.

There are [some caveats](https://codeburst.io/why-shouldnt-you-trust-system-clocks-72a82a41df93) when it comes to relying on system clock times in a distributed infrastructure such as the Lambda platform, though. I trust AWS has the best practices in place when it comes to calculating the execution time of a particualr invocation, but the start and end times from different invocations might not be in perfect sync if they’re running on different machines. That’s something we need to take into account and investigate better before releasing this API.

### Scalability

As it is currently architected, X-Lambda has limitations to scale the warming process, mainly due to the AWS CloudWatch and Lambda APIs on which we rely have their limits. The GetMetricData, for example, accepts up to 50 RPS and returns up to 90,000 data points per minute. When retrieving the timeseries metrics to support forecasting, if you have too many functions to be warmed up at the same time, these APIs can throttle our requests and disrupt the overall process. That’s why we suggest it’s safer to schedule X-Lambda to warm a maximum of 50 Lambda functions at a time.

Our Lambdas (Professor, Wolverine, Jean and Cyclops) work coupled to each other and we don’t have enough logic to rate limit all of AWS API requests. Nevertheless, rate limiting is implemented, to some extent, it in this alpha release. For example: you can set a global maximum concurrency limit for invoking your Lambda functions. The Cyclops function will adjust to it when firing the warming requests. However, if a function happens to need more containers than the concurrency limit imposed, X-Lambda won’t be able to limit the entire set of containers, restricting itself to warming up to the concurrency limit set.

In future versions, we will extend to a more robust architecture, decoupling the Lambdas and relying on queuing to make X-Lambda really scalable.

## Project roadmap

We have several ideas to improve and extend X-Lambda. Some of them were already mentioned above:

*   Decoupling X-Lambda functions
*   Enable scaling to warm a high number of functions
*   Update Yan Cui’s benchmark
*   Release an API to provide concurrency metrics for any function
*   Establish a feedback-loop to improve forecasting over time

There’s also plan to release helper libraries in Python (pypi), NodeJS (npm), and other languages to support handling the warm requests payload format and waiting times.

We welcome ideas to improve X-Lambda and contributions to implement new features or fix bugs in the current codebase. Please use the Github issues area to communicate with us.
