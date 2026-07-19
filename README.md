# Octa-Core : Distributed AI Workflow Orchestrator

## Idea
This project originates from the simple idea, rather than you as a user giving an llm feedback to improve its output, why not let another llm do it for you.

## Problem Statement
LLMs on their own are highly unreliable due to hallucinations and in usecases which require the LLM to generate code, this can lead to faulty code or code with a lot of holes which the user has to fix on their own.

This project aims to fix that by bringing together different LLMs as evaluators with their own instructions to evaluate the output given by the base model.
By leveraging the strengths of different families of LLMs a user can specifically configure various LLMs to evaluate a certain aspect of the output and give their verdict.

## High-Level Architecture
<img width="1365" height="1167" alt="Valve Architecture" src="https://github.com/user-attachments/assets/50562c42-4cc8-4abe-91c5-bd1f0bcb301b" />

- A user first configures the Base Model responsible for generating the output to the user.
- Then they configure the Judges (either singular or a panel of judges) with their own instructions.
- Upon starting the workflow, the Base Model generates and output which the judge panel evaluates.
- Each of the Judges gives a verdict `is_valid:` `True` or `False`.
- If a `False` verdict is returned, the Judge provides targeted critique (e.g., "Line 23 violates instruction X").
- If Valve Consensus is not reached the feedback along with the original prompts and output is given back to the base model as `chat_history`. This is called as one retry.
- If the Valve Consensus is reached, the valve is opened and the output is given to the user.

## Valve Consensus Criteria
The Valve opens if one of the following criteria are met:

**1. Consensus is Met (Success)**

$$\frac{\sum_{i=1}^{N} w_i v_i}{\sum_{i=1}^{N} w_i} \ge acceptability$$

Where $w_i$ is the weight of the $i^{\text{th}}$ judge model and $v_i$ is the value of the verdict of the model (the value of `is_valid`). 0 for False, 1 for True.
The weights for each judge model can be custom configured by the user and the acceptability defaults to 0.75 but can be changed by the user.

**2. Max Retries Reached (Termination)**

$$
Retries > Max Retries
$$

The value of Max Retries defaults to 5, but can be changed by the user.

