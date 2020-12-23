# Serverless URL shortener

## Motivation

The idea of building myself a URL shortener had crossed my mind a few times before. However the idea was always dismissed as I usually didn't know where to start.

My main goal was to be able to create short and memorable URLs for personal things like my dotfiles install script (something the likes of [migueli.to/dotfiles](https://migueli.to/dotfiles)). In other words, URLs should be "branded", i.e. have my name on it, and customizable.

In the last few months I made up for the lack of technical knowledge by getting [some training in Amazon Web Services (AWS)](https://www.udemy.com/course/aws-certified-solutions-architect-associate/). I found particularly interesting the section on serverless and AWS Lambda and decided that it was a good fit for my project.

## Architecture

There are a bunch of AWS services supporting this project such as [S3](https://aws.amazon.com/free/), [CloudFront](https://aws.amazon.com/es/cloudfront/), [API Gateway](https://aws.amazon.com/es/api-gateway/) and [Lambda](https://aws.amazon.com/es/lambda/). To glue everything together a [CloudFormation](https://aws.amazon.com/es/cloudformation/) stack is sitting on the driver seat as *infrastructure-as-code* (IaC) solution.

But none of this is necessarily complicated or has to be created by hand thanks to the [Serverless Framework](https://serverless.com/) that allows you to decouple from the specifics of your cloud provider.

The actual code that runs in the cloud to provide the shorten functionality is written in Python 3.

The above is just a very rough overview of how everything actually works so I wrote down [some more detailed notes for my future self](https://github.com/mperezi/aws-lambda-url-shortener/wiki).

## The cake is a lie

Everyone that has been working in the "cloud" for a while should know that the magic behind it is... well... not that magical. At the end of the day it's just servers hidden somewhere. As the joke runs:

> There is no cloud: it's just someone else's computer

*Cloud* and *serverless* are definitely buzzwords these days and should be taken with a grain of salt but every now and then it's exciting to take a look under the hood to see what's going on. 

In the case of serverless and more especifically AWS Lambda the technology that backs it up is called [Firecracker](https://firecracker-microvm.github.io/), a microVM (running on a server - where else?) that can launch in a fraction of a second, making it really scalable.

So THERE ARE SERVERS behind serverless. It's just that you don't *care*. 

## Acknowledgements

This work is heavily inspired by the following article:

* [How to build a Serverless URL shortener using AWS Lambda and S3](https://www.freecodecamp.org/news/how-to-build-a-serverless-url-shortener-using-aws-lambda-and-s3-4fbdf70cbf5c/)
