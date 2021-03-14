"""
app.py: AWS lambda to poll https://www.metaculus.com/questions/4470/ to determine when 
https://www.metaculus.com/questions/3631/ closes.

Dependencies: an SNS topic to publish the closing notification, and the MinimumWageTrigger which periodically
invokes this Lambda. When the closing condition is met, this Lambda will disable the MinimumWageTrigger.
"""

import boto3
import ergo
import json

from datetime import datetime

def handler(event, context):
    metaculus = ergo.Metaculus()

    biden_vaccine_question = metaculus.get_question(id=4470)

    num_iterations = 1000

    intervals = [0, 0, 0]
    for i in range(num_iterations):
        # Some fraction of the question is above the upper bound for the q, but ergo
        # will just guess at the samples there and they will clearly be in the >= $15
        # bucket. So I think this is okay.
        sample = biden_vaccine_question.sample_community()
        if sample <= 10:
            intervals[0] += 1
        elif sample >= 15:
            intervals[2] += 1
        else:
            intervals[1] += 1
        
    probabilities = [float(x)/num_iterations for x in intervals]

    if any(x < 0.1 for x in probabilities):
        message = "One of the minimum wage forecasts has dropped below 0.1. Notify metaculus admins to close the questions. %s: %s" % (datetime.now().isoformat(), probabilities)
        sns = boto3.client('sns')
        sns.publish(TopicArn="arn:aws:sns:us-west-2:393884012696:MinimumWageTopic", Message=message)

        print("Disabling MinimumWageTrigger")
        events = boto3.client('events')
        result = events.disable_rule(Name="MinimumWageTrigger")
        print(result)

    print(probabilities)

    return {
        'statusCode': 200,
        'body': json.dumps(probabilities)
    }