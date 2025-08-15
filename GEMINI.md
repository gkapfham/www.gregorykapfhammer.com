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
- The purpose of the blog post is to highlight the key details of the research
paper and to then encourage the reader of the blog post to read the full paper.
- Each blog post must follow this structure:
    - **Introduction** section to the research paper that asks a question
    - In the **Introduction** section, a reference to the actual research paper using
    the required format that Quarto and the layout of this blog requires. Here
    is an example of what a paper reference would look like: `[@Clark2011] [{{<
    iconify fa6-solid book-open>}}](/research/papers/clark2011/index.qmd)`. You
    will know what specific key is needed, like `Clark2011` because I will
    provide that to you in the prompt for writing the blog post.
    - **Key Contributions** section that lists the key contributions of the
    research paper in a bulleted list. Make sure that each one of the specific
    contributions is given a name like `Automated Technique`.
    - **Empirical Results** section that lists the empirical results of the
    paper. Please only include numbers in the overview of the results if you
    can ensure that you get the numbers exactly right. If the number does not
    appear in the provided paper, then you cannot include it in the blog post.
    - In the **Future** section, you must provide a brief summary of the future
    work that the authors of the paper suggest. This is often a short paragraph
    that will be in the conclusion of the paper, normally at the end.
    - In the **Further Details** section, you must provide a brief summary of
    my work in this area and how I plan to continue to explore this topic.
    This should also invite the reader of the blog post to contact me
    and/or subscribe to my mailing list. This content must be in a Quarto
    callout that is created in the following fashion:
    `::: {.callout-note appearance="simple"}`.

## Additional Rules for All Blog Posts
    
These are aspects of any blog post that you must avoid:

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
