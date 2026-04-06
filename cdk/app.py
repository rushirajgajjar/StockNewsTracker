#!/usr/bin/env python3
"""CDK app entry point for StockNewsTracker infrastructure."""

import aws_cdk as cdk

from stack import StockNewsTrackerStack

app = cdk.App()
StockNewsTrackerStack(app, "StockNewsTrackerStack")
app.synth()
