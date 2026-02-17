---
title: "Serverless Generative AI: Amazon Bedrock Running in Lambda"
date: 2023-11-24
categories: [AI, Tutorials]
tags: [amazon-bedrock, serverless, video]
description: "In this video Mike takes a look at getting Amazon Bedrock working in a Lambda function. This is a point in time video as things will change, but for now, you ne"
---

{% include embed/youtube.html id='7PK4zdUgAt0' %}

have you tried getting Amazon Bedrock working with a Lambda function well in this video that's exactly what we're going to take a look at let's jump into the AWS console and take a look here I have Amazon Bedrock just a quick recap here um I've got my models enabled currently in this in this account so if I scroll down go to model access you'll see that in this particular region I've got access to a whole ton of different models if you're wondering how all of this works and why all of this works and how to use the console a little bit more uh in detail then there's a link up in the corner somewhere up there which will go to a video where I walk through all of that now let's jump into the uh Lambda console itself so here I've got a Lambda function which I've already created so it's a python 3.11 function um it's called My Bedrock function because no imagination okay let's scroll down um and you can see the code here so I'm importing boto three I'm using the Bedrock runtime um object from the Bedrock client rather um and then following the bouncing ball here so this is the almost boilerplate code I've got this very simple prompt uh write a fictional article about sorry write an artic

## Links & Resources

- [🌐 Get started with Amazon Bedrock](https://aws.amazon.com/bedrock/)

