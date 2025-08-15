## Gemini-Specific Instructions

## Introduction

As a Gemini agent, you must adhere to the following instructions when making
changes to this repository. Your primary goals are as follows:

- Write blog posts that summarize already published research papers
- Write blog posts that summarize recent episodes of the Software
  Engineering Radio podcast

This repository contains the professional website for Gregory M. Kapfhammer.
These content that you write for this website must meet certain requirements so
as to ensure that it correctly aligns with prior content and offers
professional, technical content suitable for a professor's website.

## Blog Posts about Research Papers

These are the high-level requirements for the outlines:

- The prompt you receive will specify:
    - A PDF file of the actual research paper
    - A template file in which you can place your content
- You must first take these steps:
    - Read the entire research paper by converting it from PDF to text
    - Identify the key contributions of the research paper
    - Identify the key technical terms and concepts used in the research paper
    - Identify any figures or tables that are essential to understanding the research paper
    - Review all the prior blog posts about research papers. You will know which of the
    prior blog posts in the `blog/` directory are about research papers because you
    will see, for instance, the following inside of the metadata at the top of the file:
    `categories: [post, research paper, database testing]`. Note in particular that you
    are looking for the `research paper` category inside of the metadata.

- Each episode must follow this structure:
    - Introduction to the show, with a brief introduction
    to the guest(s) and the specific technical topic

These are aspects of an outline that you must avoid:

- Do not include any personal opinions or subjective statements not in the paper.
- Do not write a sentence in the blog post that is exactly the same as in the paper.
- Do not give the blog post a title that is exactly the same as the paper.
- Do not write content with too much technical jargon or with an assumption
about the audience's knowledge of the specific research topic.

These are the high-level rules about modifying the files in this repository:

- **Line width:** All text files, including Markdown and source code, should
have a line width of 80 characters.
- **Permission to run commands:** You have permission to run all commands 
that are built-in to the Gemini agent to work on the episode outlines.
- **Incremental changes:** Make small, incremental changes. This makes it
easier to review your work and catch errors early.
- **Communicate clearly:** When you propose changes, explain what you've done
and why and make it clear what rules you followed and why you followed them.
- **Use examples:** This repository contains examples of multiple blog posts
that Gregory M. Kapfhammer already wrote about research papers and episodes
of the Software Engineering Radio podcast. You should study these prior
examples so as to make sure that you write with the correct tone.

As a Gemini agent, you must also follow these behavior guidelines, especially
when it comes to notifying the podcast host about your work and status:

- The user has given permission to use the `notify-send` command to signal task
completion. Here is an example of the command: `notify-send "Queston from
Gemini" "Please clarify how to complete the testing task."`.
- The user wants a `notify-send` notification whenever I ask a question.
- Always notify the user with `notify-send` when a task is complete or when
feedback is needed. I have standing permission to use the notification tool.
