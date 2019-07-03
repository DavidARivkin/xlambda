# Adapting your functions to handle warming requests

Your Lambda function handlers need to respond properly to warming requests.

## Payload

When X-Lambda sends a warming request, it will provide a payload similar to this:

```
{
    "xlambda": {
        "action": "warm_up",
        "settings": {
            "startup_time": 1234
        }
    }
}
```

## Handling the warming payload

We recommend you to short-circuit your function upon receiving these warming requests and skip the execution of your real code, returning an early response.

It is also paramount that, if the invocation is being served by a previously warmed container, it waits a certain period of time before returning or terminating the execution. This makes sure these containers are not being reused during the warming process. The `startup_time` parameter will provide how much time (in milliseconds) is safe for your function to sleep. When in doubt whether the invocation is in a pre-warmed container, sleep as default for all warming requests.

More on this in the [Warming dynamics](https://github.com/dashbird/xlambda/blob/master/README.md#warming-dynamics) README section.

## Example

Below is an example of how you could short-circuit the execution of your Lambda function in the event of a warming payload, as well as sleep for the necessary time:

```python
import time


def your_function_handler(event, context):
    if 'xlambda' in event and event['xlambda']['action'] == 'warm_up':
        time.sleep(event['xlambda']['settings']['startup_time'] / 1000)
        return {'status': 200, 'warmed': True}

    # Execute your code here...
```
